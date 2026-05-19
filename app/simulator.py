"""Deterministic mock topology for demos without live network devices."""

from __future__ import annotations

import os
import random
import time


def simulator_enabled(config):
    if os.getenv("NETSENTINEL_SIMULATOR", "").lower() in ("1", "true", "yes", "on"):
        return True
    return bool(config.get("simulator", {}).get("enabled"))


def simulated_interfaces(device, config):
    sim_cfg = config.get("simulator", {})
    now_bucket = int(time.time() // max(10, int(sim_cfg.get("period_seconds", 60))))
    seed = f"{device.get('name', 'device')}:{now_bucket}"
    rng = random.Random(seed)
    count = int(device.get("simulated_interfaces", sim_cfg.get("interfaces_per_device", 4)))
    anomaly_rate = float(sim_cfg.get("anomaly_rate", 0.15))

    rows = []
    for idx in range(count):
        intf = f"GigabitEthernet0/{idx}"
        is_uplink = idx == 0
        high = rng.random() < anomaly_rate
        down = rng.random() < anomaly_rate / 4
        tx = rng.randint(1, 12) + (rng.randint(35, 90) if high else 0)
        rx = rng.randint(1, 12) + (rng.randint(25, 80) if high and rng.random() < 0.5 else 0)
        tx = min(tx, 255)
        rx = min(rx, 255)
        rows.append(
            {
                "intf": intf,
                "ip": f"10.{abs(hash(device.get('name', 'd'))) % 200}.{idx}.1",
                "status": "down" if down else "up",
                "protocol": "down" if down else "up",
                "rxload": rx,
                "network_load": tx,
                "reliability": 180 if high and rng.random() < 0.3 else 255,
                "input_errors": rng.randint(15, 60) if high and rng.random() < 0.3 else rng.randint(0, 2),
                "is_admin_down": False,
                "interface_role": "uplink" if is_uplink else "access",
            }
        )
    return rows
