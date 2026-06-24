from __future__ import annotations


def ensure_same_scope(resource: dict, context: dict, resource_name: str = "resource") -> None:
    user_id = context.get("user_id")
    tenant_id = context.get("tenant_id")
    if resource.get("user_id") not in {None, "", user_id}:
        raise ValueError(f"{resource_name}_cross_user_rejected")
    if resource.get("tenant_id") not in {None, "", tenant_id}:
        raise ValueError(f"{resource_name}_cross_tenant_rejected")


def scoped_where_clause(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return f"{prefix}user_id = ? AND {prefix}tenant_id = ?"
