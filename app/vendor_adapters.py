"""Vendor-specific remediation command adapters."""

from __future__ import annotations


class VendorAdapter:
    name = "generic"

    def commands(self, intf, action, limit_mbps=None):
        return None


class CiscoAdapter(VendorAdapter):
    name = "cisco"

    def commands(self, intf, action, limit_mbps=None):
        if action == "fix":
            return [f"interface {intf}", "shutdown", "no shutdown"]
        if action == "limit" and limit_mbps:
            bps = int(float(limit_mbps) * 1_000_000)
            burst = max(8000, int(bps / 1000))
            return [
                f"interface {intf}",
                f"rate-limit input {bps} {burst} {burst} conform-action transmit exceed-action drop",
                f"rate-limit output {bps} {burst} {burst} conform-action transmit exceed-action drop",
            ]
        if action == "removelimit" and limit_mbps:
            bps = int(float(limit_mbps) * 1_000_000)
            burst = max(8000, int(bps / 1000))
            return [
                f"interface {intf}",
                f"no rate-limit input {bps} {burst} {burst} conform-action transmit exceed-action drop",
                f"no rate-limit output {bps} {burst} {burst} conform-action transmit exceed-action drop",
            ]
        return None


class MikrotikAdapter(VendorAdapter):
    name = "mikrotik"

    def commands(self, intf, action, limit_mbps=None):
        if action == "fix":
            return [f"/interface disable [find name={intf}]", f"/interface enable [find name={intf}]"]
        if action == "limit" and limit_mbps:
            limit = int(float(limit_mbps))
            return [f"/queue simple add name=limit_{intf} target={intf} max-limit={limit}M/{limit}M"]
        if action == "removelimit":
            return [f"/queue simple remove [find name=limit_{intf}]"]
        return None


class JuniperAdapter(VendorAdapter):
    name = "juniper"

    def commands(self, intf, action, limit_mbps=None):
        if action == "fix":
            return [f"delete interfaces {intf} disable", "commit"]
        return None


class AristaAdapter(CiscoAdapter):
    name = "arista"


_ADAPTERS = [
    ("mikrotik", MikrotikAdapter()),
    ("juniper", JuniperAdapter()),
    ("arista", AristaAdapter()),
    ("cisco", CiscoAdapter()),
]


def register_adapter(marker, adapter):
    """Register a vendor adapter at runtime for local plugins/extensions."""
    if not marker or not isinstance(adapter, VendorAdapter):
        raise ValueError("marker and VendorAdapter instance are required")
    _ADAPTERS.insert(0, (str(marker).lower(), adapter))


def get_adapter(device_type):
    device_type = (device_type or "").lower()
    for marker, adapter in _ADAPTERS:
        if marker in device_type:
            return adapter
    return VendorAdapter()


def remediation_commands(device_type, intf, action, limit_mbps=None):
    return get_adapter(device_type).commands(intf, action, limit_mbps=limit_mbps)


def supported_vendors():
    return [adapter.name for _, adapter in _ADAPTERS] + ["generic"]
