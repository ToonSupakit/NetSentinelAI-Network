# à¸™à¸³à¹€à¸‚à¹‰à¸²à¹„à¸¥à¸šà¸£à¸²à¸£à¸µà¸—à¸µà¹ˆà¸ˆà¸³à¹€à¸›à¹‡à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¸ˆà¸±à¸”à¸à¸²à¸£à¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥
from sqlalchemy import (
    create_engine,
    text,
)  # à¹„à¸¥à¸šà¸£à¸²à¸£à¸µà¸ªà¸³à¸«à¸£à¸±à¸šà¸ˆà¸±à¸”à¸à¸²à¸£à¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥ SQL
from datetime import datetime  # à¸ªà¸³à¸«à¸£à¸±à¸šà¸ˆà¸±à¸”à¸à¸²à¸£à¸§à¸±à¸™à¸—à¸µà¹ˆà¹à¸¥à¸°à¹€à¸§à¸¥à¸²
import yaml  # à¸ªà¸³à¸«à¸£à¸±à¸šà¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²
import logging
import os
from dotenv import load_dotenv

from app import user_repository

load_dotenv()
log = logging.getLogger(__name__)

# à¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²à¸ˆà¸²à¸ config.yaml
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# à¸ªà¸£à¹‰à¸²à¸‡à¸à¸²à¸£à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸à¸±à¸šà¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥ MySQL â€” à¸­à¹ˆà¸²à¸™ URL à¸ˆà¸²à¸ .env
DB_URL = os.getenv("DB_URL", config.get("database", {}).get("url", ""))
engine = create_engine(DB_URL, pool_size=5, max_overflow=10, pool_recycle=3600, pool_pre_ping=True)


def init_db():
    """à¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸£à¸´à¹ˆà¸¡à¸•à¹‰à¸™à¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥ à¸ªà¸£à¹‰à¸²à¸‡à¸•à¸²à¸£à¸²à¸‡à¸—à¸µà¹ˆà¸ˆà¸³à¹€à¸›à¹‡à¸™"""
    with engine.connect() as conn:
        # à¸ªà¸£à¹‰à¸²à¸‡à¸•à¸²à¸£à¸²à¸‡ interface_logs à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥ interface
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS interface_logs (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                device_name    VARCHAR(50),
                interface_name VARCHAR(50),
                ip_address     VARCHAR(20),
                status         VARCHAR(20),
                protocol       VARCHAR(20),
                reliability    INT DEFAULT 255,
                network_load   INT DEFAULT 1,
                rxload         INT DEFAULT 1,
                input_errors   INT DEFAULT 0,
                link_type      VARCHAR(20),
                zone           VARCHAR(20),
                location       VARCHAR(50),
                collected_at   DATETIME,
                created_at     TIMESTAMP DEFAULT current_timestamp(),
                label          VARCHAR(10)
            )
        """))
        # à¸ªà¸£à¹‰à¸²à¸‡à¸•à¸²à¸£à¸²à¸‡ ai_predictions à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸à¹‡à¸šà¸œà¸¥à¸à¸²à¸£à¸—à¸³à¸™à¸²à¸¢à¸‚à¸­à¸‡ AI
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                log_id           INT,
                device_name      VARCHAR(50),
                interface_name   VARCHAR(50),
                prediction_label VARCHAR(50),
                confidence_score FLOAT,
                detection_source VARCHAR(32) NULL,
                severity         VARCHAR(16) NULL,
                correlated_with  VARCHAR(128) NULL,
                notification_suppressed BOOLEAN DEFAULT FALSE,
                is_fixed         BOOLEAN DEFAULT FALSE,
                fixed_at         DATETIME,
                predicted_at     DATETIME,
                FOREIGN KEY (log_id) REFERENCES interface_logs(id)
            )
        """))
        # à¸ªà¸£à¹‰à¸²à¸‡à¸•à¸²à¸£à¸²à¸‡ devices à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸­à¸¸à¸›à¸à¸£à¸“à¹Œ
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS devices (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(50) UNIQUE,
                host        VARCHAR(50),
                device_type VARCHAR(50),
                username    VARCHAR(50),
                password    VARCHAR(50),
                secret      VARCHAR(50),
                location    VARCHAR(50),
                zone        VARCHAR(20),
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMP DEFAULT current_timestamp()
            )
        """))
        # à¸ªà¸£à¹‰à¸²à¸‡à¸•à¸²à¸£à¸²à¸‡ users à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰ Dashboard
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                username    VARCHAR(50) UNIQUE NOT NULL,
                password    VARCHAR(255) NOT NULL,
                role        VARCHAR(20) DEFAULT 'admin',
                created_at  TIMESTAMP DEFAULT current_timestamp()
            )
        """))

        # â”€â”€ à¸ªà¸£à¹‰à¸²à¸‡ Indexes à¹€à¸žà¸·à¹ˆà¸­à¹€à¸žà¸´à¹ˆà¸¡à¸„à¸§à¸²à¸¡à¹€à¸£à¹‡à¸§ query â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        index_statements = [
            "CREATE INDEX idx_logs_device_intf_time ON interface_logs(device_name, interface_name, collected_at)",
            "CREATE INDEX idx_logs_label ON interface_logs(label)",
            "CREATE INDEX idx_logs_collected_at ON interface_logs(collected_at)",
            "CREATE INDEX idx_pred_label_date ON ai_predictions(prediction_label, predicted_at)",
            "CREATE INDEX idx_pred_log_id ON ai_predictions(log_id)",
        ]
        for stmt in index_statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass  # index à¸­à¸²à¸ˆà¸¡à¸µà¸­à¸¢à¸¹à¹ˆà¹à¸¥à¹‰à¸§

        conn.commit()
    _migrate_ai_predictions_detection_source()
    _migrate_ai_predictions_intel_columns()
    _seed_default_admin()
    log.info("Database initialized with indexes")


def _migrate_ai_predictions_detection_source():
    """à¹€à¸žà¸´à¹ˆà¸¡à¸„à¸­à¸¥à¸±à¸¡à¸™à¹Œ detection_source à¸ªà¸³à¸«à¸£à¸±à¸šà¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸—à¸µà¹ˆà¸ªà¸£à¹‰à¸²à¸‡à¸ˆà¸²à¸à¸ªà¸„à¸µà¸¡à¸²à¹€à¸à¹ˆà¸²"""
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE ai_predictions ADD COLUMN detection_source VARCHAR(32) NULL"))
            conn.commit()
    except Exception:
        pass


def _migrate_ai_predictions_intel_columns():
    statements = [
        "ALTER TABLE ai_predictions ADD COLUMN severity VARCHAR(16) NULL",
        "ALTER TABLE ai_predictions ADD COLUMN correlated_with VARCHAR(128) NULL",
        "ALTER TABLE ai_predictions ADD COLUMN notification_suppressed BOOLEAN DEFAULT FALSE",
    ]
    for stmt in statements:
        try:
            with engine.connect() as conn:
                conn.execute(text(stmt))
                conn.commit()
        except Exception:
            pass


def cleanup_old_data(days=30):
    """à¸¥à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¹€à¸à¹ˆà¸²à¸à¸§à¹ˆà¸² N à¸§à¸±à¸™ à¹€à¸žà¸·à¹ˆà¸­à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰ DB à¸šà¸§à¸¡"""
    try:
        with engine.connect() as conn:
            # à¸¥à¸š predictions à¹€à¸à¹ˆà¸²
            result1 = conn.execute(
                text("""
                DELETE FROM ai_predictions
                WHERE predicted_at < DATE_SUB(NOW(), INTERVAL :days DAY)
            """),
                {"days": days},
            )

            # à¸¥à¸š logs à¹€à¸à¹ˆà¸²à¸—à¸µà¹ˆà¹„à¸¡à¹ˆà¸¡à¸µ prediction à¸­à¹‰à¸²à¸‡à¸­à¸´à¸‡
            result2 = conn.execute(
                text("""
                DELETE FROM interface_logs
                WHERE collected_at < DATE_SUB(NOW(), INTERVAL :days DAY)
                  AND id NOT IN (SELECT log_id FROM ai_predictions)
            """),
                {"days": days},
            )

            conn.commit()
            total = result1.rowcount + result2.rowcount
            if total > 0:
                log.info(f"Cleanup: à¸¥à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¹€à¸à¹ˆà¸² {total} records (>{days} à¸§à¸±à¸™)")
    except Exception as e:
        log.error(f"Cleanup error: {e}")


def get_analytics():
    with engine.connect() as conn:

        # 1. à¸ªà¸£à¸¸à¸› anomaly à¸—à¸±à¹‰à¸‡à¸«à¸¡à¸”
        anomaly_summary = conn.execute(text("""
            SELECT 
                COUNT(*) as total_logs,
                SUM(label = 'anomaly') as total_anomaly,
                SUM(label = 'normal')  as total_normal,
                ROUND(SUM(label = 'anomaly') / NULLIF(COUNT(*), 0) * 100, 1) as anomaly_pct
            FROM interface_logs
        """)).fetchone()

        # 2. anomaly à¸§à¸±à¸™à¸™à¸µà¹‰
        anomaly_today = conn.execute(text("""
            SELECT COUNT(*) as today_anomaly
            FROM ai_predictions
            WHERE prediction_label = 'anomaly'
              AND DATE(predicted_at) = CURDATE()
        """)).fetchone()

        # 3. fix rate
        fix_rate = conn.execute(text("""
            SELECT 
                COUNT(*)                                    as total_anomaly,
                SUM(is_fixed = 1)                           as total_fixed,
                ROUND(SUM(is_fixed = 1) / NULLIF(COUNT(*), 0) * 100, 1) as fix_rate_pct
            FROM ai_predictions
            WHERE prediction_label = 'anomaly'
        """)).fetchone()

        # 4. top 5 device à¸—à¸µà¹ˆà¸¡à¸µà¸›à¸±à¸à¸«à¸²à¹€à¸¢à¸­à¸°à¸ªà¸¸à¸”
        top_devices = conn.execute(text("""
            SELECT device_name, COUNT(*) as anomaly_count
            FROM ai_predictions
            WHERE prediction_label = 'anomaly'
            GROUP BY device_name
            ORDER BY anomaly_count DESC
            LIMIT 5
        """)).fetchall()

        # 5. top 5 interface à¸—à¸µà¹ˆà¸¡à¸µà¸›à¸±à¸à¸«à¸²à¹€à¸¢à¸­à¸°à¸ªà¸¸à¸”
        top_interfaces = conn.execute(text("""
            SELECT device_name, interface_name, COUNT(*) as anomaly_count
            FROM ai_predictions
            WHERE prediction_label = 'anomaly'
            GROUP BY device_name, interface_name
            ORDER BY anomaly_count DESC
            LIMIT 5
        """)).fetchall()

        # 6. uptime à¹à¸•à¹ˆà¸¥à¸° device (% à¸‚à¸­à¸‡à¹€à¸§à¸¥à¸²à¸—à¸µà¹ˆ normal)
        uptime = conn.execute(text("""
            SELECT 
                device_name,
                ROUND(SUM(label = 'normal') / COUNT(*) * 100, 1) as uptime_pct,
                COUNT(*) as total_records
            FROM interface_logs
            GROUP BY device_name
            ORDER BY device_name
        """)).fetchall()

        # 7. traffic trend à¸£à¸²à¸¢à¸Šà¸±à¹ˆà¸§à¹‚à¸¡à¸‡ (6 à¸Šà¸±à¹ˆà¸§à¹‚à¸¡à¸‡à¸¥à¹ˆà¸²à¸ªà¸¸à¸”)
        traffic_trend = conn.execute(text("""
            SELECT 
                DATE_FORMAT(collected_at, '%H:00') as hour,
                ROUND(AVG(network_load), 1)        as avg_load,
                MAX(network_load)                  as max_load,
                COUNT(*)                           as records
            FROM interface_logs
            WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
            GROUP BY DATE_FORMAT(collected_at, '%H:00')
            ORDER BY hour ASC
        """)).fetchall()

        # 8. anomaly by type
        anomaly_by_type = conn.execute(text("""
            SELECT 
                status, protocol,
                COUNT(*) as count
            FROM interface_logs
            WHERE label = 'anomaly'
            GROUP BY status, protocol
            ORDER BY count DESC
        """)).fetchall()

        return {
            "summary": anomaly_summary,
            "today": anomaly_today,
            "fix_rate": fix_rate,
            "top_devices": top_devices,
            "top_interfaces": top_interfaces,
            "uptime": uptime,
            "traffic_trend": traffic_trend,
            "anomaly_by_type": anomaly_by_type,
        }


def save_log(device, intf, ip, status, proto, rel, tx, rx, err, ltype, zone, location, label):
    now = datetime.now()
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            INSERT INTO interface_logs
            (device_name, interface_name, ip_address, status, protocol,
             reliability, network_load, rxload, input_errors, link_type,
             zone, location, collected_at, created_at, label)
            VALUES (:device, :intf, :ip, :status, :proto,
                    :rel, :load, :rx, :err, :ltype,
                    :zone, :location, :now, :now, :label)
        """),
            {
                "device": device,
                "intf": intf,
                "ip": ip,
                "status": status,
                "proto": proto,
                "rel": rel,
                "load": tx,
                "rx": rx,
                "err": err,
                "ltype": ltype,
                "zone": zone,
                "location": location,
                "now": now,
                "label": label,
            },
        )
        conn.commit()
        return result.lastrowid


def get_interface_runtime_features(device, intf, current_log_id=None, window=20):
    """Build recent per-interface features for runtime prediction."""
    try:
        window = max(2, min(int(window), 200))
    except (TypeError, ValueError):
        window = 20

    where_current = "AND id <= :current_log_id" if current_log_id else ""
    params = {"device": device, "intf": intf, "limit": window, "current_log_id": current_log_id or 0}

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                SELECT network_load, rxload, input_errors, label
                FROM interface_logs
                WHERE device_name = :device
                  AND interface_name = :intf
                  {where_current}
                ORDER BY collected_at DESC, id DESC
                LIMIT :limit
            """),
                params,
            ).fetchall()
    except Exception as e:
        log.debug("Runtime feature query failed for %s/%s: %s", device, intf, e)
        rows = []

    if not rows:
        return {
            "tx_delta": 0,
            "rx_delta": 0,
            "error_rate": 0,
            "uptime_pct": 100,
            "tx_baseline": None,
            "rx_baseline": None,
            "tx_baseline_delta": 0,
            "rx_baseline_delta": 0,
        }

    latest = rows[0]
    older = rows[1] if len(rows) > 1 else None
    normal_rows = [r for r in rows if r[3] == "normal"]
    if normal_rows:
        tx_baseline = sum(float(r[0] or 0) for r in normal_rows) / len(normal_rows)
        rx_baseline = sum(float(r[1] or 0) for r in normal_rows) / len(normal_rows)
    else:
        tx_baseline = float(latest[0] or 0)
        rx_baseline = float(latest[1] or 0)

    tx_delta = float(latest[0] or 0) - (float(older[0] or 0) if older else float(latest[0] or 0))
    rx_delta = float(latest[1] or 0) - (float(older[1] or 0) if older else float(latest[1] or 0))
    err_delta = float(latest[2] or 0) - (float(older[2] or 0) if older else 0)
    uptime_pct = (sum(1 for r in rows if r[3] == "normal") / len(rows)) * 100

    return {
        "tx_delta": tx_delta,
        "rx_delta": rx_delta,
        "error_rate": max(0, err_delta),
        "uptime_pct": uptime_pct,
        "tx_baseline": tx_baseline,
        "rx_baseline": rx_baseline,
        "tx_baseline_delta": float(latest[0] or 0) - tx_baseline,
        "rx_baseline_delta": float(latest[1] or 0) - rx_baseline,
    }


def save_prediction(
    log_id,
    device,
    intf,
    prediction,
    confidence,
    detection_source=None,
    severity=None,
    correlated_with=None,
    notification_suppressed=False,
):
    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO ai_predictions
            (log_id, device_name, interface_name, prediction_label,
             confidence_score, detection_source, severity, correlated_with,
             notification_suppressed, predicted_at)
            VALUES (:log_id, :device, :intf, :label, :score, :src, :severity,
                    :correlated_with, :notification_suppressed, :now)
        """),
            {
                "log_id": log_id,
                "device": device,
                "intf": intf,
                "label": prediction,
                "score": confidence,
                "src": detection_source,
                "severity": severity,
                "correlated_with": correlated_with,
                "notification_suppressed": bool(notification_suppressed),
                "now": datetime.now(),
            },
        )
        conn.commit()


def get_anomaly_history(limit=10):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT p.predicted_at, p.device_name, p.interface_name,
                    p.prediction_label, p.confidence_score, p.is_fixed,
                    l.status, l.protocol, l.network_load, l.rxload,
                    p.detection_source, p.severity, p.correlated_with,
                    p.notification_suppressed
            FROM ai_predictions p
            JOIN interface_logs l ON p.log_id = l.id
            WHERE p.prediction_label = 'anomaly'
            ORDER BY p.predicted_at DESC
            LIMIT :limit
        """),
            {"limit": limit},
        )
        return result.fetchall()


def mark_as_fixed(log_id):
    with engine.connect() as conn:
        conn.execute(
            text("""
            UPDATE ai_predictions
            SET is_fixed = TRUE, fixed_at = :now
            WHERE log_id = :log_id
        """),
            {"log_id": log_id, "now": datetime.now()},
        )
        conn.commit()


def mark_anomalies_fixed_for_interface(device_name, interface_name):
    """à¸«à¸¥à¸±à¸‡ remediation à¸ˆà¸²à¸ Dashboard â€” à¸—à¸³à¹€à¸„à¸£à¸·à¹ˆà¸­à¸‡à¸«à¸¡à¸²à¸¢ anomaly à¸—à¸µà¹ˆà¸¢à¸±à¸‡à¹„à¸¡à¹ˆ fixed à¸‚à¸­à¸‡ interface à¸™à¸µà¹‰"""
    now = datetime.now()
    with engine.connect() as conn:
        conn.execute(
            text("""
            UPDATE ai_predictions
            SET is_fixed = TRUE, fixed_at = :now
            WHERE prediction_label = 'anomaly'
              AND COALESCE(is_fixed, 0) = 0
              AND device_name = :d AND interface_name = :i
        """),
            {"d": device_name, "i": interface_name, "now": now},
        )
        conn.commit()


def get_device_status():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT l.device_name, l.interface_name, l.ip_address,
                    l.status, l.protocol, l.network_load, l.rxload,
                    l.reliability, l.label, l.collected_at
            FROM interface_logs l
            INNER JOIN (
                SELECT device_name, interface_name, MAX(collected_at) as max_time
                FROM interface_logs
                GROUP BY device_name, interface_name
            ) latest ON l.device_name = latest.device_name
                    AND l.interface_name = latest.interface_name
                    AND l.collected_at = latest.max_time
            ORDER BY l.device_name, l.interface_name
        """))
        return result.fetchall()


# â”€â”€ User Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _seed_default_admin():
    user_repository.seed_default_admin(engine)


def authenticate_user(username, password):
    return user_repository.authenticate_user(engine, username, password)


def create_user(username, password, role="user"):
    return user_repository.create_user(engine, username, password, role)


def get_all_users():
    return user_repository.get_all_users(engine)


def delete_user(user_id, actor_id=None):
    return user_repository.delete_user(engine, user_id, actor_id=actor_id)


def update_user_role(user_id, role):
    return user_repository.update_user_role(engine, user_id, role)
