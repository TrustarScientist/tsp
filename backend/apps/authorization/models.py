"""
tsp/backend/apps/authorization/models.py

Role-based permissions, scoped by tenant/campus, with an explicit
override layer for ad-hoc grants/denials. Deny-by-default throughout.
"""
from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class Role(models.Model):
    code = models.SlugField(unique=True)          # 'teacher', 'parent', 'school_admin'
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    code = models.SlugField(unique=True)           # 'view_grades', 'edit_attendance'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("role", "permission")


class UserRoleAssignment(models.Model):
    """A user's role within a specific tenant, optionally scoped further
    to one campus. campus=null means tenant/HQ-wide."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments"
    )
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE)
    campus = models.ForeignKey("core.Campus", on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # e.g. substitute teachers
    history = HistoricalRecords() 
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant", "role"],
                condition=models.Q(campus__isnull=True),
                name="unique_tenant_wide_role_assignment",
            ),
            models.UniqueConstraint(
                fields=["user", "tenant", "campus", "role"],
                condition=models.Q(campus__isnull=False),
                name="unique_campus_scoped_role_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.role.code} @ {self.tenant.name}"


class UserPermissionOverride(models.Model):
    """Ad-hoc grant or deny for one user, independent of their role.
    Explicit denies win over anything a role would otherwise allow
    (e.g. custody restrictions, disciplinary action)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="permission_overrides"
    )
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE)
    campus = models.ForeignKey("core.Campus", on_delete=models.CASCADE, null=True, blank=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    is_granted = models.BooleanField(default=True)   # False = explicit deny
    expires_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)             # audit trail — required for denies
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # new for "hard" auditing
    history = HistoricalRecords() 




    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant", "permission"],
                condition=models.Q(campus__isnull=True),
                name="unique_tenant_wide_permission_override",
            ),
            models.UniqueConstraint(
                fields=["user", "tenant", "campus", "permission"],
                condition=models.Q(campus__isnull=False),
                name="unique_campus_scoped_permission_override",
            ),
        ]

    def __str__(self):
        verdict = "GRANT" if self.is_granted else "DENY"
        return f"{verdict}: {self.user} — {self.permission.code} @ {self.tenant.name}"