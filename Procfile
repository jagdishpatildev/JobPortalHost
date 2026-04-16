web: python manage.py migrate --no-input && python manage.py collectstatic --no-input --clear && daphne -b 0.0.0.0 -p $PORT job_portal.asgi:application
