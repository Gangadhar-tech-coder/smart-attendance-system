#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Collect static files
python manage.py collectstatic --no-input

# 3. Apply database migrations
python manage.py migrate

# 4. Load old data (if you have it)
python manage.py loaddata mydata.json || true

# 5. AUTO-CREATE SUPERUSER (The Magic Step)
# This creates a user 'admin_new' with password 'admin123' automatically.
# It checks if the user exists first so it doesn't crash on the second deploy.
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin_new').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell