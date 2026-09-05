# apps/identity/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.authorization.models import UserRoleAssignment


class TenantAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        active_tenants = UserRoleAssignment.objects.filter(
            user=user, is_active=True
        ).values_list("tenant_id", flat=True).distinct()

        if len(active_tenants) == 1:
            token["tenant_id"] = str(active_tenants[0])
        # 0 or 2+ tenants: no claim added, deliberately — JWTTenantResolver
        # finds nothing and falls through to header/host resolvers.
        # Multi-tenant users need a school-picker flow (not built yet).

        return token