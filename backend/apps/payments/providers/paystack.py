# apps/payments/providers/paystack.py
import requests
from django.conf import settings
from .base import PaymentProvider


class PaystackProvider(PaymentProvider):
    BASE_URL = "https://api.paystack.co"

    def initiate(self, amount_kobo: int, email: str) -> dict:
        response = requests.post(
            f"{self.BASE_URL}/transaction/initialize",
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            json={"email": email, "amount": amount_kobo},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return {"reference": data["reference"], "checkout_url": data["authorization_url"]}

    def verify(self, reference: str) -> dict:
        response = requests.get(
            f"{self.BASE_URL}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return {"status": "success" if data["status"] == "success" else "failed", "raw": data}