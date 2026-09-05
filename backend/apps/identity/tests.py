# apps/identity/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from apps.core.models import Tenant
from apps.authorization.models import Role, UserRoleAssignment
from apps.identity.models import CustomUser


class TenantAwareLoginTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Login Test School", subdomain="login-test")
        self.user = CustomUser.objects.create_user(email="teacher@example.com", password="testpass123")
        role = Role.objects.create(code="teacher", name="Teacher")
        UserRoleAssignment.objects.create(user=self.user, tenant=self.tenant, role=role)

    def test_login_embeds_tenant_id_in_token(self):
        client = APIClient()
        response = client.post("/api/token/", {"email": "teacher@example.com", "password": "testpass123"})
        self.assertEqual(response.status_code, 200)
        print("\nACCESS TOKEN:", response.data["access"])
        self.assertIn("access", response.data)

        from rest_framework_simplejwt.tokens import AccessToken
        decoded = AccessToken(response.data["access"])
        self.assertEqual(decoded["tenant_id"], str(self.tenant.id))


        