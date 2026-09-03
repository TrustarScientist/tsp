# apps/content/tests.py
from django.test import TestCase
from apps.core.models import Tenant, set_current_tenant, reset_current_tenant
from apps.core.db import tenant_scope
from apps.content.models import Page, PageSection


class ContentTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Content Test School", subdomain="content-test")

    def test_page_with_ordered_sections(self):
        token = set_current_tenant(self.tenant)
        try:
            with tenant_scope(self.tenant):
                page = Page.objects.create(
                    tenant=self.tenant, page_type="home", slug="home", is_published=True
                )
                PageSection.objects.create(
                    tenant=self.tenant, page=page, section_type="hero", order=0,
                    content={"heading": "Welcome"},
                )
                PageSection.objects.create(
                    tenant=self.tenant, page=page, section_type="stats", order=1,
                    content={"items": []},
                )
                sections = list(page.sections.all())
                self.assertEqual(len(sections), 2)
                self.assertEqual(sections[0].section_type, "hero")
                self.assertEqual(sections[1].section_type, "stats")
        finally:
            reset_current_tenant(token)