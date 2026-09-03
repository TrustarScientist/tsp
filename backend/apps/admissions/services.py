"""
apps/admissions/services.py

submit_application: anyone, unauthenticated — trust-free public step.
confirm_application: staff only — creates the Student row, the trust
boundary between raw public input and core people data.
"""
from django.db import transaction
from apps.people.models import Student
from .models import Application


def submit_application(tenant, campus, first_name, last_name, applicant_email,
                        applicant_phone="", date_of_birth=None, submitted_by=None):
    return Application.objects.create(
        tenant=tenant, campus=campus,
        applicant_first_name=first_name, applicant_last_name=last_name,
        applicant_date_of_birth=date_of_birth,
        applicant_email=applicant_email, applicant_phone=applicant_phone,
        submitted_by=submitted_by,
    )


def confirm_application(application, reviewed_by, admission_number=None):
    with transaction.atomic():
        student = Student.objects.create(
            tenant=application.tenant, campus=application.campus,
            first_name=application.applicant_first_name,
            last_name=application.applicant_last_name,
            date_of_birth=application.applicant_date_of_birth,
            admission_number=admission_number or f"APP-{Student.objects.count() + 1:05d}",
            status="applicant",
        )
        application.student = student
        application.status = "under_review"
        application.reviewed_by = reviewed_by
        application.save()
    return application