# apps/identity/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import TenantAwareTokenObtainPairSerializer


class TenantAwareTokenObtainPairView(TokenObtainPairView):
    serializer_class = TenantAwareTokenObtainPairSerializer