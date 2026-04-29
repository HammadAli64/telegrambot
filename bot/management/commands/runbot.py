from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from telegram.error import Conflict, NetworkError

from bot.telegram_bot import build_application
from models.models import Task


class Command(BaseCommand):
    help = "Run Telegram bot in polling mode."

    def handle(self, *args, **options):
        if not settings.BOT_ENABLED:
            self.stdout.write(self.style.WARNING("BOT_ENABLED is false. Skipping Telegram polling startup."))
            return

        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN is missing in environment.")

        db_engine = settings.DATABASES["default"].get("ENGINE", "unknown")
        db_name = settings.DATABASES["default"].get("NAME", "")
        db_host = settings.DATABASES["default"].get("HOST", "")
        self.stdout.write(f"DB engine: {db_engine}")
        self.stdout.write(f"DB target: {db_host or db_name}")
        self.stdout.write(f"DB connection vendor: {connection.vendor}")
        self.stdout.write(f"Current task count: {Task.objects.count()}")

        app = build_application()
        self.stdout.write(self.style.SUCCESS("Starting Telegram bot polling..."))
        try:
            app.run_polling(close_loop=False)
        except Conflict as exc:
            raise CommandError(
                "Telegram polling conflict: another bot instance is already running. "
                "Run polling in only one service or set BOT_ENABLED=false on others."
            ) from exc
        except NetworkError as exc:
            raise CommandError(
                "Network error while connecting to Telegram. "
                "Check DNS/firewall or set TELEGRAM_PROXY_URL in .env."
            ) from exc
