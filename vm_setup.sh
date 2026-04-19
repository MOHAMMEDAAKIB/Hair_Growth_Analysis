#!/usr/bin/env bash
# =============================================================================
# Oracle VM first-time setup script for Hair AI Pro (FastAPI + YOLO + OpenCV)
# Run this ONCE on a fresh Ubuntu 22.04 Oracle Always Free VM as the ubuntu user
# Usage: bash vm_setup.sh
# =============================================================================

set -euo pipefail

REPO_URL="https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git"  # <-- change this
APP_DIR="/opt/hair_ai_pro"
SERVICE_FILE="hair-ai-pro.service"
NGINX_CONF="hair-ai-pro.nginx.conf"

echo "========================================"
echo " Hair AI Pro — VM Setup"
echo "========================================"

# ── 1. System packages ────────────────────────────────────────────────────────
echo "[1/7] Installing system packages..."
sudo apt-get update -y
sudo apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    git nginx curl \
    libgl1 libglib2.0-0 \
    build-essential

# ── 2. Clone the repo ─────────────────────────────────────────────────────────
echo "[2/7] Cloning repository to $APP_DIR..."
sudo mkdir -p "$APP_DIR"
sudo chown ubuntu:ubuntu "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

# ── 3. Python virtual environment ─────────────────────────────────────────────
echo "[3/7] Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 4. Environment variables ──────────────────────────────────────────────────
echo "[4/7] Creating .env file..."
cat > "$APP_DIR/.env" << 'EOF'
# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_or_service_key_here

# ── AWS S3 ────────────────────────────────────────────────
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_S3_BUCKET=your_bucket_name_here
AWS_REGION=your_region_here

# ── Other APIs ────────────────────────────────────────────
# Add your other API keys below
# SOME_API_KEY=value

# ── App settings ──────────────────────────────────────────
ENVIRONMENT=production
EOF
echo "  !! IMPORTANT: Edit $APP_DIR/.env and fill in your real secrets before starting the service."

# ── 5. Systemd service ────────────────────────────────────────────────────────
echo "[5/7] Installing systemd service..."
sudo cp "$APP_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable hair-ai-pro

# ── 6. Nginx config ───────────────────────────────────────────────────────────
echo "[6/7] Configuring Nginx..."
sudo cp "$APP_DIR/$NGINX_CONF" /etc/nginx/sites-available/hair-ai-pro
sudo ln -sf /etc/nginx/sites-available/hair-ai-pro /etc/nginx/sites-enabled/hair-ai-pro
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# ── 7. Oracle firewall (iptables) ─────────────────────────────────────────────
echo "[7/7] Opening firewall ports 80 and 443..."
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
# Persist rules across reboots
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

echo ""
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit $APP_DIR/.env with your real secrets"
echo "  2. sudo systemctl start hair-ai-pro"
echo "  3. sudo systemctl status hair-ai-pro"
echo "  4. Update /etc/nginx/sites-available/hair-ai-pro — set your IP/domain in server_name"
echo "  5. (Optional) Run: sudo certbot --nginx to get free HTTPS via Let's Encrypt"
echo ""
