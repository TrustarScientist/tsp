# apps/people/admin.py
from django.contrib import admin
from apps.core.admin import TenantScopedAdmin
from .models import Student, Staff, GuardianRelationship


@admin.register(Student)
class StudentAdmin(TenantScopedAdmin):
    list_display = ("admission_number", "first_name", "last_name", "tenant", "status")
    list_filter = ("tenant", "status")


@admin.register(Staff)
class StaffAdmin(TenantScopedAdmin):
    list_display = ("staff_number", "user", "tenant", "is_active_employee")
    list_filter = ("tenant", "is_active_employee")


@admin.register(GuardianRelationship)
class GuardianRelationshipAdmin(TenantScopedAdmin):
    list_display = ("guardian", "student", "relationship_type", "is_primary_contact")