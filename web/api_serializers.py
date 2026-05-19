"""JSON serialization helpers for dashboard API rows."""


def serialize_status_rows(rows):
    return [
        {
            "device": row[0],
            "interface": row[1],
            "ip": row[2],
            "status": row[3],
            "protocol": row[4],
            "network_load": row[5],
            "rxload": row[6],
            "reliability": row[7],
            "label": row[8],
            "collected_at": str(row[9]),
        }
        for row in rows
    ]


def serialize_anomaly_rows(rows):
    return [
        {
            "predicted_at": str(row[0]),
            "device": row[1],
            "interface": row[2],
            "label": row[3],
            "confidence": row[4],
            "is_fixed": row[5],
            "status": row[6],
            "protocol": row[7],
            "network_load": row[8],
            "rxload": row[9],
            "detection_source": row[10] if len(row) > 10 else None,
            "severity": row[11] if len(row) > 11 else None,
            "correlated_with": row[12] if len(row) > 12 else None,
            "notification_suppressed": bool(row[13]) if len(row) > 13 else False,
        }
        for row in rows
    ]


def serialize_analytics(data):
    return {
        "summary": list(data["summary"]),
        "today": list(data["today"]),
        "fix_rate": list(data["fix_rate"]),
        "uptime": [list(row) for row in data["uptime"]],
        "top_devices": [list(row) for row in data["top_devices"]],
        "top_interfaces": [list(row) for row in data["top_interfaces"]],
        "traffic_trend": [list(row) for row in data["traffic_trend"]],
        "anomaly_by_type": [list(row) for row in data["anomaly_by_type"]],
    }


def serialize_traffic_rows(rows):
    return [
        {
            "device": row[0],
            "interface": row[1],
            "tx": float(row[2]),
            "rx": float(row[3]),
            "time": row[4],
        }
        for row in rows
    ]
