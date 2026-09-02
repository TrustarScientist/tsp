from contextlib import contextmanager
from django.db import connection, transaction
from .models import set_bypass_tenant_scope, reset_bypass_tenant_scope


@contextmanager
def tenant_scope(tenant):
    with transaction.atomic():
        with connection.cursor() as cursor:
            tenant_id = str(tenant.id) if tenant is not None else ""
            cursor.execute("SET LOCAL app.current_tenant_id = %s", [tenant_id])
            cursor.execute("SET LOCAL app.bypass_tenant_scope = %s", ["false"])
        yield


@contextmanager
def platform_admin_scope():
    """Explicit RLS + application-layer bypass — for trusted
    platform-operator views only (Django Admin). Never used for
    ordinary application code or real user-facing requests."""
    token = set_bypass_tenant_scope(True)
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.bypass_tenant_scope = %s", ["true"])
            yield
    finally:
        reset_bypass_tenant_scope(token)