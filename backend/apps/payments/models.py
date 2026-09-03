"""
apps/payments/models.py

Payment records are provider-agnostic — the model doesn't assume
Paystack specifically. Provider-specific details live in a separate,
swappable adapter layer (services.py), so adding a second provider
later means adding a new adapter, not touching this model.
"""
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TenantScopedModel


class Payment(TenantScopedModel):
    PURPOSE_CHOICES = [
        ("application_fee", "Application Fee"),
        ("tuition", "Tuition"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]
    PROVIDER_CHOICES = [
        ("paystack", "Paystack"),
        ("flutterwave", "Flutterwave"),
        ("manual", "Manual / Bank Transfer"),
    ]

    campus = models.ForeignKey("core.Campus", on_delete=models.PROTECT, related_name="payments")
    application = models.ForeignKey(
        "admissions.Application", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )

    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    amount_kobo = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")

    payer_email = models.EmailField()
    payer_phone = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Provider-agnostic fields — every provider has SOME reference and
    # SOME way to check status, even if the underlying API differs.
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="paystack")
    provider_reference = models.CharField(max_length=100, unique=True)
    provider_checkout_url = models.URLField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.tenant.name} — {self.purpose} — {self.status} — {self.provider_reference}"


# make tenancy nullable here
class PaymentProviderEvent(TenantScopedModel):
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="+",
        null=True, blank=True,  # ← overriding TenantScopedModel's default
        help_text="Null if the webhook reference didn't match any known Payment."
    )
    provider = models.CharField(max_length=20)
    event_type = models.CharField(max_length=100)
    provider_reference = models.CharField(max_length=100)
    raw_payload = models.JSONField()
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} — {self.event_type} — {self.provider_reference}"