"""
apps/payments/providers/base.py

Every payment provider adapter implements this interface. Swapping or
adding a provider means writing a new adapter class here, never
touching Payment models, admin, or the calling code in services.py.
"""
from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    @abstractmethod
    def initiate(self, amount_kobo: int, email: str) -> dict:
        """Returns {"reference": str, "checkout_url": str}"""
        ...

    @abstractmethod
    def verify(self, reference: str) -> dict:
        """Returns {"status": "success"|"failed", "raw": dict}"""
        ...