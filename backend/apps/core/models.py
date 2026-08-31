"""
tsp/backend/apps/core/models.py

Foundation layer. Nothing here is domain-specific (no students, no
grades) — this is the plumbing every other app in this project builds on.
"""
import uuid
import contextvars
from django.conf import settings
from django.db import models


# ---------------------------------------------------------------------
# Timestamps on every model, no exceptions. Soft delete as the default.
# ---------------------------------------------------------------------

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Default manager: soft-deleted rows are invisible unless explicitly
    asked for."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(TimestampedModel):
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="+", on_delete=models.SET_NULL
    )

    objects = SoftDeleteManager()   # default: excludes soft-deleted rows
    all_objects = models.Manager()  # explicit access for support/audit/restore

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self, by_user=None):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.deleted_by = by_user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])


# ---------------------------------------------------------------------
# Tenant. One tenant = one operationally independent school.
# A location only becomes its own Tenant if it has its own students,
# staff, and calendar. Otherwise it's just data on an existing Tenant
# — see Campus below for that case.
# ---------------------------------------------------------------------

class Tenant(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    # Public identity / routing — subdomain always exists; custom_domain
    # is the premium tier (DNS CNAME pointed at this platform).
    subdomain = models.SlugField(unique=True)
    custom_domain = models.CharField(max_length=255, blank=True, null=True, unique=True)
    theme_slug = models.CharField(max_length=100, default="default")

    # Legal entity fields, relevant once governance/board structure matters
    entity_type = models.CharField(
        max_length=30,
        choices=[
            ("sole_proprietorship", "Sole Proprietorship"),
            ("partnership", "Partnership"),
            ("limited_liability", "Limited Liability Company"),
        ],
        default="sole_proprietorship",
    )
    legal_name = models.CharField(max_length=255, blank=True)
    rc_number = models.CharField("CAC Registration Number", max_length=50, blank=True)
    registered_address = models.TextField(blank=True)

    # Never assume Nigeria — supports future multi-country expansion
    currency = models.CharField(max_length=3, default="NGN")
    locale = models.CharField(max_length=10, default="en-NG")
    jurisdiction = models.CharField(
        max_length=10,
        default="NG",
        help_text="ISO country code. Drives which compliance-rules table applies.",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------
# Campus: a scoping dimension INSIDE a Tenant, not a separate tenant.
# Every Tenant gets at least one Campus (the "Main Campus").
# ---------------------------------------------------------------------

class Campus(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="campuses")
    name = models.CharField(max_length=255)
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ["tenant", "name"]

    def __str__(self):
        return f"{self.tenant.name} — {self.name}"


# ---------------------------------------------------------------------
# SchoolGroup: the Organization layer above Tenant, for proprietors
# running more than one operationally-independent school.
# ---------------------------------------------------------------------

class SchoolGroup(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_groups"
    )

    def __str__(self):
        return self.name


class GroupMembership(TimestampedModel):
    group = models.ForeignKey(SchoolGroup, on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="group_memberships")

    class Meta:
        unique_together = ("group", "tenant")


# ---------------------------------------------------------------------
# TenantScopedManager. Application-level half of dual enforcement
# (database-level half is Postgres RLS — separate, added later).
# ---------------------------------------------------------------------

class TenantContextMissing(Exception):
    """Raised when tenant-scoped code runs without a tenant set — fail
    closed, never silently unfiltered."""


_current_tenant: contextvars.ContextVar = contextvars.ContextVar("current_tenant", default=None)

def get_current_tenant():
    return _current_tenant.get()

def set_current_tenant(tenant):
    return _current_tenant.set(tenant)   # returns a Token

def reset_current_tenant(token):
    _current_tenant.reset(token)         # restores prior value exactly





class TenantScopedManager(models.Manager):
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant is None:
            raise TenantContextMissing(
                "No tenant in context. Every tenant-scoped query must run "
                "inside a request (via TenantMiddleware) or an explicit "
                "tenant context."
            )
        return super().get_queryset().filter(tenant=tenant, deleted_at__isnull=True)


class TenantScopedModel(SoftDeleteModel):
    """Base class for every domain model that belongs to exactly one
    school. Inherit from this, not from models.Model directly, for
    anything student/staff/school-data related."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="+")

    objects = TenantScopedManager()  # tenant-filtered AND soft-delete-filtered
    all_objects = models.Manager()   # explicit escape hatch (e.g. break-glass support)

    class Meta:
        abstract = True