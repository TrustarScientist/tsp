# apps/core/signals.py — new file
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Tenant, Campus

@receiver(post_save, sender=Tenant)
def create_main_campus(sender, instance, created, **kwargs):
    if created:
        Campus.objects.create(tenant=instance, name="Main Campus", is_main=True)