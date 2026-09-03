from django.test import TestCase
from apps.core.models import Tenant, set_current_tenant, reset_current_tenant
from apps.core.db import tenant_scope
from apps.identity.models import CustomUser
from apps.admissions.services import submit_application, confirm_application


class AdmissionFlowTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test School", subdomain="admissions-test")
        self.campus = self.tenant.campuses.first()
        self.staff_user = CustomUser.objects.create_user(
            email="staff@example.com", password="testpass123"
        )

    def test_submit_then_confirm_creates_student(self):
        token = set_current_tenant(self.tenant)
        try:
            with tenant_scope(self.tenant):
                application = submit_application(
                    tenant=self.tenant, campus=self.campus,
                    first_name="Test", last_name="Applicant",
                    applicant_email="test@example.com",
                )
                self.assertEqual(application.status, "submitted")
                self.assertIsNone(application.student)

                confirm_application(application, reviewed_by=self.staff_user)
                self.assertEqual(application.status, "under_review")
                self.assertIsNotNone(application.student)
                self.assertEqual(application.student.first_name, "Test")
                self.assertEqual(application.student.status, "applicant")
        finally:
            reset_current_tenant(token)