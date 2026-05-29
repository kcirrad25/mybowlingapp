#!/bin/bash
# ============================================================
# Cherokee Bowling League - FIRST DEPLOY
# Run this ONCE after uploading your code to the server.
# ============================================================

set -e

APP_DIR="/home/ec2-user/cherokeebowling"
cd "$APP_DIR"

echo "=== Installing Python packages ==="
source .venv/bin/activate
pip install -r requirements.txt

echo "=== Running database migrations ==="
python manage.py migrate

echo "=== Creating admin user ==="
python manage.py createsuperuser

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Creating log directory ==="
mkdir -p logs

echo "=== Installing systemd service ==="
sudo cp deploy/cherokee-bowling.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cherokee-bowling
sudo systemctl start cherokee-bowling

echo "=== Installing nginx config ==="
sudo cp deploy/nginx.conf /etc/nginx/conf.d/cherokee-bowling.conf
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo ""
echo "============================================================"
echo "FIRST DEPLOY COMPLETE!"
echo ""
echo "Check status:  sudo systemctl status cherokee-bowling"
echo "Check logs:    tail -f $APP_DIR/logs/error.log"
echo "Nginx logs:    sudo tail -f /var/log/nginx/error.log"
echo "============================================================"
