import logging

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib import admin, messages
from telegram import Bot

from .models import BotSession, PaidMember, Task

logger = logging.getLogger(__name__)


def _task_message(task: Task) -> str:
    return (
        f"Task #{task.id}\n"
        f"Name: {task.name}\n"
        f"Phone: {task.phone_number}\n"
        f"Category: {task.category}\n"
        f"Address: {task.address or '-'}\n"
        f"Description: {task.description}"
    )


def _post_task_to_channel(task: Task) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_PRIVATE_CHANNEL_ID:
        return
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        async_to_sync(bot.send_message)(chat_id=settings.TELEGRAM_PRIVATE_CHANNEL_ID, text=_task_message(task))
    except Exception:
        logger.exception("Failed posting approved task #%s from Django admin", task.id)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "phone_number", "status", "telegram_user_id", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "phone_number", "description", "telegram_username")
    ordering = ("-created_at",)
    actions = ("approve_selected_tasks", "reject_selected_tasks")

    @admin.action(description="Approve selected tasks")
    def approve_selected_tasks(self, request, queryset):
        approved_count = 0
        for task in queryset:
            if task.status != Task.STATUS_APPROVED:
                task.status = Task.STATUS_APPROVED
                task.save(update_fields=["status", "updated_at"])
                _post_task_to_channel(task)
                approved_count += 1
        self.message_user(request, f"Approved {approved_count} task(s).", level=messages.SUCCESS)

    @admin.action(description="Reject selected tasks")
    def reject_selected_tasks(self, request, queryset):
        updated = queryset.exclude(status=Task.STATUS_REJECTED).update(status=Task.STATUS_REJECTED)
        self.message_user(request, f"Rejected {updated} task(s).", level=messages.WARNING)

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:
            old_status = Task.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if obj.status == Task.STATUS_APPROVED and old_status != Task.STATUS_APPROVED:
            _post_task_to_channel(obj)


@admin.register(PaidMember)
class PaidMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "username", "full_name", "is_active", "created_at")
    search_fields = ("user_id", "username", "full_name")
    list_filter = ("is_active",)


@admin.register(BotSession)
class BotSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "step", "updated_at")
    search_fields = ("user_id", "step")
