# à¸™à¸³à¹€à¸‚à¹‰à¸²à¹„à¸¥à¸šà¸£à¸²à¸£à¸µà¸—à¸µà¹ˆà¸ˆà¸³à¹€à¸›à¹‡à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¸à¸²à¸£à¸—à¸³à¸™à¸²à¸¢à¸”à¹‰à¸§à¸¢ AI
import joblib  # à¸ªà¸³à¸«à¸£à¸±à¸šà¹‚à¸«à¸¥à¸”à¹à¸¥à¸°à¸šà¸±à¸™à¸—à¸¶à¸ AI model
import yaml  # à¸ªà¸³à¸«à¸£à¸±à¸šà¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²
import logging
from app import prediction_intel
from app.ai_features import frame_for_prediction
from app.db import (
    get_interface_runtime_features,
    save_prediction,
)  # à¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¸šà¸±à¸™à¸—à¸¶à¸à¸œà¸¥à¸à¸²à¸£à¸—à¸³à¸™à¸²à¸¢

log = logging.getLogger(__name__)

# à¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²à¸ˆà¸²à¸ config.yaml
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# à¸•à¸±à¸§à¹à¸›à¸£à¹‚à¸à¸¥à¸šà¸­à¸¥à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸à¹‡à¸šà¹‚à¸¡à¹€à¸”à¸¥
model = None


def reload_model():
    """à¹‚à¸«à¸¥à¸” à¸«à¸£à¸·à¸­ à¹‚à¸«à¸¥à¸” AI model à¹ƒà¸«à¸¡à¹ˆà¸ˆà¸²à¸à¹„à¸Ÿà¸¥à¹Œ"""
    global model
    try:
        model = joblib.load(config["model"]["path"])
        log.info(f"ðŸ”„ à¹‚à¸«à¸¥à¸” AI model à¸ªà¸³à¹€à¸£à¹‡à¸ˆà¸ˆà¸²à¸ {config['model']['path']}")
    except FileNotFoundError:
        model = None
        log.warning(
            f"âš ï¸ à¹„à¸¡à¹ˆà¸žà¸š model file: {config['model']['path']} â€” à¹ƒà¸«à¹‰à¸£à¸±à¸™ train_model.py à¸à¹ˆà¸­à¸™"
        )
    except Exception as e:
        model = None
        log.error(f"âŒ à¹‚à¸«à¸¥à¸” model à¸¥à¹‰à¸¡à¹€à¸«à¸¥à¸§: {e}")


# à¹‚à¸«à¸¥à¸”à¸„à¸£à¸±à¹‰à¸‡à¹à¸£à¸à¸•à¸­à¸™à¹€à¸£à¸´à¹ˆà¸¡à¹‚à¸›à¸£à¹à¸à¸£à¸¡
reload_model()


def analyze_cause(data):
    return prediction_intel.analyze_cause(data, config)


def predict_one(data):
    """à¸—à¸³à¸™à¸²à¸¢à¸„à¸§à¸²à¸¡à¸œà¸´à¸”à¸›à¸à¸•à¸´à¸ªà¸³à¸«à¸£à¸±à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥ interface à¸Šà¸¸à¸”à¹€à¸”à¸µà¸¢à¸§

    AI à¸—à¸³à¸‡à¸²à¸™à¸„à¸¹à¹ˆà¸‚à¸™à¸²à¸™à¸à¸±à¸š Rules à¹€à¸ªà¸¡à¸­ (à¹„à¸¡à¹ˆà¹ƒà¸Šà¹ˆà¹à¸„à¹ˆà¸”à¹ˆà¸²à¸™à¸ªà¸­à¸‡):
    1) device_unreachable â€” à¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¹„à¸¡à¹ˆà¹„à¸”à¹‰
    2) rules+ai â€” à¸—à¸±à¹‰à¸‡ Rules à¹à¸¥à¸° AI à¹€à¸«à¹‡à¸™à¸•à¸£à¸‡à¸à¸±à¸™à¸§à¹ˆà¸²à¸œà¸´à¸”à¸›à¸à¸•à¸´
    3) rules â€” à¹€à¸‰à¸žà¸²à¸° Rules à¸šà¸­à¸à¸§à¹ˆà¸²à¸œà¸´à¸”à¸›à¸à¸•à¸´ (AI à¹„à¸¡à¹ˆà¸žà¸š à¸«à¸£à¸·à¸­à¹„à¸¡à¹ˆà¸¡à¸µ model)
    4) ai â€” à¹€à¸‰à¸žà¸²à¸° AI à¸•à¸£à¸§à¸ˆà¸žà¸š pattern à¸œà¸´à¸”à¸›à¸à¸•à¸´ (Rules à¸¡à¸­à¸‡à¸§à¹ˆà¸²à¸›à¸à¸•à¸´)
    5) healthy â€” à¸œà¹ˆà¸²à¸™à¸—à¸±à¹‰à¸‡ Rules à¹à¸¥à¸° AI
    """
    if data.get("is_device_down"):
        return "anomaly", 1.0, "device_unreachable"

    rules_says_anomaly = data["label"] == "anomaly"

    # â”€â”€ AI Analysis (à¸—à¸³à¸‡à¸²à¸™à¹€à¸ªà¸¡à¸­à¸–à¹‰à¸²à¸¡à¸µ model) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ai_says_anomaly = False
    ai_confidence = 0.0

    if model is not None:
        features = frame_for_prediction(data, model)

        pred_int = model.predict(features)[0]
        # decision_function: à¸„à¹ˆà¸²à¸¢à¸´à¹ˆà¸‡à¸•à¸´à¸”à¸¥à¸š = à¸¢à¸´à¹ˆà¸‡ outlier
        score = model.decision_function(features)[0]
        ai_confidence = min(1.0, max(0.0, 0.5 - score))  # à¹à¸›à¸¥à¸‡à¹€à¸›à¹‡à¸™ 0-1

        if pred_int == -1:
            ai_says_anomaly = True

    # â”€â”€ à¸•à¸±à¸”à¸ªà¸´à¸™à¸œà¸¥à¸£à¸§à¸¡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if rules_says_anomaly and ai_says_anomaly:
        # à¸—à¸±à¹‰à¸‡à¸ªà¸­à¸‡à¹€à¸«à¹‡à¸™à¸•à¸£à¸‡à¸à¸±à¸™ â†’ à¸„à¸§à¸²à¸¡à¸¡à¸±à¹ˆà¸™à¹ƒà¸ˆà¸ªà¸¹à¸‡à¸ªà¸¸à¸”
        return "anomaly", max(0.95, ai_confidence), "rules+ai"

    if rules_says_anomaly:
        # à¹€à¸‰à¸žà¸²à¸° Rules à¹€à¸«à¹‡à¸™ (AI à¸­à¸²à¸ˆà¹„à¸¡à¹ˆà¸¡à¸µ model à¸«à¸£à¸·à¸­ AI à¹„à¸¡à¹ˆà¹€à¸«à¹‡à¸™à¸”à¹‰à¸§à¸¢)
        return "anomaly", 1.0, "rules"

    if ai_says_anomaly:
        # à¹€à¸‰à¸žà¸²à¸° AI à¹€à¸«à¹‡à¸™ â€” pattern à¸œà¸´à¸”à¸›à¸à¸•à¸´à¸—à¸µà¹ˆ Rules à¹„à¸¡à¹ˆà¸„à¸£à¸­à¸šà¸„à¸¥à¸¸à¸¡
        return "anomaly", round(ai_confidence, 4), "ai"

    # à¸œà¹ˆà¸²à¸™à¸—à¸±à¹‰à¸‡à¸„à¸¹à¹ˆ
    return "normal", 1.0, "healthy"


def enrich_runtime_features(data):
    enriched = dict(data)
    if data.get("is_device_down") or data.get("intf") == "ALL":
        return enriched
    try:
        features = get_interface_runtime_features(
            data.get("device"),
            data.get("intf"),
            current_log_id=data.get("log_id"),
            window=config.get("model", {}).get("feature_window", 20),
        )
        enriched.update(features)
    except Exception as e:
        log.debug("Runtime feature enrichment failed for %s/%s: %s", data.get("device"), data.get("intf"), e)
    return enriched


def classify_severity(data, confidence, detection_source):
    return prediction_intel.classify_severity(data, confidence, detection_source, config)


def _is_down_event(anomaly):
    return prediction_intel.is_down_event(anomaly)


def _is_root_event(anomaly):
    return prediction_intel.is_root_event(anomaly)


def _same_area(root, child):
    return prediction_intel.same_area(root, child)


def apply_correlation(anomalies):
    return prediction_intel.apply_correlation(anomalies)


def predict_all(collected_data):
    """à¸—à¸³à¸™à¸²à¸¢à¸„à¸§à¸²à¸¡à¸œà¸´à¸”à¸›à¸à¸•à¸´à¸ªà¸³à¸«à¸£à¸±à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥ interface à¸—à¸±à¹‰à¸‡à¸«à¸¡à¸”"""
    records = []
    anomalies = []

    for raw in collected_data:
        data = enrich_runtime_features(raw)
        prediction, confidence, detection_source = predict_one(data)
        record = {
            "data": data,
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "detection_source": detection_source,
            "severity": None,
            "correlated_with": None,
            "notification_suppressed": False,
        }
        records.append(record)

        if prediction == "anomaly":
            causes, suggestions = analyze_cause(data)
            severity = classify_severity(data, confidence, detection_source)
            anomaly = {
                **data,
                "prediction": prediction,
                "confidence": confidence,
                "detection_source": detection_source,
                "severity": severity,
                "correlated_with": None,
                "notification_suppressed": False,
                "causes": causes,
                "suggestions": suggestions,
            }
            record["severity"] = severity
            record["anomaly_ref"] = anomaly
            anomalies.append(anomaly)

    apply_correlation(anomalies)
    for record in records:
        anomaly = record.get("anomaly_ref")
        if anomaly:
            record["correlated_with"] = anomaly.get("correlated_with")
            record["notification_suppressed"] = anomaly.get("notification_suppressed", False)

        data = record["data"]
        save_prediction(
            data["log_id"],
            data["device"],
            data["intf"],
            record["prediction"],
            record["confidence"],
            detection_source=record["detection_source"],
            severity=record["severity"],
            correlated_with=record["correlated_with"],
            notification_suppressed=record["notification_suppressed"],
        )

        if record["prediction"] == "anomaly":
            log.info(
                "Anomaly %s %s source=%s severity=%s confidence=%.2f suppressed=%s",
                data["device"],
                data["intf"],
                record["detection_source"],
                record["severity"],
                record["confidence"],
                record["notification_suppressed"],
            )

    return [a for a in anomalies if not a.get("notification_suppressed")]
