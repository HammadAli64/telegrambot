import json
import logging

from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot

from models.models import PaidMember, Task

logger = logging.getLogger(__name__)


def _authorized(request: HttpRequest) -> bool:
    return bool(settings.ADMIN_WEB_KEY) and request.GET.get("key") == settings.ADMIN_WEB_KEY


def index(request: HttpRequest):
    return render(request, "index.html")


def pending_page(request: HttpRequest):
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    return render(request, "pending.html")


def members_page(request: HttpRequest):
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    return render(request, "members.html")


def pending_tasks_api(request: HttpRequest):
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    data = list(Task.objects.filter(status=Task.STATUS_PENDING).values())
    return JsonResponse({"items": data})


@csrf_exempt
def approve_task_api(request: HttpRequest, task_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    task = get_object_or_404(Task, id=task_id)
    task.status = Task.STATUS_APPROVED
    task.save(update_fields=["status", "updated_at"])

    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_PRIVATE_CHANNEL_ID:
        try:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            message = (
                f"Task #{task.id}\n"
                f"Name: {task.name}\n"
                f"Phone: {task.phone_number}\n"
                f"Category: {task.category}\n"
                f"Address: {task.address or '-'}\n"
                f"Description: {task.description}"
            )
            async_to_sync(bot.send_message)(chat_id=settings.TELEGRAM_PRIVATE_CHANNEL_ID, text=message)
        except Exception:
            logger.exception("Failed posting approved task via web panel")

    return JsonResponse({"status": "approved"})


@csrf_exempt
def reject_task_api(request: HttpRequest, task_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    task = get_object_or_404(Task, id=task_id)
    task.status = Task.STATUS_REJECTED
    task.save(update_fields=["status", "updated_at"])
    return JsonResponse({"status": "rejected"})


def members_api(request: HttpRequest):
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    members = list(PaidMember.objects.filter(is_active=True).values())
    return JsonResponse({"items": members})


def _json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


@csrf_exempt
def add_member_api(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    body = _json_body(request)
    user_id = int(body.get("user_id", 0))
    if not user_id:
        return JsonResponse({"detail": "user_id is required"}, status=400)

    member, _ = PaidMember.objects.update_or_create(
        user_id=user_id,
        defaults={
            "username": body.get("username", ""),
            "full_name": body.get("full_name", ""),
            "is_active": True,
        },
    )
    return JsonResponse({"status": "added", "member_id": member.id})


@csrf_exempt
def remove_member_api(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    body = _json_body(request)
    user_id = int(body.get("user_id", 0))
    if not user_id:
        return JsonResponse({"detail": "user_id is required"}, status=400)

    updated = PaidMember.objects.filter(user_id=user_id).update(is_active=False)
    if not updated:
        return JsonResponse({"detail": "Member not found"}, status=404)
    return JsonResponse({"status": "removed"})
