#!/bin/bash
# ============================================================
# Cherokee Bowling League - REDEPLOY / UPDATE
# Run this any time you upload new code changes.
# ============================================================

set -e

APP_DIR="/home/ec2-user/cherokeebowling"
cd "$APP_DIR"

echo "=== Installing / updating Python packages ==="
source .venv/bin/activate
pip install -r requirements.txt

echo "=== Running any new migrations ==="
python manage.py migrate

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Restarting Django app ==="
sudo systemctl restart cherokee-bowling

echo ""
echo "=== Site updated and restarted ==="
sudo systemctl status cherokee-bowling --no-pager
