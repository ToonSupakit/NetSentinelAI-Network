"""Pure collector rule helpers for topology, skip, link, and label decisions."""


def infer_device_role(device):
    role = device.get("role") or device.get("device_role") or device.get("topology_role")
    if role:
        return str(role).lower()
    text = " ".join(str(device.get(key, "")) for key in ("name", "location", "zone")).lower()
    if "core" in text:
        return "core"
    if "edge" in text:
        return "edge"
    if "access" in text:
        return "access"
    return "unknown"


def infer_interface_role(device, intf, data):
    role = data.get("interface_role") or data.get("role")
    if role:
        return str(role).lower()
    intf_roles = device.get("interfaces", {}) or device.get("interface_roles", {})
    if isinstance(intf_roles, dict):
        cfg = intf_roles.get(intf)
        if isinstance(cfg, dict):
            role = cfg.get("role") or cfg.get("interface_role")
        else:
            role = cfg
        if role:
            return str(role).lower()
    lowered = intf.lower()
    if "uplink" in lowered or "wan" in lowered:
        return "uplink"
    if "downlink" in lowered:
        return "downlink"
    return "access"


def upstream_devices(device):
    values = []
    for key in ("upstream_device", "parent_device", "depends_on", "uplink_device"):
        value = device.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value:
            values.append(str(value))
    return values


def should_skip(intf, ip, is_admin_down, skip_types):
    del is_admin_down
    for skip in skip_types:
        if intf.startswith(str(skip)):
            return True
    return ip == "unassigned"


def get_link_type(ip, rules, default):
    if ip == "unknown":
        return "Unknown"
    for rule in rules:
        prefix = str(rule["prefix"])
        if ip.startswith(prefix) or prefix in ip:
            return rule["type"]
    return default


def get_label(
    status_num,
    protocol_num,
    network_load,
    rxload,
    reliability,
    input_errors,
    is_admin_down,
    threshold_load,
    threshold_reliability,
    threshold_errors,
):
    if is_admin_down:
        return "anomaly"
    if status_num == 0:
        return "anomaly"
    if protocol_num == 0:
        return "anomaly"
    if network_load > threshold_load:
        return "anomaly"
    if rxload > threshold_load:
        return "anomaly"
    if reliability < threshold_reliability:
        return "anomaly"
    if input_errors > threshold_errors:
        return "anomaly"
    return "normal"
