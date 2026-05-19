# à¸™à¸³à¹€à¸‚à¹‰à¸²à¹„à¸¥à¸šà¸£à¸²à¸£à¸µà¸—à¸µà¹ˆà¸ˆà¸³à¹€à¸›à¹‡à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¸à¸²à¸£à¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸ˆà¸²à¸à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¹€à¸„à¸£à¸·à¸­à¸‚à¹ˆà¸²à¸¢
from netmiko import (
    ConnectHandler,
)  # à¹„à¸¥à¸šà¸£à¸²à¸£à¸µà¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸à¸±à¸šà¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¹€à¸„à¸£à¸·à¸­à¸‚à¹ˆà¸²à¸¢
from app.db import (
    save_log,
)  # à¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¸šà¸±à¸™à¸—à¸¶à¸à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸¥à¸‡à¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml  # à¸ªà¸³à¸«à¸£à¸±à¸šà¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²
import re  # à¸ªà¸³à¸«à¸£à¸±à¸šà¸à¸²à¸£à¸›à¸£à¸°à¸¡à¸§à¸¥à¸œà¸¥à¸‚à¹‰à¸­à¸„à¸§à¸²à¸¡à¸”à¹‰à¸§à¸¢ regular expression
import time  # à¸ªà¸³à¸«à¸£à¸±à¸šà¸ˆà¸±à¸”à¸à¸²à¸£à¹€à¸§à¸¥à¸²
import os
import logging
from dotenv import load_dotenv
from app import collector_rules
from app.snmp_helper import get_snmp_interfaces
from app.simulator import simulated_interfaces, simulator_enabled

load_dotenv()
log = logging.getLogger(__name__)

# à¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²à¸ˆà¸²à¸ config.yaml
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# à¸­à¹ˆà¸²à¸™à¹„à¸Ÿà¸¥à¹Œà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¸ˆà¸²à¸ devices.yaml
with open("config/devices.yaml", "r", encoding="utf-8") as f:
    devices_config = yaml.safe_load(f)

# à¸”à¸¶à¸‡à¸„à¹ˆà¸²à¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²à¸ˆà¸²à¸à¹„à¸Ÿà¸¥à¹Œ config
SKIP_TYPES = [
    s for s in config["anomaly"]["skip_types"] if s is not None
]  # à¸›à¸£à¸°à¹€à¸ à¸— interface à¸—à¸µà¹ˆà¸ˆà¸°à¸‚à¹‰à¸²à¸¡
THRESHOLD_LOAD = config["model"]["threshold_load"]  # à¸„à¹ˆà¸² threshold à¸ªà¸³à¸«à¸£à¸±à¸š network load
THRESHOLD_RELIABILITY = config["model"]["threshold_reliability"]  # à¸„à¹ˆà¸² threshold à¸ªà¸³à¸«à¸£à¸±à¸š reliability
THRESHOLD_ERRORS = config["model"]["threshold_errors"]  # à¸„à¹ˆà¸² threshold à¸ªà¸³à¸«à¸£à¸±à¸š input errors
MAX_RETRIES = 3  # à¸ˆà¸³à¸™à¸§à¸™à¸„à¸£à¸±à¹‰à¸‡à¸ªà¸¹à¸‡à¸ªà¸¸à¸”à¹ƒà¸™à¸à¸²à¸£ retry
RETRY_DELAY = 5  # à¸£à¸°à¸¢à¸°à¹€à¸§à¸¥à¸²à¸«à¸™à¹ˆà¸§à¸‡à¸£à¸°à¸«à¸§à¹ˆà¸²à¸‡ retry (à¸§à¸´à¸™à¸²à¸—à¸µ)

# â”€â”€ Link Type â€” à¸­à¹ˆà¸²à¸™à¸ˆà¸²à¸ config (à¹„à¸¡à¹ˆ hardcode IP) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
LINK_TYPE_RULES = config.get("link_types", {}).get("rules", [])
LINK_TYPE_DEFAULT = config.get("link_types", {}).get("default", "Other")


def infer_device_role(device):
    return collector_rules.infer_device_role(device)


def infer_interface_role(device, intf, data):
    return collector_rules.infer_interface_role(device, intf, data)


def upstream_devices(device):
    return collector_rules.upstream_devices(device)


def get_device_credentials(device):
    """à¸”à¸¶à¸‡ credentials à¸ˆà¸²à¸ device config à¸«à¸£à¸·à¸­ .env default (à¸­à¹ˆà¸²à¸™ os.environ à¸—à¸¸à¸à¸„à¸£à¸±à¹‰à¸‡)"""
    return {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": device.get("username") or os.getenv("DEVICE_USERNAME", "admin"),
        "password": device.get("password") or os.getenv("DEVICE_PASSWORD", "admin"),
        "secret": device.get("secret") or os.getenv("DEVICE_SECRET", "admin"),
    }


def should_skip(intf, ip, is_admin_down):
    return collector_rules.should_skip(intf, ip, is_admin_down, SKIP_TYPES)


def get_link_type(ip):
    return collector_rules.get_link_type(ip, LINK_TYPE_RULES, LINK_TYPE_DEFAULT)


def parse_interfaces(raw):
    """à¹à¸›à¸¥à¸‡à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸ˆà¸²à¸à¸„à¸³à¸ªà¸±à¹ˆà¸‡ show interfaces à¹€à¸›à¹‡à¸™à¹‚à¸„à¸£à¸‡à¸ªà¸£à¹‰à¸²à¸‡à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸—à¸µà¹ˆà¹ƒà¸Šà¹‰à¸‡à¸²à¸™à¹„à¸”à¹‰"""
    result = {}
    current = None
    for line in raw.splitlines():
        # à¸«à¸²à¸šà¸£à¸£à¸—à¸±à¸”à¸—à¸µà¹ˆà¸¡à¸µà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸ªà¸–à¸²à¸™à¸°à¸‚à¸­à¸‡ interface
        m = re.match(r"^(\S+)\s+is\s+(.+),\s+line protocol is\s+(\S+)", line)
        if m:
            current = m.group(1)
            result[current] = {
                "phys": m.group(2).strip(),  # à¸ªà¸–à¸²à¸™à¸° physical
                "proto": m.group(3).strip(),  # à¸ªà¸–à¸²à¸™à¸° protocol
                "reliability": "255",  # à¸„à¹ˆà¸²à¸„à¸§à¸²à¸¡à¹€à¸ªà¸–à¸µà¸¢à¸£ (default)
                "txload": "1",  # à¸„à¹ˆà¸² load à¸‚à¸²à¸­à¸­à¸ (default)
                "rxload": "1",  # à¸„à¹ˆà¸² load à¸‚à¸²à¹€à¸‚à¹‰à¸² (default)
                "input_errors": "0",  # à¸ˆà¸³à¸™à¸§à¸™ input errors (default)
            }
        if current:
            # à¸«à¸²à¸„à¹ˆà¸² reliability, txload, rxload
            r = re.search(r"reliability (\d+)/255,\s*txload (\d+)/255,\s*rxload (\d+)/255", line)
            if r:
                result[current]["reliability"] = r.group(1)
                result[current]["txload"] = r.group(2)
                result[current]["rxload"] = r.group(3)
            # à¸«à¸²à¸ˆà¸³à¸™à¸§à¸™ input errors
            e = re.search(r"(\d+) input errors", line)
            if e:
                result[current]["input_errors"] = e.group(1)
    return result


# â”€â”€ à¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¸à¸³à¸«à¸™à¸” label (à¸›à¸à¸•à¸´/à¸œà¸´à¸”à¸›à¸à¸•à¸´) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def get_label(status_num, protocol_num, network_load, rxload, reliability, input_errors, is_admin_down):
    return collector_rules.get_label(
        status_num,
        protocol_num,
        network_load,
        rxload,
        reliability,
        input_errors,
        is_admin_down,
        THRESHOLD_LOAD,
        THRESHOLD_RELIABILITY,
        THRESHOLD_ERRORS,
    )


def collect_device(device, on_timeout=None):
    """à¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥ interface à¸—à¸±à¹‰à¸‡à¸«à¸¡à¸”à¸ˆà¸²à¸à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¹€à¸”à¸µà¸¢à¸§à¸œà¹ˆà¸²à¸™ SNMP"""
    host = device["host"]
    community = device.get("snmp_community", os.getenv("SNMP_COMMUNITY", "public"))

    for attempt in range(MAX_RETRIES):
        try:
            results = []

            # à¸”à¸¶à¸‡à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸œà¹ˆà¸²à¸™ SNMP à¸«à¸£à¸·à¸­ simulator à¸ªà¸³à¸«à¸£à¸±à¸š demo
            if simulator_enabled(config) or device.get("simulate"):
                interfaces_data = simulated_interfaces(device, config)
            else:
                oid_overrides = device.get("snmp_oids") or config.get("snmp", {}).get("oids")
                interfaces_data = get_snmp_interfaces(host, community, oid_overrides=oid_overrides)

            for data in interfaces_data:
                intf = data["intf"]
                ip = data["ip"]
                is_admin_down = data.get("is_admin_down", False)

                if should_skip(intf, ip, is_admin_down):
                    continue

                status_num = 0 if (is_admin_down or data["status"] == "down") else 1
                protocol_num = 1 if data["protocol"] == "up" else 0

                reliability = int(data["reliability"])
                network_load = int(data["network_load"])
                rxload = int(data["rxload"])
                input_errors = int(data["input_errors"])
                link_type = get_link_type(ip)
                device_role = infer_device_role(device)
                interface_role = infer_interface_role(device, intf, data)
                upstream = upstream_devices(device)

                label = get_label(
                    status_num, protocol_num, network_load, rxload, reliability, input_errors, is_admin_down
                )

                log_id = save_log(
                    device["name"],
                    intf,
                    ip,
                    data["status"],
                    data["protocol"],
                    reliability,
                    network_load,
                    rxload,
                    input_errors,
                    link_type,
                    device.get("zone", "Unknown"),
                    device.get("location", "Unknown"),
                    label,
                )

                results.append(
                    {
                        "log_id": log_id,
                        "device": device["name"],
                        "intf": intf,
                        "ip": ip,
                        "status_num": status_num,
                        "protocol_num": protocol_num,
                        "reliability": reliability,
                        "network_load": network_load,
                        "rxload": rxload,
                        "input_errors": input_errors,
                        "link_type": link_type,
                        "label": label,
                        "is_admin_down": is_admin_down,
                        "device_role": device_role,
                        "interface_role": interface_role,
                        "upstream_devices": upstream,
                        "zone": device.get("zone", "Unknown"),
                        "location": device.get("location", "Unknown"),
                    }
                )

            # à¹€à¸¡à¸·à¹ˆà¸­à¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸ªà¸³à¹€à¸£à¹‡à¸ˆ â†’ update record ALL à¹ƒà¸«à¹‰à¹€à¸›à¹‡à¸™ up (à¸à¸£à¸“à¸µà¹€à¸„à¸¢ down)
            save_log(
                device["name"],
                "ALL",
                host,
                "up",
                "up",
                255,
                0,
                0,
                0,
                "Unknown",
                device.get("zone", "Unknown"),
                device.get("location", "Unknown"),
                "normal",
            )

            log.info(f"{device['name']}: à¹€à¸à¹‡à¸šà¹„à¸”à¹‰ {len(results)} interface")
            return results

        except Exception as e:
            # à¸ˆà¸±à¸”à¸à¸²à¸£à¸à¸²à¸£ retry à¸–à¹‰à¸²à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸¥à¹‰à¸¡à¹€à¸«à¸¥à¸§
            if attempt < MAX_RETRIES - 1:
                log.warning(f"{device['name']} retry {attempt+1}/{MAX_RETRIES}: {e}")
                time.sleep(RETRY_DELAY)
            else:
                log.error(f"{device['name']}: à¸«à¸¡à¸” retry à¹à¸¥à¹‰à¸§ â€” {e}")
                # à¹à¸ˆà¹‰à¸‡à¹€à¸•à¸·à¸­à¸™ timeout à¸–à¹‰à¸²à¸¡à¸µà¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™ callback
                if on_timeout:
                    on_timeout(
                        {
                            "device": device["name"],
                            "host": device["host"],
                            "zone": device.get("zone", "Unknown"),
                            "error": str(e),
                        }
                    )

                # à¸šà¸±à¸™à¸—à¸¶à¸ device down à¸¥à¸‡ DB à¹€à¸žà¸·à¹ˆà¸­à¹ƒà¸«à¹‰ predictor à¸•à¸£à¸§à¸ˆà¸ˆà¸±à¸šà¹„à¸”à¹‰
                log_id = save_log(
                    device["name"],
                    "ALL",
                    device["host"],
                    "down",
                    "down",
                    0,
                    0,
                    0,
                    0,
                    "Unknown",
                    device.get("zone", "Unknown"),
                    device.get("location", "Unknown"),
                    "anomaly",
                )
                return [
                    {
                        "log_id": log_id,
                        "device": device["name"],
                        "intf": "ALL",
                        "ip": device["host"],
                        "status_num": 0,
                        "protocol_num": 0,
                        "reliability": 0,
                        "network_load": 0,
                        "rxload": 0,
                        "input_errors": 0,
                        "link_type": "Unknown",
                        "label": "anomaly",
                        "is_admin_down": False,
                        "is_device_down": True,
                        "error": str(e),
                        "device_role": infer_device_role(device),
                        "interface_role": "device",
                        "upstream_devices": upstream_devices(device),
                        "zone": device.get("zone", "Unknown"),
                        "location": device.get("location", "Unknown"),
                    }
                ]

    return []


# â”€â”€ à¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™à¸ªà¸³à¸«à¸£à¸±à¸šà¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸ˆà¸²à¸à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¸—à¸±à¹‰à¸‡à¸«à¸¡à¸” (à¸žà¸£à¹‰à¸­à¸¡à¸à¸±à¸™) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def collect_all(on_timeout=None):
    """à¹€à¸à¹‡à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥ interface à¸—à¸±à¹‰à¸‡à¸«à¸¡à¸”à¸ˆà¸²à¸à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¸—à¸¸à¸à¸•à¸±à¸§ â€” à¹ƒà¸Šà¹‰ ThreadPoolExecutor"""
    all_results = []
    devices = devices_config["devices"]
    max_workers = min(len(devices), 8)  # à¹„à¸¡à¹ˆà¹€à¸à¸´à¸™ 8 threads

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(collect_device, device, on_timeout): device["name"] for device in devices}
        for future in as_completed(futures):
            device_name = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                log.error(f"{device_name}: ThreadPool error â€” {e}")

    return all_results
