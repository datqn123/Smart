"""OQ-01 template allowlist mirrored in MCP; enforced again in-agent."""

ALLOWED_TEMPLATE_PARAMS: dict[str, frozenset[str]] = {
    "sales_by_day_v1": frozenset({"days"}),
}


def validate_template_params(template_id: str, keys: frozenset[str]) -> tuple[bool, str]:
    allowed = ALLOWED_TEMPLATE_PARAMS.get(template_id)
    if allowed is None:
        return False, "UNKNOWN_TEMPLATE"
    if keys != allowed:
        return False, "DB_QUERY_REJECTED"
    return True, ""
