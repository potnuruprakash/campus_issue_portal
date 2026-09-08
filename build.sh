#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Collect static files for WhiteNoise
python manage.py collectstatic --noinput

# 3. Apply database migrations
python manage.py migrate

# 4. Initialize MongoDB Atlas collections, indexes, and baseline seed data (safe & idempotent)
python manage.py seed_data
