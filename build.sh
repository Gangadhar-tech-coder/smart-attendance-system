#!/usr/bin/env bash
# Exit on error
set -o errexit
echo "--- Collecting Static Files ---"
python manage.py collectstatic --no-input

echo "--- Migrating Database ---"
python manage.py migrate

echo "--- Creating Superuser (admin_new) ---"
# This python script creates the user safely
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin_new').exists() or User.objects.create_superuser('admin_new', 'admin@example.com', 'admin123')" | python manage.py shell

echo "--- Starting Server ---"
# We use 'exec' to allow gunicorn to handle signals properly
exec gunicorn smart_attendance.wsgi:application --bind 0.0.0.0:8000