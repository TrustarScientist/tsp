"""
apps/admissions/models.py

Public-facing admissions flow. Anyone can submit an application, no
login required — raw applicant data is captured on Application only.
A Student row is created ONLY when staff confirms the application is
real (confirm_application in services.py) — that confirmation is the
trust boundary between anonymous public input and the platform's
core people data.
"""
from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TenantScopedModel


class Application(TenantScopedModel):
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("interview_scheduled", "Interview Scheduled"),
        ("offered", "Offer Extended"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    campus = models.ForeignKey("core.Campus", on_delete=models.PROTECT, related_name="applications")
    student = models.OneToOneField(
        "people.Student", on_delete=models.CASCADE, related_name="application",
        null=True, blank=True,
    )

    applicant_first_name = models.CharField(max_length=150)
    applicant_last_name = models.CharField(max_length=150)
    applicant_date_of_birth = models.DateField(null=True, blank=True)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=20, blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="submitted")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    notes = models.TextField(blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"Application: {self.applicant_first_name} {self.applicant_last_name} ({self.status})"