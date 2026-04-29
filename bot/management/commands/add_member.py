from django.core.management.base import BaseCommand, CommandError

from models.models import PaidMember


class Command(BaseCommand):
    help = "Add or activate a paid member manually."

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)
        parser.add_argument("--username", type=str, default="")
        parser.add_argument("--full-name", type=str, default="")

    def handle(self, *args, **options):
        user_id = options["user_id"]
        if user_id <= 0:
            raise CommandError("user_id must be positive.")

        member, _ = PaidMember.objects.update_or_create(
            user_id=user_id,
            defaults={
                "username": options["username"],
                "full_name": options["full_name"],
                "is_active": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Member active: {member.user_id}"))
