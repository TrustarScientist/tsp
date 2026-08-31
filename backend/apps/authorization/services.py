"""
apps/authorization/services.py

Permission resolution: explicit overrides first, then role permissions.
Deny-by-default — no match anywhere means False, always.
"""
from django.utils import timezone

from .models import UserPermissionOverride, UserRoleAssignment


def user_can(user, permission_code, tenant, campus=None):
    now = timezone.now()

    override = (
        UserPermissionOverride.objects.filter(
            user=user, tenant=tenant, campus=campus, permission__code=permission_code
        )
        .exclude(expires_at__lt=now)
        .first()
    )
    if override is not None:
        return override.is_granted

    return (
        UserRoleAssignment.objects.filter(
            user=user,
            tenant=tenant,
            campus=campus,
            is_active=True,
            role__permissions__permission__code=permission_code,
        )
        .exclude(expires_at__lt=now)
        .exists()
    )