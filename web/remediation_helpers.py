"""Validation helpers for remediation API payloads."""


def parse_rate_limit_payload(data):
    limit_mbps = data.get("limit_mbps", 50)
    rollback_min = data.get("rollback_min", 0)

    try:
        limit_mbps = float(limit_mbps)
    except (ValueError, TypeError):
        return False, None, None, "Invalid limit value", "invalid_limit"
    if limit_mbps <= 0 or limit_mbps > 10000:
        return False, None, None, "Limit must be between 1-10000 Mbps", "limit_out_of_range"

    try:
        rollback_min = int(rollback_min or 0)
    except (ValueError, TypeError):
        return False, None, None, "Invalid rollback value", "invalid_rollback"
    if rollback_min < 0 or rollback_min > 10080:
        return False, None, None, "Rollback must be between 0 and 10080 minutes", "invalid_rollback"

    return True, limit_mbps, rollback_min, None, None
