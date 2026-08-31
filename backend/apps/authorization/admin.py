from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRoleAssignment, UserPermissionOverride

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "description")
    search_fields = ("name", "code")

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "description")
    search_fields = ("code",)

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")
    list_filter = ("role",)

@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "campus", "role", "is_active", "expires_at")
    list_filter = ("is_active", "tenant", "role")
    search_fields = ("user__email", "user__username")

@admin.register(UserPermissionOverride)
class UserPermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "campus", "permission", "is_granted", "expires_at")
    list_filter = ("is_granted", "tenant")
    search_fields = ("user__email", "user__username", "reason")
