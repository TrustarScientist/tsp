from django.contrib import admin
from .models import Tenant, Campus, SchoolGroup, GroupMembership

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
