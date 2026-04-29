import json
import logging

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot

from models.models import PaidMember, Task

logger = logging.getLogger(__name__)


def _authorized(request: HttpRequest) -> bool:
    return bool(request.session.get("panel_authenticated"))


def _task_message(task: Task) -> str:
    return (
        f"Task #{task.id}\n"
        f"Name: {task.name}\n"
        f"Phone: {task.phone_number}\n"
        f"Category: {task.category}\n"
        f"Address: {task.address or '-'}\n"
        f"Description: {task.description}"
    )


def _post_approved_task(task: Task) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_PRIVATE_CHANNEL_ID:
        return
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        sent = async_to_sync(bot.send_message)(chat_id=settings.TELEGRAM_PRIVATE_CHANNEL_ID, text=_task_message(task))
        task.channel_chat_id = str(settings.TELEGRAM_PRIVATE_CHANNEL_ID)
        task.channel_message_id = sent.message_id
        task.save(update_fields=["channel_chat_id", "channel_message_id", "updated_at"])
    except Exception:
        logger.exception("Failed posting approved task to private channel")


def _edit_approved_task_message(task: Task) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    if not task.channel_message_id:
        # Fallback for older approved tasks that were posted before message metadata existed.
        _post_approved_task(task)
        return
    chat_id = task.channel_chat_id or settings.TELEGRAM_PRIVATE_CHANNEL_ID
    if not chat_id:
        return
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        async_to_sync(bot.edit_message_text)(
            chat_id=chat_id,
            message_id=task.channel_message_id,
            text=_task_message(task),
        )
    except Exception:
        logger.exception("Failed editing approved task message in channel")


def _delete_approved_task_message(task: Task) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not task.channel_message_id:
        return
    chat_id = task.channel_chat_id or settings.TELEGRAM_PRIVATE_CHANNEL_ID
    if not chat_id:
        return
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        async_to_sync(bot.delete_message)(
            chat_id=chat_id,
            message_id=task.channel_message_id,
        )
    except Exception:
        logger.exception("Failed deleting approved task message in channel")
    finally:
        task.channel_message_id = None
        task.channel_chat_id = ""
        task.save(update_fields=["channel_message_id", "channel_chat_id", "updated_at"])


def index(request: HttpRequest):
    return render(request, "index.html")


def login_page(request: HttpRequest):
    if _authorized(request):
        return redirect("tasks_page")
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if username == settings.PANEL_USERNAME and password == settings.PANEL_PASSWORD:
            request.session["panel_authenticated"] = True
            return redirect("tasks_page")
        error = "Invalid username or password."
    return render(request, "login.html", {"error": error})


def logout_page(request: HttpRequest):
    request.session.flush()
    return redirect("login_page")


def pending_page(request: HttpRequest):
    if not _authorized(request):
        return redirect("login_page")
    return render(request, "pending.html")


def members_page(request: HttpRequest):
    if not _authorized(request):
        return redirect("login_page")
    return render(request, "members.html")


def tasks_page(request: HttpRequest):
    if not _authorized(request):
        return redirect("login_page")
    return render(request, "tasks.html")


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
    if task.status != Task.STATUS_APPROVED:
        task.status = Task.STATUS_APPROVED
        task.save(update_fields=["status", "updated_at"])
        _post_approved_task(task)
    else:
        if task.channel_message_id:
            _edit_approved_task_message(task)
        else:
            _post_approved_task(task)

    return JsonResponse({"status": "approved"})


@csrf_exempt
def reject_task_api(request: HttpRequest, task_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    task = get_object_or_404(Task, id=task_id)
    if task.status == Task.STATUS_APPROVED:
        _delete_approved_task_message(task)
    task.status = Task.STATUS_REJECTED
    task.save(update_fields=["status", "updated_at"])
    return JsonResponse({"status": "rejected"})


def members_api(request: HttpRequest):
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    members = list(PaidMember.objects.filter(is_active=True).values())
    return JsonResponse({"items": members})


def all_tasks_api(request: HttpRequest):
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().lower()
    page = max(int(request.GET.get("page", 1)), 1)
    page_size = max(int(request.GET.get("page_size", 10)), 1)

    qs = Task.objects.all()
    if query:
        if query.isdigit():
            qs = qs.filter(id=int(query))
        else:
            qs = qs.filter(Q(name__icontains=query) | Q(category__icontains=query))
    if status in {Task.STATUS_PENDING, Task.STATUS_APPROVED, Task.STATUS_REJECTED}:
        qs = qs.filter(status=status)

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = list(qs.values()[start:end])
    total_pages = (total + page_size - 1) // page_size if total else 1
    return JsonResponse({"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages})


def _json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


@csrf_exempt
def update_task_api(request: HttpRequest, task_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    body = _json_body(request)
    allowed_fields = {"name", "phone_number", "category", "address", "description"}
    update_fields = {}
    for key in allowed_fields:
        if key in body:
            update_fields[key] = body[key]

    if not update_fields:
        return JsonResponse({"detail": "No valid fields provided"}, status=400)

    task = get_object_or_404(Task, id=task_id)

    for field, value in update_fields.items():
        setattr(task, field, value)
    task.save(update_fields=[*update_fields.keys(), "updated_at"])
    if task.status == Task.STATUS_APPROVED:
        if task.channel_message_id:
            _edit_approved_task_message(task)
        else:
            _post_approved_task(task)

    return JsonResponse({"status": "updated"})


@csrf_exempt
def delete_task_api(request: HttpRequest, task_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    if not _authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    task = get_object_or_404(Task, id=task_id)
    if task.status == Task.STATUS_APPROVED:
        _delete_approved_task_message(task)
    task.delete()
    return JsonResponse({"status": "deleted"})


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
