"""Feature engineering shared by training and runtime prediction."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

BASE_FEATURES = ["reliability", "network_load", "rxload", "input_errors"]
EXTENDED_FEATURES = [
    "reliability",
    "network_load",
    "rxload",
    "input_errors",
    "tx_delta",
    "rx_delta",
    "error_rate",
    "uptime_pct",
    "tx_baseline_delta",
    "rx_baseline_delta",
]


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except (TypeError, ValueError):
        return default


def feature_values(row: dict) -> dict:
    return {
        "reliability": _num(row.get("reliability"), 255),
        "network_load": _num(row.get("network_load"), 1),
        "rxload": _num(row.get("rxload"), 1),
        "input_errors": _num(row.get("input_errors"), 0),
        "tx_delta": _num(row.get("tx_delta"), 0),
        "rx_delta": _num(row.get("rx_delta"), 0),
        "error_rate": _num(row.get("error_rate"), row.get("input_errors", 0)),
        "uptime_pct": _num(row.get("uptime_pct"), 100),
        "tx_baseline_delta": _num(row.get("tx_baseline_delta"), 0),
        "rx_baseline_delta": _num(row.get("rx_baseline_delta"), 0),
    }


def model_feature_names(model) -> list[str]:
    names = getattr(model, "feature_names_in_", None)
    if names is None:
        return BASE_FEATURES
    try:
        names = list(names)
    except TypeError:
        return BASE_FEATURES
    valid = set(EXTENDED_FEATURES)
    names = [name for name in names if isinstance(name, str) and name in valid]
    return names or BASE_FEATURES


def frame_for_prediction(row: dict, model=None) -> pd.DataFrame:
    values = feature_values(row)
    names = model_feature_names(model)
    return pd.DataFrame([{name: values[name] for name in names}])


def prepare_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    out["collected_at"] = pd.to_datetime(out["collected_at"], errors="coerce")
    out = out.sort_values(["device_name", "interface_name", "collected_at"])
    group = out.groupby(["device_name", "interface_name"], dropna=False)

    out["tx_delta"] = group["network_load"].diff().fillna(0)
    out["rx_delta"] = group["rxload"].diff().fillna(0)
    out["error_rate"] = group["input_errors"].diff().fillna(out["input_errors"]).clip(lower=0)
    out["uptime_pct"] = group["label"].transform(lambda s: (s == "normal").rolling(20, min_periods=1).mean() * 100)

    normal_tx = out["network_load"].where(out["label"] == "normal")
    normal_rx = out["rxload"].where(out["label"] == "normal")
    out["tx_baseline"] = normal_tx.groupby([out["device_name"], out["interface_name"]]).transform(
        lambda s: s.shift().rolling(20, min_periods=1).mean()
    )
    out["rx_baseline"] = normal_rx.groupby([out["device_name"], out["interface_name"]]).transform(
        lambda s: s.shift().rolling(20, min_periods=1).mean()
    )
    out["tx_baseline_delta"] = (out["network_load"] - out["tx_baseline"].fillna(out["network_load"])).fillna(0)
    out["rx_baseline_delta"] = (out["rxload"] - out["rx_baseline"].fillna(out["rxload"])).fillna(0)

    for name in EXTENDED_FEATURES:
        out[name] = pd.to_numeric(out[name], errors="coerce").fillna(0)
    return out
