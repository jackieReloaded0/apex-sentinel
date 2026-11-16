"""
Django 管理コマンド: check_apex
Cloud Run Jobs または手動実行用: python manage.py check_apex
"""
from django.core.management.base import BaseCommand
from jobs.check_apex import run_check_apex


class Command(BaseCommand):
    help = "Run Oracle APEX keep-alive health check and save log to Firestore"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Executing Oracle APEX health check..."))
        try:
            result = run_check_apex()
            if result.get("is_healthy"):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Health check succeeded! Status: {result.get('status_code')}, Time: {result.get('response_time_ms')}ms"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Health check warning/failure. Status: {result.get('status_code')}, Error: {result.get('error_message')}"
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during health check execution: {e}"))
