# apps/core/admin.py
from django.contrib import admin
from .models import Tenant, Campus, SchoolGroup, GroupMembership

from django.contrib import admin
from apps.core.models import Tenant, set_current_tenant, reset_current_tenant
from apps.core.db import tenant_scope, platform_admin_scope
from .models import Tenant as TenantModel, Campus, SchoolGroup, GroupMembership



class TenantScopedAdmin(admin.ModelAdmin):
    """Shared base for any Django Admin class managing a
    TenantScopedModel. Handles: platform-wide list view, dropdown
    population across tenants, and correct tenant context (both
    Django-side and Postgres RLS-side) for add/edit. Inherit this for
    every future tenant-scoped model's admin — no per-model rewriting
    needed. See docs/ADR-001-tenant-isolation.md for the full reasoning."""

    exclude = ("deleted_at", "deleted_by")

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        related_model = db_field.related_model
        if hasattr(related_model, "all_objects"):
            kwargs["queryset"] = related_model.all_objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def changelist_view(self, request, extra_context=None):
        with platform_admin_scope():
            return super().changelist_view(request, extra_context)

    def _changeform_view(self, request, object_id, form_url, extra_context):
        with platform_admin_scope():
            tenant = self._resolve_tenant_for_form(request, object_id)
            token = set_current_tenant(tenant)
            try:
                if tenant is not None:
                    with tenant_scope(tenant):
                        return super()._changeform_view(request, object_id, form_url, extra_context)
                return super()._changeform_view(request, object_id, form_url, extra_context)
            finally:
                reset_current_tenant(token)

    def _resolve_tenant_for_form(self, request, object_id):
        if object_id:
            with platform_admin_scope():
                obj = self.model.all_objects.filter(pk=object_id).first()
            return obj.tenant if obj else None
        if request.method == "POST":
            tenant_id = request.POST.get("tenant")
            if tenant_id:
                return TenantModel.objects.filter(pk=tenant_id).first()
        return None

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    # Important multi-tenant operational columns displayed at a glance
    list_display = ("name", "subdomain", "custom_domain", "currency", "jurisdiction", "is_active")
    search_fields = ("name", "subdomain", "custom_domain", "rc_number")
    list_filter = ("is_active", "jurisdiction", "currency", "entity_type")

@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_main", "created_at")
    search_fields = ("name", "tenant__name")
    list_filter = ("is_main", "tenant")

@admin.register(SchoolGroup)
class SchoolGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__email", "owner__username")

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "tenant", "created_at")
    list_filter = ("group",)
