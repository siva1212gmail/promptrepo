from django.core.management.base import BaseCommand
from django.utils import timezone
from prompts.models import Prompt


class Command(BaseCommand):
    help = "Checks and confirms publishing of due scheduled drops (publish_at <= now)."

    def handle(self, *args, **options):
        now = timezone.now()
        due_prompts = Prompt.objects.filter(is_published=True, publish_at__lte=now)
        count = due_prompts.count()
        self.stdout.write(self.style.SUCCESS(f"Found {count} live drops currently published and available to visitors."))
