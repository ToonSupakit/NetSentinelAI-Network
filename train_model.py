"""
Train the anomaly model from historical interface data.

The training set uses per-device/per-interface baselines and runtime-like
features so ports with naturally different traffic patterns do not get forced
into one global baseline.
"""

import os
import sys
import warnings
from datetime import datetime

import joblib
import pandas as pd
import yaml
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine

from app.ai_features import EXTENDED_FEATURES, prepare_training_frame
from app.model_registry import write_metadata

warnings.filterwarnings("ignore")

load_dotenv()


def _metric_rate(numerator, denominator):
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _evaluate(model, normal_val, anomaly_val, features):
    frames = []
    if len(normal_val):
        frames.append((normal_val[features], [0] * len(normal_val)))
    if len(anomaly_val):
        frames.append((anomaly_val[features], [1] * len(anomaly_val)))
    if not frames:
        return {
            "precision": None,
            "recall": None,
            "false_positive_rate": None,
            "validation_rows": 0,
            "normal_validation_rows": 0,
            "anomaly_validation_rows": 0,
        }

    X_eval = pd.concat([f[0] for f in frames], ignore_index=True)
    y_true = [label for _, labels in frames for label in labels]
    y_pred = [1 if p == -1 else 0 for p in model.predict(X_eval)]

    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 1)
    fp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 1)
    tn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 0)
    fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 0)

    return {
        "precision": _metric_rate(tp, tp + fp),
        "recall": _metric_rate(tp, tp + fn),
        "false_positive_rate": _metric_rate(fp, fp + tn),
        "outlier_rate": round(sum(y_pred) / len(y_pred), 4) if y_pred else None,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "validation_rows": len(y_true),
        "normal_validation_rows": len(normal_val),
        "anomaly_validation_rows": len(anomaly_val),
    }


def main():
    print("Loading config and database...")
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    model_cfg = config.get("model", {})
    db_url = os.getenv("DB_URL", config.get("database", {}).get("url", ""))
    engine = create_engine(db_url)

    test_size = float(model_cfg.get("train_validation_fraction", 0.2))
    test_size = min(max(test_size, 0.05), 0.5)
    random_state = int(model_cfg.get("random_state", 42))
    contamination = float(model_cfg.get("contamination", 0.05))
    contamination = min(max(contamination, 0.001), 0.5)
    features = list(model_cfg.get("features") or EXTENDED_FEATURES)
    features = [name for name in features if name in EXTENDED_FEATURES] or EXTENDED_FEATURES

    print("Querying interface history from database...")
    df = pd.read_sql(
        """
        SELECT device_name, interface_name, reliability, network_load, rxload,
               input_errors, status, protocol, label, collected_at
        FROM interface_logs
        WHERE interface_name != 'ALL'
          AND collected_at IS NOT NULL
        """,
        engine,
    )

    if len(df) == 0:
        print("Error: No interface history found for training.", file=sys.stderr)
        return 1

    before = len(df)
    df = df[
        (df["reliability"] > 0)
        & (df["reliability"] <= 255)
        & (df["network_load"] >= 0)
        & (df["network_load"] <= 255)
        & (df["rxload"] >= 0)
        & (df["rxload"] <= 255)
    ].copy()
    after = len(df)
    if before != after:
        print(f"Filtered out {before - after} invalid SNMP rows")

    df = prepare_training_frame(df)
    normal_df = df[(df["status"] == "up") & (df["protocol"] == "up") & (df["label"] == "normal")].copy()
    anomaly_df = df[df["label"] == "anomaly"].copy()

    if len(normal_df) < 10:
        print(f"Error: Only {len(normal_df)} clean normal rows. Need at least 10.", file=sys.stderr)
        return 1

    train_df, normal_val = train_test_split(
        normal_df,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )
    X_train = train_df[features]

    print("\nData Summary")
    print(f"  Clean normal rows : {len(normal_df)}")
    print(f"  Anomaly rows      : {len(anomaly_df)}")
    print(f"  Training rows     : {len(X_train)}")
    print(f"  Validation rows   : {len(normal_val) + len(anomaly_df)}")
    print(f"  Features          : {features}")
    print(f"  Contamination     : {contamination}")
    print("\nFeature stats:")
    print(X_train.describe().round(2).to_string())

    print("\nTraining Isolation Forest...")
    model = IsolationForest(
        n_estimators=int(model_cfg.get("n_estimators", 200)),
        contamination=contamination,
        random_state=random_state,
        max_features=1.0,
        bootstrap=True,
    )
    model.fit(X_train)

    metrics = _evaluate(model, normal_val, anomaly_df, features)
    print("\nEvaluation")
    for key in ("precision", "recall", "false_positive_rate", "outlier_rate"):
        print(f"  {key:20s}: {metrics.get(key)}")
    print(
        "  confusion matrix    : "
        f"TP={metrics.get('true_positive', 0)} "
        f"FP={metrics.get('false_positive', 0)} "
        f"TN={metrics.get('true_negative', 0)} "
        f"FN={metrics.get('false_negative', 0)}"
    )

    out_path = model_cfg["path"]
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    joblib.dump(model, out_path)

    version = datetime.now().strftime("%Y%m%d-%H%M%S")
    metadata_path = write_metadata(
        out_path,
        {
            "trained": True,
            "status": "ready",
            "model_version": version,
            "trained_at": datetime.now().isoformat(timespec="seconds"),
            "features": features,
            "training_rows": len(X_train),
            "normal_rows": len(normal_df),
            "anomaly_rows": len(anomaly_df),
            "contamination": contamination,
            "random_state": random_state,
            "evaluation": metrics,
        },
    )

    print("\nTraining complete.")
    print(f"Model saved to {out_path}")
    print(f"Metadata saved to {metadata_path}")
    print(f"Model version: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
