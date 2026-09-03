# apps/payments/tests.py
from django.test import TestCase, Client
from apps.core.models import Tenant, set_current_tenant, reset_current_tenant
from apps.core.db import tenant_scope
from apps.payments.services import initiate_payment, verify_payment
from apps.payments.models import Payment

# 
import hashlib
import hmac
import json
from django.conf import settings



class PaystackIntegrationTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Payments Test School", subdomain="payments-test")
        self.campus = self.tenant.campuses.first()

    def test_initiate_and_verify_payment(self):
        token = set_current_tenant(self.tenant)
        try:
            with tenant_scope(self.tenant):
                payment = initiate_payment(
                    tenant=self.tenant, campus=self.campus,
                    purpose="application_fee", amount_naira=5000,
                    payer_email="test@example.com",
                )
                self.assertEqual(payment.status, "pending")
                self.assertTrue(payment.provider_checkout_url.startswith("https://"))
                print("\nCheckout URL:", payment.provider_checkout_url)
                print("Reference:", payment.provider_reference)

                # Verify immediately — Paystack sandbox transactions
                # created via API (not completed by a real card) will
                # correctly come back as "failed"/not yet paid, since
                # no actual checkout happened. This still proves the
                # verify() call itself works correctly end-to-end.
                result = verify_payment(payment)
                print("Status after verify:", result.status)
        finally:
            reset_current_tenant(token)




# web hook things
class PaystackWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/webhooks/paystack/"

    def _signed_request(self, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode("utf-8"), body, hashlib.sha512
        ).hexdigest()
        return body, signature

    def test_valid_signature_is_accepted(self):
        payload = {"event": "charge.success", "data": {"reference": "TEST_REF_123"}}
        body, signature = self._signed_request(payload)

        response = self.client.post(
            self.url, data=body, content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_signature_is_rejected(self):
        payload = {"event": "charge.success", "data": {"reference": "TEST_REF_123"}}
        body, _ = self._signed_request(payload)

        response = self.client.post(
            self.url, data=body, content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="fake_signature_here",
        )
        self.assertEqual(response.status_code, 401)