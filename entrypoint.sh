#!/bin/sh
set -e

echo "=============================================="
echo "⚡ Starting Prompt Petti in Docker Container..."
echo "=============================================="

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Seeding initial demo data (Categories, Prompts, Admin)..."
python manage.py seed_demo

echo "==> Collecting static assets via WhiteNoise..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn WSGI server on port 8000..."
exec gunicorn promptpetti.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
