# apps/admissions/admin.py
from django.contrib import admin
from apps.core.admin import TenantScopedAdmin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(TenantScopedAdmin):
    list_display = ("applicant_first_name", "applicant_last_name", "tenant", "status", "submitted_at")
    list_filter = ("tenant", "status")