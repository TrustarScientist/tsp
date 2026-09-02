# apps/people/tests.py
from django.test import TestCase
from apps.core.models import Tenant, set_current_tenant, reset_current_tenant
from apps.core.models import TenantContextMissing
from apps.people.models import Student


class StudentTenantScopingTests(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="School A", subdomain="school-a-test")
        self.tenant_b = Tenant.objects.create(name="School B", subdomain="school-b-test")
        self.campus_a = self.tenant_a.campuses.first()
        self.campus_b = self.tenant_b.campuses.first()

    def test_query_without_tenant_context_fails_closed(self):
        with self.assertRaises(TenantContextMissing):
            list(Student.objects.all())

    def test_scoped_manager_only_returns_current_tenant(self):
        token_a = set_current_tenant(self.tenant_a)
        Student.objects.create(
            tenant=self.tenant_a, campus=self.campus_a,
            admission_number="A001", first_name="Ada", last_name="Lovelace",
        )
        reset_current_tenant(token_a)

        token_b = set_current_tenant(self.tenant_b)
        Student.objects.create(
            tenant=self.tenant_b, campus=self.campus_b,
            admission_number="B001", first_name="Grace", last_name="Hopper",
        )

        # Still scoped to tenant_b — should see only Grace, not Ada
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Student.objects.first().first_name, "Grace")
        reset_current_tenant(token_b)

    def test_admission_number_unique_per_tenant_not_globally(self):
        token_a = set_current_tenant(self.tenant_a)
        Student.objects.create(
            tenant=self.tenant_a, campus=self.campus_a,
            admission_number="0001", first_name="Ada", last_name="Lovelace",
        )
        reset_current_tenant(token_a)

        token_b = set_current_tenant(self.tenant_b)
        # Same admission_number "0001" at a DIFFERENT tenant should be fine
        Student.objects.create(
            tenant=self.tenant_b, campus=self.campus_b,
            admission_number="0001", first_name="Grace", last_name="Hopper",
        )
        reset_current_tenant(token_b)
        # If this doesn't raise, the constraint is correctly scoped