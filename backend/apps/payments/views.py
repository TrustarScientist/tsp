# apps/payments/views.py
"""
Paystack webhook receiver. Verifies the request signature (critical —
without this, anyone could POST fake "payment successful" events),
logs the raw event, then processes it if it's one we care about.
"""
import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.db import platform_admin_scope
from .models import Payment, PaymentProviderEvent


@csrf_exempt
@require_POST
def paystack_webhook(request):
    signature = request.headers.get("x-paystack-signature", "")
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        request.body,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return HttpResponse(status=401)  # not really from Paystack — reject

    payload = json.loads(request.body)
    event_type = payload.get("event", "")
    reference = payload.get("data", {}).get("reference", "")

    with platform_admin_scope():
        payment = Payment.all_objects.filter(provider="paystack", provider_reference=reference).first()
        tenant = payment.tenant if payment else None

        PaymentProviderEvent.objects.create(
            tenant=tenant, provider="paystack", event_type=event_type,
            provider_reference=reference, raw_payload=payload, processed=False,
        )

        if payment and event_type == "charge.success":
            from django.utils import timezone
            payment.status = "successful"
            payment.verified_at = timezone.now()
            payment.save()

    return HttpResponse(status=200)