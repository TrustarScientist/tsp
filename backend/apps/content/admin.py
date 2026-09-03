# apps/content/admin.py
from django.contrib import admin
from apps.core.admin import TenantScopedAdmin
from .models import Page, PageSection, NavItem, GalleryItem


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 1
    fields = ("section_type", "order", "is_visible", "content")


@admin.register(Page)
class PageAdmin(TenantScopedAdmin):
    list_display = ("slug", "tenant", "page_type", "is_published")
    list_filter = ("tenant", "page_type", "is_published")
    inlines = [PageSectionInline]


@admin.register(NavItem)
class NavItemAdmin(TenantScopedAdmin):
    list_display = ("label", "tenant", "order", "is_visible")
    list_filter = ("tenant",)


@admin.register(GalleryItem)
class GalleryItemAdmin(TenantScopedAdmin):
    list_display = ("caption", "tenant", "campus")
    list_filter = ("tenant",)