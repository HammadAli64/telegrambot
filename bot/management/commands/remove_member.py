from django.core.management.base import BaseCommand, CommandError

from models.models import PaidMember


class Command(BaseCommand):
    help = "Deactivate a paid member manually."

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        user_id = options["user_id"]
        if user_id <= 0:
            raise CommandError("user_id must be positive.")

        updated = PaidMember.objects.filter(user_id=user_id).update(is_active=False)
        if not updated:
            raise CommandError("Member not found.")
        self.stdout.write(self.style.SUCCESS(f"Member removed: {user_id}"))
