#!/bin/bash
# ============================================================
# Cherokee Bowling League - ONE-TIME EC2 Server Setup
# Run this ONCE after first connecting to your EC2 instance.
# Amazon Linux 2023
# ============================================================

set -e

APP_DIR="/home/ec2-user/cherokeebowling"
APP_USER="ec2-user"

echo "=== Step 1: Update system packages ==="
sudo dnf update -y

echo "=== Step 2: Install Python 3.11, nginx, git ==="
sudo dnf install -y python3.11 python3.11-pip python3.11-devel nginx git gcc

echo "=== Step 3: Create app directory ==="
mkdir -p "$APP_DIR"
cd "$APP_DIR"

echo "=== Step 4: Create Python virtual environment ==="
python3.11 -m venv .venv
source .venv/bin/activate

echo "=== Step 5: Upgrade pip ==="
pip install --upgrade pip

echo ""
echo "============================================================"
echo "SETUP COMPLETE."
echo ""
echo "Next steps:"
echo "  1. Upload your project code to: $APP_DIR"
echo "     (the deploy.sh script will do this for you)"
echo "  2. Create your .env file:"
echo "     nano $APP_DIR/.env"
echo "  3. Run the first deploy:"
echo "     bash $APP_DIR/deploy/first_deploy.sh"
echo "============================================================"
