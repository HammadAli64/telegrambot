from django.contrib import admin

from .models import BotSession, PaidMember, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "phone_number", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "phone_number", "description", "telegram_username")


@admin.register(PaidMember)
class PaidMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "username", "full_name", "is_active", "created_at")
    search_fields = ("user_id", "username", "full_name")
    list_filter = ("is_active",)


@admin.register(BotSession)
class BotSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "step", "updated_at")
    search_fields = ("user_id", "step")
