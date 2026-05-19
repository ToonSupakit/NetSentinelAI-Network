from app.vendor_adapters import VendorAdapter, remediation_commands, register_adapter


class AcmeAdapter(VendorAdapter):
    name = "acme"

    def commands(self, intf, action, limit_mbps=None):
        if action == "fix":
            return [f"repair port {intf}"]
        return None


def test_vendor_adapter_plugin_registration():
    register_adapter("acme_os", AcmeAdapter())
    assert remediation_commands("acme_os_ssh", "eth0", "fix") == ["repair port eth0"]


def test_cisco_fix_and_rate_limit_commands():
    assert remediation_commands("cisco_ios", "Gi0/1", "fix") == [
        "interface Gi0/1",
        "shutdown",
        "no shutdown",
    ]

    limit = remediation_commands("cisco_ios", "Gi0/1", "limit", 50)
    remove = remediation_commands("cisco_ios", "Gi0/1", "removelimit", 50)

    assert limit == [
        "interface Gi0/1",
        "rate-limit input 50000000 50000 50000 conform-action transmit exceed-action drop",
        "rate-limit output 50000000 50000 50000 conform-action transmit exceed-action drop",
    ]
    assert remove == [
        "interface Gi0/1",
        "no rate-limit input 50000000 50000 50000 conform-action transmit exceed-action drop",
        "no rate-limit output 50000000 50000 50000 conform-action transmit exceed-action drop",
    ]


def test_mikrotik_and_juniper_commands():
    assert remediation_commands("mikrotik_routeros", "ether1", "fix") == [
        "/interface disable [find name=ether1]",
        "/interface enable [find name=ether1]",
    ]
    assert remediation_commands("mikrotik_routeros", "ether1", "removelimit") == [
        "/queue simple remove [find name=limit_ether1]"
    ]
    assert remediation_commands("juniper_junos", "ge-0/0/1", "fix") == [
        "delete interfaces ge-0/0/1 disable",
        "commit",
    ]


def test_unknown_vendor_has_no_commands():
    assert remediation_commands("unknown_os", "eth0", "fix") is None
