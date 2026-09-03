# apps/core/management/commands/apply_rls.py
"""
Usage: python manage.py apply_rls <table_name>
Applies the standard tenant-isolation RLS policy to a table. Safe to
re-run — drops and recreates the policy if it already exists.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Apply the standard tenant-isolation RLS policy to a table."

    def add_arguments(self, parser):
        parser.add_argument("table_name", type=str)

    def handle(self, *args, **options):
        table = options["table_name"]
        policy_name = f"tenant_isolation_{table}"

        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            cursor.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
            cursor.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table};")
            cursor.execute(f"""
                CREATE POLICY {policy_name} ON {table}
                    USING (
                        current_setting('app.bypass_tenant_scope', true) = 'true'
                        OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
                    )
                    WITH CHECK (
                        current_setting('app.bypass_tenant_scope', true) = 'true'
                        OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
                    );
            """)
        self.stdout.write(self.style.SUCCESS(f"RLS applied to {table}"))