# apps/core/tests.py
from django.test import TestCase
from apps.core.models import Tenant
from .models import Tenant, Campus, TenantContextMissing, set_current_tenant, reset_current_tenant, get_current_tenant


class TenantScopingTests(TestCase):
    def test_tenant_creates_main_campus_automatically(self):
        tenant = Tenant.objects.create(name="Test School", subdomain="test-school")
        self.assertTrue(tenant.campuses.filter(is_main=True).exists())

    def test_tenant_scoped_query_fails_without_context(self):
        # write once TenantScopedModel has a real concrete subclass to test against —
        # flag as pending until the People app gives us one
        pass

class TenantSignalTests(TestCase):
    def test_tenant_creates_main_campus_automatically(self):
        tenant = Tenant.objects.create(name="Test School", subdomain="test-school")
        self.assertTrue(tenant.campuses.filter(is_main=True).exists())
        self.assertEqual(tenant.campuses.count(), 1)