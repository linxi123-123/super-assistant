from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from server.services.user_tenant_service import build_user_tenant_context


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        user_id = request.headers.get("X-User-Id") or request.query_params.get("user_id")
        request.state.tenant_context = build_user_tenant_context(user_id)
        return await call_next(request)
