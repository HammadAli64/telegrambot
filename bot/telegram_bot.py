import logging
from asgiref.sync import sync_to_async
from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.request import HTTPXRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from models.models import BotSession, PaidMember, Task

logger = logging.getLogger(__name__)

CATEGORIES = ["Design", "Development", "Marketing", "Writing", "Video Editing", "Other"]


def _admin_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Approve", callback_data=f"approve:{task_id}"),
                InlineKeyboardButton("Reject", callback_data=f"reject:{task_id}"),
            ]
        ]
    )


@sync_to_async
def _is_paid_member(user_id: int) -> bool:
    return PaidMember.objects.filter(user_id=user_id, is_active=True).exists()


@sync_to_async
def _get_or_create_session(user_id: int) -> BotSession:
    session, _ = BotSession.objects.get_or_create(user_id=user_id)
    return session


@sync_to_async
def _delete_session(user_id: int) -> None:
    BotSession.objects.filter(user_id=user_id).delete()


@sync_to_async
def _save_session_step(session: BotSession, step: str, data: dict) -> None:
    session.step = step
    session.data = data
    session.save(update_fields=["step", "data", "updated_at"])


@sync_to_async
def _create_task_from_session(user, data: dict) -> Task:
    return Task.objects.create(
        telegram_user_id=user.id,
        telegram_username=user.username or "",
        name=data["name"],
        phone_number=data["phone_number"],
        category=data["category"],
        address=data.get("address", ""),
        description=data["description"],
        status=Task.STATUS_PENDING,
    )


@sync_to_async
def _pending_tasks():
    return list(Task.objects.filter(status=Task.STATUS_PENDING)[:20])


@sync_to_async
def _get_task(task_id: int):
    return Task.objects.filter(id=task_id).first()


@sync_to_async
def _mark_approved(task: Task) -> None:
    task.status = Task.STATUS_APPROVED
    task.save(update_fields=["status", "updated_at"])


@sync_to_async
def _mark_rejected(task: Task) -> None:
    task.status = Task.STATUS_REJECTED
    task.save(update_fields=["status", "updated_at"])


def _task_message(task: Task) -> str:
    return (
        f"Task #{task.id}\n"
        f"Name: {task.name}\n"
        f"Phone: {task.phone_number}\n"
        f"Category: {task.category}\n"
        f"Address: {task.address or '-'}\n"
        f"Description: {task.description}"
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    logger.info("Received /start from user_id=%s username=%s", user.id, user.username or "")
    paid_note = "You are not a paid member yet." if not await _is_paid_member(user.id) else "Paid member access is active."
    text = (
        "Welcome to the task marketplace bot.\n\n"
        "Commands:\n"
        "/post_task - submit a new task\n"
        "\n"
        f"{paid_note}"
    )
    await message.reply_text(text)


async def post_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    session = await _get_or_create_session(user.id)
    data = session.data or {}
    await _save_session_step(session, "name", data)
    await message.reply_text("Please enter your full name:")


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    if user.id != settings.TELEGRAM_ADMIN_ID:
        await message.reply_text("Unauthorized.")
        return

    tasks = await _pending_tasks()
    if not tasks:
        await message.reply_text("No pending tasks found.")
        return

    for task in tasks:
        await message.reply_text(_task_message(task), reply_markup=_admin_keyboard(task.id))


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    telegram_message = update.effective_message
    if not user or not telegram_message or not telegram_message.text:
        return
    message = telegram_message.text.strip()
    session = await _get_or_create_session(user.id)
    logger.info("Received text from user_id=%s step=%s text=%s", user.id, session.step, message[:80])
    data = dict(session.data or {})

    if session.step == "name":
        data["name"] = message
        await _save_session_step(session, "phone_number", data)
        await telegram_message.reply_text("Enter phone number:")
        return

    if session.step == "phone_number":
        data["phone_number"] = message
        await _save_session_step(session, "category", data)
        await telegram_message.reply_text(f"Enter category ({', '.join(CATEGORIES)}):")
        return

    if session.step == "category":
        data["category"] = message
        await _save_session_step(session, "address", data)
        await telegram_message.reply_text("Enter address (or type '-' to skip):")
        return

    if session.step == "address":
        data["address"] = "" if message == "-" else message
        await _save_session_step(session, "description", data)
        await telegram_message.reply_text("Write your task description:")
        return

    if session.step == "description":
        data["description"] = message
        task = await _create_task_from_session(user, data)
        await _delete_session(user.id)
        await telegram_message.reply_text(f"Task submitted successfully as pending (ID: {task.id}).")
        return

    await telegram_message.reply_text("Use /post_task to start task submission.")


async def moderation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if user.id != settings.TELEGRAM_ADMIN_ID:
        await query.edit_message_text("Unauthorized action.")
        return

    action, task_id_str = query.data.split(":")
    task = await _get_task(int(task_id_str))
    if not task:
        await query.edit_message_text("Task no longer exists.")
        return

    if action == "approve":
        await _mark_approved(task)
        if settings.TELEGRAM_PRIVATE_CHANNEL_ID:
            try:
                await context.bot.send_message(chat_id=settings.TELEGRAM_PRIVATE_CHANNEL_ID, text=_task_message(task))
            except Exception:
                logger.exception("Failed posting approved task to private channel")
        await query.edit_message_text(f"Approved task #{task.id}")
        return

    await _mark_rejected(task)
    await query.edit_message_text(f"Rejected task #{task.id}")


def build_application() -> Application:
    builder = Application.builder().token(settings.TELEGRAM_BOT_TOKEN)
    if settings.TELEGRAM_PROXY_URL:
        request = HTTPXRequest(proxy=settings.TELEGRAM_PROXY_URL)
        # Use the same transport for both Bot API calls and getUpdates polling.
        builder = builder.request(request).get_updates_request(request)

    app = builder.build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("post_task", post_task_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(moderation_callback, pattern=r"^(approve|reject):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    return app
