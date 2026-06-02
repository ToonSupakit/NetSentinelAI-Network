"""predict_one behaviour: rules vs ML vs missing model."""

from unittest.mock import MagicMock

import app.predictor as pred


def _base_row(**overrides):
    row = {
        "log_id": 1,
        "device": "R1",
        "intf": "Gi0/0",
        "label": "normal",
        "is_device_down": False,
        "is_admin_down": False,
        "status_num": 1,
        "protocol_num": 1,
        "reliability": 255,
        "network_load": 1,
        "rxload": 1,
        "input_errors": 0,
        "link_type": "LAN",
    }
    row.update(overrides)
    return row


def _mock_model(predict_val, decision_val):
    m = MagicMock()
    m.predict = MagicMock(return_value=[predict_val])
    m.decision_function = MagicMock(return_value=[decision_val])
    return m


def test_predict_device_unreachable():
    label, conf, src = pred.predict_one(_base_row(is_device_down=True))
    assert label == "anomaly" and conf == 1.0 and src == "device_unreachable"


def test_predict_rules_anomaly():
    label, conf, src = pred.predict_one(_base_row(label="anomaly"))
    assert label == "anomaly" and src == "rules"


def test_predict_no_model(monkeypatch):
    monkeypatch.setattr(pred, "model", None)
    label, conf, src = pred.predict_one(_base_row())
    assert label == "normal" and conf == 1.0 and src == "healthy"


def test_predict_isolation_forest_outlier(monkeypatch):
    monkeypatch.setattr(pred, "model", _mock_model(-1, -0.2))
    label, conf, src = pred.predict_one(_base_row(network_load=30, rxload=30))
    assert label == "anomaly" and src == "ai"
    assert 0.0 <= conf <= 1.0


def test_predict_isolation_forest_inlier(monkeypatch):
    monkeypatch.setattr(pred, "model", _mock_model(1, 0.1))
    label, conf, src = pred.predict_one(_base_row())
    assert label == "normal" and conf == 1.0 and src == "healthy"


def test_predict_rules_and_ai_agree(monkeypatch):
    monkeypatch.setattr(pred, "model", _mock_model(-1, -0.5))
    label, conf, src = pred.predict_one(_base_row(label="anomaly", network_load=30, rxload=30))
    assert label == "anomaly" and src == "rules+ai"
    assert conf >= 0.95


def test_predict_uses_model_feature_names(monkeypatch):
    seen = {}

    class FeatureAwareModel:
        feature_names_in_ = ["reliability", "tx_delta", "uptime_pct"]

        def predict(self, features):
            seen["columns"] = list(features.columns)
            seen["tx_delta"] = features.loc[0, "tx_delta"]
            return [1]

        def decision_function(self, features):
            return [0.2]

    monkeypatch.setattr(pred, "model", FeatureAwareModel())

    label, _conf, src = pred.predict_one(_base_row(tx_delta=42, uptime_pct=88))

    assert label == "normal"
    assert src == "healthy"
    assert seen == {"columns": ["reliability", "tx_delta", "uptime_pct"], "tx_delta": 42}


def test_ai_only_anomaly_has_medium_severity(monkeypatch):
    monkeypatch.setattr(pred, "model", _mock_model(-1, -0.3))
    data = _base_row(network_load=30, rxload=30)
    label, conf, src = pred.predict_one(data)

    assert label == "anomaly"
    assert src == "ai"
    assert pred.classify_severity(data, conf, src) == "medium"


def test_analyze_cause_for_ai_fallback_has_generic_guidance(monkeypatch):
    monkeypatch.setattr(
        pred, "config", {"model": {"threshold_load": 20, "threshold_reliability": 200, "threshold_errors": 10}}
    )
    causes, suggestions = pred.analyze_cause(_base_row())

    assert any("AI" in cause for cause in causes)
    assert suggestions


def test_predict_all_suppresses_correlated_downstream(monkeypatch):
    monkeypatch.setattr(pred, "model", None)
    monkeypatch.setattr(pred, "enrich_runtime_features", lambda row: row)
    saved = []
    monkeypatch.setattr(pred, "save_prediction", lambda *args, **kwargs: saved.append((args, kwargs)))

    root = _base_row(
        log_id=10,
        device="Core1",
        intf="Gi0/0",
        label="anomaly",
        status_num=0,
        protocol_num=0,
        device_role="core",
        interface_role="uplink",
        zone="A",
    )
    child = _base_row(
        log_id=11,
        device="Access1",
        intf="Gi0/1",
        label="anomaly",
        status_num=0,
        protocol_num=0,
        device_role="access",
        interface_role="access",
        upstream_devices=["Core1"],
        zone="A",
    )

    reported = pred.predict_all([root, child])

    assert len(reported) == 1
    assert reported[0]["device"] == "Core1"
    assert reported[0]["severity"] == "critical"
    assert saved[1][1]["notification_suppressed"] is True
    assert saved[1][1]["correlated_with"] == "Core1:Gi0/0"
