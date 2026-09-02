"""
apps/people/models.py

Foundational identity for people a school actually deals with:
students, staff, and the guardians connected to students. Deliberately
institution-agnostic — no grade/class/curriculum fields here. That
belongs to the academics domain.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel


class Student(TenantScopedModel):
    """A person enrolled (or applying) at a school. Not every Student
    has a CustomUser account — many won't, especially younger students
    (see identity model's no-email-required design)."""

    STATUS_CHOICES = [
        ("applicant", "Applicant"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("graduated", "Graduated"),
        ("withdrawn", "Withdrawn"),
    ]

    campus = models.ForeignKey(
        "core.Campus", on_delete=models.PROTECT, related_name="students"
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="student_profile",
        help_text="Only set if this student has their own login."
    )

    admission_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applicant")

    # Legal Data Suppression edge case (flagged earlier, not yet
    # enforced anywhere) — the field exists now since it's cheap to add
    # here; actual enforcement in permission-checking logic is deferred.
    is_privacy_restricted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "admission_number"],
                name="unique_admission_number_per_tenant",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


class Staff(TenantScopedModel):
    """A person employed by the school — teacher, admin, support staff.
    Role/permission (what they can DO) lives in authorization.
    Employment status/type (what they ARE) lives here."""

    EMPLOYMENT_TYPE_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
    ]

    campus = models.ForeignKey(
        "core.Campus", on_delete=models.PROTECT, null=True, blank=True,
        related_name="staff", help_text="Null = tenant-wide staff (e.g. HQ admin)."
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile",
        help_text="Staff always have a login — unlike students."
    )

    staff_number = models.CharField(max_length=50)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default="full_time")
    is_active_employee = models.BooleanField(default=True)
    date_joined = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "staff_number"],
                name="unique_staff_number_per_tenant",
            ),
        ]

    def __str__(self):
        return f"{self.user} — staff #{self.staff_number}"


class GuardianRelationship(TenantScopedModel):
    """Connects a guardian's CustomUser account to one or more Students.
    Solves the 'one parent email, multiple children' case — the parent
    has ONE account, linked to each child via a separate row here."""

    RELATIONSHIP_CHOICES = [
        ("parent", "Parent"),
        ("guardian", "Legal Guardian"),
        ("sponsor", "Sponsor"),
        ("other", "Other"),
    ]

    guardian = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardian_relationships"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="guardian_relationships"
    )
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default="parent")
    is_primary_contact = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["guardian", "student"],
                name="unique_guardian_student_pair",
            ),
        ]

    def __str__(self):
        return f"{self.guardian} → {self.student} ({self.relationship_type})"