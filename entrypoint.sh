#!/bin/sh
set -e

# Ensure static root exists
mkdir -p /app/staticfiles

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Purge logic runs in both dev and prod
if [ "$RUN_PURGE_ON_STARTUP" = "true" ]; then
    echo "Purging old rooms..."
    python manage.py purge_old_rooms
fi

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting Daphne (production mode)..."
    daphne -b 0.0.0.0 -p 8000 mysite.asgi:application
else
    echo "Starting Django runserver (development mode)..."
    python manage.py runserver 0.0.0.0:8000
fi
