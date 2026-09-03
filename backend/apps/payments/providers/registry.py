# apps/payments/providers/registry.py
from .paystack import PaystackProvider
from .manual import ManualProvider

PROVIDERS = {
    "paystack": PaystackProvider(),
    "manual": ManualProvider(),
}

def get_provider(name: str):
    return PROVIDERS[name]