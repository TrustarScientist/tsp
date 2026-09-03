# apps/payments/admin.py
from django.contrib import admin
from apps.core.admin import TenantScopedAdmin
from .models import Payment, PaymentProviderEvent
from .services import mark_manual_payment_successful


@admin.register(Payment)
class PaymentAdmin(TenantScopedAdmin):
    list_display = ("provider_reference", "tenant", "provider", "purpose", "status", "amount_kobo")
    list_filter = ("tenant", "provider", "purpose", "status")
    actions = ["confirm_manual_payments"]

    @admin.action(description="Confirm selected manual payments as successful")
    def confirm_manual_payments(self, request, queryset):
        manual_pending = queryset.filter(provider="manual", status="pending")
        count = 0
        for payment in manual_pending:
            mark_manual_payment_successful(payment, confirmed_by=request.user)
            count += 1
        self.message_user(request, f"{count} manual payment(s) confirmed successful.")


@admin.register(PaymentProviderEvent)
class PaymentProviderEventAdmin(TenantScopedAdmin):
    list_display = ("provider", "event_type", "provider_reference", "processed", "received_at")
    list_filter = ("tenant", "provider", "processed", "event_type")