# Telegram Task Marketplace Bot (Django)

This project is a complete backend + simple frontend system for a Telegram task marketplace.

## Features

- Customer flow via Telegram:
  - `/start`
  - `/post_task`
  - Step-by-step task form: name, phone, category, optional address, description
  - Saves tasks in SQLite with `pending` status
- Admin moderation via Telegram:
  - `/admin` for pending tasks
  - Inline buttons: Approve / Reject
  - Approved tasks are posted to a private Telegram channel
- Paid member system:
  - Track paid users in database
  - Add/remove members manually (management commands + web panel)
- Web UI (HTML/CSS/JS):
  - Pending tasks page
  - Members management page
- Logging:
  - Console logging configured in Django settings

## Project Structure

```text
bot/
  management/commands/
    runbot.py
    add_member.py
    remove_member.py
  telegram_bot.py
api/
  urls.py
  views.py
models/
  models.py
  admin.py
  migrations/
core/
  settings.py
  urls.py
database/
  db.sqlite3
templates/
static/
```

## Setup

1. Create and activate virtualenv (optional but recommended)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy env template:
   - `copy .env.example .env` (Windows)
4. Update `.env`:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ADMIN_ID`
   - `TELEGRAM_PRIVATE_CHANNEL_ID`
   - `TELEGRAM_PROXY_URL` (optional, if Telegram is blocked on your network)
   - `ADMIN_WEB_KEY`

## Run

1. Run migrations:
   - `python manage.py migrate`
2. Start Django server:
   - `python manage.py runserver`
3. Start Telegram bot polling (separate terminal):
   - `python manage.py runbot`

## Railway Deployment

Deploy as two services from the same GitHub repo:

1. **Web service**
   - Start command:
     - `python manage.py migrate && python manage.py sync_admin_user && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
2. **Worker service**
   - Start command:
     - `python manage.py migrate && python manage.py runbot`

Set these environment variables in Railway:

- `DJANGO_SECRET_KEY`
- `DEBUG=False`
- `REQUIRE_DATABASE_URL=true` (recommended in production)
- `ALLOWED_HOSTS` (include your Railway domain)
- `CSRF_TRUSTED_ORIGINS` (for example `https://your-app.up.railway.app`)
- `DATABASE_URL` (from Railway Postgres plugin)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_ID`
- `TELEGRAM_PRIVATE_CHANNEL_ID`
- `BOT_ENABLED` (`true` only for worker service, `false` for web service)
- `ADMIN_WEB_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_EMAIL` (optional)
- `TELEGRAM_PROXY_URL` (optional)

Add Railway Postgres plugin and ensure `DATABASE_URL` is present.  
This project automatically uses `DATABASE_URL` when provided, otherwise it falls back to SQLite for local development.
With `DEBUG=False` and `REQUIRE_DATABASE_URL=true`, startup will fail fast if `DATABASE_URL` is missing.

## Manual paid member management

- Add/activate member:
  - `python manage.py add_member 123456789 --username company1 --full-name "Company One"`
- Remove member:
  - `python manage.py remove_member 123456789`

## Web admin pages

Use `?key=ADMIN_WEB_KEY` in URL:

- Pending moderation:
  - `http://127.0.0.1:8000/admin/pending/?key=your-key`
- Members:
  - `http://127.0.0.1:8000/admin/members/?key=your-key`

## Built-in Django Admin Panel

Use Django built-in admin at:

- `https://<your-domain>/django-admin/`

Login credentials come from environment variables:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_EMAIL` (optional)

Task management in built-in admin supports:

- view/search/filter/sort all tasks
- edit/delete tasks
- approve/reject selected tasks using admin actions
- auto-post to private channel when task becomes approved

## Telegram Bot Commands

- `/start` - welcome + access info
- `/post_task` - submit a new task
- `/admin` - list pending tasks (admin only)

## Notes

- For production, replace simple `?key=` auth with a real auth system.
- Payment integration (Stripe/crypto) can be added by creating payment records and activating members automatically.
- If you get `getaddrinfo failed`, your DNS/network cannot resolve Telegram hosts. Set `TELEGRAM_PROXY_URL` in `.env` and run again.
