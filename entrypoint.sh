#!/bin/sh

python manage.py collectstatic --noinput

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting Daphne (production mode)..."
    daphne -b 0.0.0.0 -p 8000 mysite.asgi:application
else
    echo "Starting Django runserver (development mode)..."
    python manage.py runserver 0.0.0.0:8000
fi