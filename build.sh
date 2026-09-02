#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "📦 Installing backend requirements..."
pip install -r requirements.txt

echo "🎨 Collecting static assets..."
python manage.py collectstatic --no-input

echo "🔄 Running database migrations..."
python manage.py migrate

echo "🌱 Seeding demo telemetry & accounts..."
python manage.py seed_demo_data

echo "✅ Build completed successfully!"
