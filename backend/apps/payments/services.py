"""
apps/payments/services.py

Calls the correct provider adapter based on Payment.provider — this
function never changes when a new provider is added.
"""
from django.utils import timezone
from .models import Payment
from .providers.registry import get_provider


def initiate_payment(tenant, campus, purpose, amount_naira, payer_email,
                     payer_phone="", application=None, provider_name="paystack"):
    amount_kobo = int(amount_naira * 100)
    provider = get_provider(provider_name)
    result = provider.initiate(amount_kobo=amount_kobo, email=payer_email)

    return Payment.objects.create(
        tenant=tenant, campus=campus, application=application,
        purpose=purpose, amount_kobo=amount_kobo,
        payer_email=payer_email, payer_phone=payer_phone,
        provider=provider_name,
        provider_reference=result["reference"],
        provider_checkout_url=result["checkout_url"],
    )


def verify_payment(payment: Payment):
    provider = get_provider(payment.provider)
    result = provider.verify(payment.provider_reference)

    payment.status = "successful" if result["status"] == "success" else "failed"
    if payment.status == "successful":
        payment.verified_at = timezone.now()
    payment.save()
    return payment




# manual payments are confirmed by staff action, not automated verification.
def mark_manual_payment_successful(payment, confirmed_by):
    """Staff-only action: confirms a manual (bank transfer/cash)
    payment after checking it arrived — no external API call."""
    from django.utils import timezone
    payment.status = "successful"
    payment.verified_at = timezone.now()
    payment.save()
    return payment


def initiate_manual_payment(tenant, campus, purpose, amount_naira, payer_email,
                            payer_phone="", application=None):
    """For staff creating a manual payment record on a family's behalf
    — e.g. logging that a bank transfer was received."""
    from .models import Payment
    from .providers.registry import get_provider

    amount_kobo = int(amount_naira * 100)
    provider = get_provider("manual")
    result = provider.initiate(amount_kobo=amount_kobo, email=payer_email)

    return Payment.objects.create(
        tenant=tenant, campus=campus, application=application,
        purpose=purpose, amount_kobo=amount_kobo,
        payer_email=payer_email, payer_phone=payer_phone,
        provider="manual",
        provider_reference=result["reference"],
        provider_checkout_url="",
    )


