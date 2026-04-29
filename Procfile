web: python manage.py migrate && python manage.py sync_admin_user && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
worker: python manage.py migrate && python manage.py runbot
