"""SNMP parsing and collector integration using mock devices."""

import app.collector as collector
import app.snmp_helper as snmp


def test_get_snmp_interfaces_from_mock_walk(monkeypatch):
    snmp._OCTET_CACHE.clear()

    async def fake_walk(_host, _community, oid):
        if oid == snmp.DEFAULT_OIDS["ifDescr"]:
            return {
                "1": "GigabitEthernet0/0",
                "2": "GigabitEthernet0/1",
                "3": "Loopback0",
                "4": "Null0",
            }
        if oid == snmp.DEFAULT_OIDS["ifOperStatus"]:
            return {"1": 1, "2": 2, "3": 1, "4": 1}
        if oid == snmp.DEFAULT_OIDS["ifAdminStatus"]:
            return {"1": 1, "2": 2, "3": 1, "4": 1}
        if oid == snmp.DEFAULT_OIDS["locIfInLoad"]:
            return {"1": 999, "2": 7}
        if oid == snmp.DEFAULT_OIDS["locIfOutLoad"]:
            return {"1": 999, "2": 8}
        if oid == snmp.DEFAULT_OIDS["locIfReliability"]:
            return {"1": 0, "2": 150}
        if oid == snmp.DEFAULT_OIDS["ifInErrors"]:
            return {"1": 3, "2": 4}
        if oid == snmp.DEFAULT_OIDS["ifInOctets"]:
            return {"1": 1000}
        if oid == snmp.DEFAULT_OIDS["ifOutOctets"]:
            return {"1": 2000}
        if oid == snmp.DEFAULT_OIDS["ifSpeed"]:
            return {"1": 1_000_000_000}
        if oid == snmp.DEFAULT_OIDS["ifHighSpeed"]:
            return {}
        return {}

    async def fake_ip_map(_host, _community):
        return {"1": "10.0.0.1", "2": "10.0.0.2"}

    monkeypatch.setattr(snmp, "snmp_walk_async", fake_walk)
    monkeypatch.setattr(snmp, "snmp_walk_ip_map", fake_ip_map)

    interfaces = snmp.get_snmp_interfaces("router1", "public")

    assert [i["intf"] for i in interfaces] == ["GigabitEthernet0/0", "GigabitEthernet0/1"]
    assert interfaces[0]["status"] == "up"
    assert interfaces[0]["reliability"] == 255
    assert interfaces[0]["rxload"] == 1
    assert interfaces[0]["network_load"] == 1
    assert interfaces[1]["status"] == "admin_down"
    assert interfaces[1]["is_admin_down"] is True


def test_collect_device_uses_snmp_rows_and_saves_all_marker(monkeypatch):
    saved = []
    monkeypatch.setattr(
        collector,
        "get_snmp_interfaces",
        lambda *_args, **_kwargs: [
            {
                "intf": "GigabitEthernet0/0",
                "ip": "10.0.0.1",
                "status": "up",
                "protocol": "up",
                "reliability": 255,
                "network_load": 1,
                "rxload": 1,
                "input_errors": 0,
                "is_admin_down": False,
            },
            {
                "intf": "GigabitEthernet0/1",
                "ip": "unassigned",
                "status": "up",
                "protocol": "up",
                "reliability": 255,
                "network_load": 1,
                "rxload": 1,
                "input_errors": 0,
                "is_admin_down": False,
            },
        ],
    )

    def fake_save_log(*args):
        saved.append(args)
        return len(saved)

    monkeypatch.setattr(collector, "save_log", fake_save_log)

    result = collector.collect_device(
        {"name": "R1", "host": "10.0.0.1", "device_type": "cisco_ios", "zone": "A", "location": "Lab"}
    )

    assert len(result) == 1
    assert result[0]["intf"] == "GigabitEthernet0/0"
    assert [row[1] for row in saved] == ["GigabitEthernet0/0", "ALL"]
