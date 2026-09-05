# apps/identity/management/commands/test_login.py
from django.core.management.base import BaseCommand
from rest_framework.test import APIClient


class Command(BaseCommand):
    help = "Log in via /api/token/ against the real dev DB and print the access token."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)

    def handle(self, *args, **options):
        client = APIClient()
        response = client.post("/api/token/", {
            "email": options["email"], "password": options["password"]
        })
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Login failed: {response.data}"))
            return
        self.stdout.write(self.style.SUCCESS(f"ACCESS: {response.data['access']}"))
        self.stdout.write(self.style.SUCCESS(f"REFRESH: {response.data['refresh']}"))


# elonmusk@xai.com   elon@1t

# python manage.py test_login elonmusk@xai.com elon@1t

# $token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg4NjQ2MzgzLCJpYXQiOjE3ODg2NDYwODMsImp0aSI6ImY0YThjZDlmY2U0ZTRiMzZiMDExNWNmMTg2ZjA5OTc4IiwidXNlcl9pZCI6ImNmY2M3OTYwLWM3ZGUtNDM1ZC04ZmYwLWFmNmVmYTM4NTA4OCIsInRlbmFudF9pZCI6IjhlYWQ1NzcwLTlmNGQtNGQxNS1hODZmLTlmNGExOGY2OWNmZSJ9.aIknHGo9CQnyQstPNkJXCQKQVrV1Ji9FocVsHLok_go"

# curl.exe http://127.0.0.1:8000/whoami/ -H "Authorization: Bearer $token"
