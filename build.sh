#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "📦 Installing backend requirements..."
pip install -r requirements.txt

echo "🎨 Collecting static assets..."
python manage.py collectstatic --no-input

echo "🔄 Running database migrations..."
python manage.py migrate

if [ "$SEED_DEMO_DATA" = "true" ]; then
    echo "🌱 Seeding demo telemetry & accounts (SEED_DEMO_DATA=true)..."
    python manage.py seed_demo_data
else
    echo "ℹ️ Skipping demo data seeding (set SEED_DEMO_DATA=true to force seed)."
fi

echo "✅ Build completed successfully!"
