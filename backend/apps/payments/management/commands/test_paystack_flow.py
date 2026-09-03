# apps/payments/management/commands/test_paystack_flow.py
from django.core.management.base import BaseCommand
from apps.core.models import Tenant, set_current_tenant, reset_current_tenant
from apps.core.db import tenant_scope
from apps.payments.services import initiate_payment, verify_payment
from apps.payments.models import Payment


class Command(BaseCommand):
    help = "Manually test the Paystack initiate/verify flow against real dev DB."

    def add_arguments(self, parser):
        parser.add_argument("--verify", type=str, help="Reference to verify instead of initiating a new one.")

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(name="Manual Payment Test", subdomain="manual-payment-test")
        token = set_current_tenant(tenant)
        try:
            with tenant_scope(tenant):
                if options["verify"]:
                    payment = Payment.objects.get(provider_reference=options["verify"])
                    result = verify_payment(payment)
                    self.stdout.write(self.style.SUCCESS(f"Status: {result.status}"))
                else:
                    payment = initiate_payment(
                        tenant=tenant, campus=tenant.campuses.first(),
                        purpose="application_fee", amount_naira=5000,
                        payer_email="test@example.com",
                    )
                    self.stdout.write(self.style.SUCCESS(f"Checkout URL: {payment.provider_checkout_url}"))
                    self.stdout.write(self.style.SUCCESS(f"Reference: {payment.provider_reference}"))
        finally:
            reset_current_tenant(token)