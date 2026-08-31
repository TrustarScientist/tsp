# tsp/backend/apps/identity/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from .models import CustomUser


class EUPBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        identifier = username  # could be a username, email, or phone — caller doesn't know which

        try:
            if "@" in identifier:
                user = CustomUser.objects.get(email=identifier)
            elif identifier.replace("+", "").isdigit():
                user = CustomUser.objects.get(phone=identifier)
            else:
                user = CustomUser.objects.get(username=identifier)
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password) and user.is_active:
            return user
        return None


    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None





        