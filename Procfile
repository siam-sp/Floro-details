web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn florodetailing.wsgi --bind 0.0.0.0:$PORT
