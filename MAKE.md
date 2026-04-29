# Task Marketplace Bot Workflow

This document summarizes the complete workflow of the Telegram task marketplace bot.

## 1) System Overview

- Customer submits tasks via Telegram bot.
- Task is saved in database with `pending` status.
- Admin reviews pending tasks and approves/rejects.
- Approved tasks are posted to private Telegram channel.
- Paid member records are managed from web panel or management commands.

## 2) Runtime Roles

- **Web role**: Django HTTP app (pages + APIs)
- **Worker role**: Telegram polling bot (`runbot`)

Only one worker instance must run polling for a token.

## 3) Environment Variables

Required (production):

- `DJANGO_SECRET_KEY`
- `DEBUG=false`
- `REQUIRE_DATABASE_URL=true`
- `DATABASE_URL` (Railway Postgres)
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_ID`
- `TELEGRAM_PRIVATE_CHANNEL_ID`
- `BOT_ENABLED`
- `ADMIN_WEB_KEY`

Optional:

- `TELEGRAM_PROXY_URL`

## 4) Customer Flow

1. User sends `/start`.
2. User sends `/post_task`.
3. Bot asks step-by-step:
   - Name
   - Phone number
   - Category
   - Address (optional, `-` to skip)
   - Task description
4. Bot creates task with `pending` status.

## 5) Admin Moderation Flow (Telegram)

1. Admin sends `/admin`.
2. Bot lists pending tasks with inline buttons:
   - Approve
   - Reject
3. On Approve:
   - status becomes `approved`
   - task is posted to private channel
4. On Reject:
   - status becomes `rejected`

Only `TELEGRAM_ADMIN_ID` is allowed to use moderation actions.

## 6) Web Panel Flow

Protected by `ADMIN_WEB_KEY` in URL:

- `/admin/pending/?key=<ADMIN_WEB_KEY>`
- `/admin/members/?key=<ADMIN_WEB_KEY>`

Capabilities:

- View pending tasks
- Approve/reject tasks
- Add/remove paid members

## 7) Railway Deployment Flow

### Recommended split

- Web service:
  - `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
  - `BOT_ENABLED=false`
- Worker service:
  - `python manage.py migrate && python manage.py runbot`
  - `BOT_ENABLED=true`

### Single-service bot-only mode

- Start command:
  - `python manage.py migrate && python manage.py runbot`

## 8) Database Verification Flow

At worker startup logs:

- DB engine
- DB target
- DB vendor
- Current task count

These logs confirm whether app is actually connected to Postgres.

## 9) Security Notes

- `/admin` moderation is enforced by server-side admin ID check.
- Inline approve/reject callbacks also enforce admin ID check.
- Keep `.env` out of git.
- Rotate Telegram token if leaked.

## 10) Quick Troubleshooting

- `409 Conflict`: more than one polling instance running.
- `No pending tasks found`: no pending rows or wrong DB service.
- `no such table`: migrations not applied to active DB.
- `getaddrinfo failed`: DNS/proxy/network issue.

