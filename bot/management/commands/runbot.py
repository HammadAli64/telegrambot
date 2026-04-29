from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram.error import NetworkError

from bot.telegram_bot import build_application


class Command(BaseCommand):
    help = "Run Telegram bot in polling mode."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN is missing in environment.")

        app = build_application()
        self.stdout.write(self.style.SUCCESS("Starting Telegram bot polling..."))
        try:
            app.run_polling(close_loop=False)
        except NetworkError as exc:
            raise CommandError(
                "Network error while connecting to Telegram. "
                "Check DNS/firewall or set TELEGRAM_PROXY_URL in .env."
            ) from exc
