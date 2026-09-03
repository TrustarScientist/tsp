# apps/payments/providers/manual.py
"""
Manual payment provider — for schools accepting bank transfer, cash,
or other offline payment. No real API call; a staff member marks the
payment successful directly, typically after confirming a bank alert.
"""
import uuid
from .base import PaymentProvider


class ManualProvider(PaymentProvider):
    def initiate(self, amount_kobo: int, email: str) -> dict:
        # No external checkout — generate our own reference, no URL.
        return {"reference": f"MANUAL-{uuid.uuid4().hex[:12].upper()}", "checkout_url": ""}

    def verify(self, reference: str) -> dict:
        # Manual verification isn't automatic — this should never be
        # called by the normal flow. Staff mark it successful directly
        # via admin/services.mark_manual_payment_successful() instead.
        raise NotImplementedError(
            "Manual payments are confirmed by staff action, not automated verification."
        )