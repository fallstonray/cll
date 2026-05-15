from django.core.management.base import BaseCommand
from django.utils import timezone
from maintenance.models import Contract


class Command(BaseCommand):
    help = 'Sets is_active=False on contracts whose end_date has passed'

    def handle(self, *args, **options):
        today = timezone.now().date()
        count = Contract.objects.filter(end_date__lt=today, is_active=True).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'{count} contract(s) marked inactive'))
