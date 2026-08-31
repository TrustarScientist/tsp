"""
tsp/backend/apps/core/middleware.py

Resolves the current Tenant for every request, exactly once, at the
top of the middleware stack — chain of responsibility:
  1. JWT tenant claim (authenticated requests, once tokens carry it)
  2. X-Tenant-ID header (explicit override / pre-tenant-selection)
  3. Host header → custom_domain or subdomain (public pages, DNS CNAME)

If no resolver finds a match, request.tenant is None and the context
var stays unset — any TenantScopedManager query downstream will then
raise TenantContextMissing rather than silently running unfiltered.
Fail closed, always.
"""
from .models import Tenant, set_current_tenant, reset_current_tenant


class TenantResolver:
    def resolve(self, request):
        raise NotImplementedError


class JWTTenantResolver(TenantResolver):
    """Reads a tenant_id claim out of the JWT, if present. Uses
    simplejwt's token parsing directly (not the full DRF auth flow,
    which runs later, at the view level) — just enough to peek at
    the claim before views are reached."""

    def resolve(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        raw_token = auth_header.split(" ", 1)[1]
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(raw_token)
            tenant_id = token.get("tenant_id")
            if tenant_id:
                return Tenant.objects.filter(id=tenant_id, is_active=True).first()
        except Exception:
            # Invalid/expired token — not this resolver's job to reject
            # the request, just don't resolve a tenant from it. DRF's
            # own authentication will reject the token at the view.
            return None
        return None


class HeaderTenantResolver(TenantResolver):
    def resolve(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return None
        return Tenant.objects.filter(id=tenant_id, is_active=True).first()


class HostTenantResolver(TenantResolver):
    """Public pages and the custom-domain premium tier. custom_domain
    is checked before subdomain — a school could theoretically have
    both, and a paid custom domain should win."""

    def resolve(self, request):
        host = request.get_host().split(":")[0]  # strip port for local dev

        tenant = Tenant.objects.filter(custom_domain=host, is_active=True).first()
        if tenant:
            return tenant

        parts = host.split(".")
        if len(parts) >= 2:
            subdomain = parts[0]
            tenant = Tenant.objects.filter(subdomain=subdomain, is_active=True).first()
            if tenant:
                return tenant

        return None


RESOLVER_CHAIN = [
    JWTTenantResolver(),
    HeaderTenantResolver(),
    HostTenantResolver(),
]


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        for resolver in RESOLVER_CHAIN:
            tenant = resolver.resolve(request)
            if tenant is not None:
                break

        request.tenant = tenant
        token = set_current_tenant(tenant)
        try:
            response = self.get_response(request)
        finally:
            # Always reset — critical in threaded/sync workers, where
            # the same thread handles the next request and would
            # otherwise inherit this request's tenant.
            reset_current_tenant(token)
        return response