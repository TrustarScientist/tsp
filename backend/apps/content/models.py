"""
apps/content/models.py

Front Door public page content, modeled as pages composed of ordered,
typed sections — matching the frontend's shared section contract
design (HeroProps, GalleryProps, etc. as TS interfaces). A theme
renders each section by section_type; content is theme-agnostic data,
never presentation.
"""
from django.db import models
from apps.core.models import TenantScopedModel


class Page(TenantScopedModel):
    PAGE_TYPE_CHOICES = [
        ("home", "Homepage"),
        ("about", "About"),
        ("admissions_info", "Admissions Information"),
        ("contact", "Contact"),
        ("custom", "Custom"),
    ]

    campus = models.ForeignKey(
        "core.Campus", on_delete=models.CASCADE, null=True, blank=True,
        related_name="pages", help_text="Null = tenant-wide page."
    )
    page_type = models.CharField(max_length=30, choices=PAGE_TYPE_CHOICES)
    slug = models.SlugField()
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="unique_page_slug_per_tenant"),
        ]

    def __str__(self):
        return f"{self.tenant.name} — {self.slug}"


class PageSection(TenantScopedModel):
    """One block on a page. section_type is the contract name the
    frontend's theme registry knows how to render (e.g. "hero" maps
    to every theme's HeroProps-shaped component). content holds
    whatever data that contract needs — theme controls how it LOOKS,
    this row controls what it SAYS."""

    SECTION_TYPE_CHOICES = [
        ("hero", "Hero"),
        ("text_block", "Text Block"),
        ("gallery", "Gallery"),
        ("testimonials", "Testimonials"),
        ("stats", "Stats/Numbers"),
        ("cta", "Call to Action"),
        ("faq", "FAQ"),
    ]

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="sections")
    section_type = models.CharField(max_length=30, choices=SECTION_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    # Matches whatever TS interface the frontend defines for this
    # section_type (e.g. {"heading": "...", "subheading": "...",
    # "cta_label": "...", "cta_url": "..."} for "hero"). Backend does
    # NOT validate shape strictly — the frontend's TS contract is the
    # source of truth for what's expected; this is intentionally loose
    # so new section fields don't require a migration.
    content = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["page", "order"]

    def __str__(self):
        return f"{self.page} — {self.section_type} (#{self.order})"


class NavItem(TenantScopedModel):
    """Site-wide, not page-specific — same nav shows on every public page."""
    label = models.CharField(max_length=100)
    url_path = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["tenant", "order"]

    def __str__(self):
        return f"{self.tenant.name} — {self.label}"


class GalleryItem(TenantScopedModel):
    """A reusable media asset. A page's 'gallery' section references a
    subset of these via IDs in its content JSON, rather than each
    gallery section owning its own duplicate image rows."""
    campus = models.ForeignKey(
        "core.Campus", on_delete=models.CASCADE, null=True, blank=True, related_name="gallery_items"
    )
    caption = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(help_text="Cloudinary URL, per locked media infra.")

    def __str__(self):
        return f"{self.tenant.name} — {self.caption or 'Untitled'}"