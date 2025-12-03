#!/bin/bash
###############################################################################
# 314Sign Installer
# 
# Compatible with:
#   - fullpageOS (Raspberry Pi kiosk mode)
#   - Raspberry Pi OS Lite 64-bit (manual kiosk setup required)
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh
#   chmod +x setup-kiosk.sh
#   sudo ./setup-kiosk.sh
###############################################################################

set -e  # Exit on any error

echo "=== 314Sign Installer ==="
echo ""

# === 1. Install required packages ===
echo "Installing packages..."
sudo apt update
sudo apt install -y lighttpd php-cgi git qrencode

# Optional packages (needed for kiosk automation features, skip on headless systems)
echo "Installing optional packages..."
sudo apt install -y inotify-tools xdotool 2>/dev/null || echo "Note: Some optional packages unavailable (normal for headless systems)"

# Enable PHP and WebDAV
echo "Enabling lighttpd modules..."
sudo lighty-enable-mod fastcgi
sudo lighty-enable-mod fastcgi-php
sudo lighty-enable-mod webdav

# === 2. Clone 314Sign from GitHub ===
TEMP_DIR=$(mktemp -d)
echo "Cloning 314Sign into $TEMP_DIR..."
if ! git clone --depth 1 https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign"; then
  echo "ERROR: Git clone failed!"
  exit 1
fi

echo "Clone successful. Checking contents..."
ls -la "$TEMP_DIR/314Sign/" | head -20

# === 3. Copy files to web root ===
echo "Copying files to /var/www/html..."
if ! sudo rsync -av \
  --exclude='.git' \
  --exclude='*.md' \
  --exclude='setup-kiosk.sh' \
  "$TEMP_DIR/314Sign/" /var/www/html/; then
  echo "ERROR: rsync failed!"
  exit 1
fi

echo "Files copied. Verifying..."
ls -la /var/www/html/ | head -20

# === 4. Create required directories ===
sudo mkdir -p /var/www/html/logs
sudo mkdir -p /var/www/html/bg
sudo mkdir -p /var/www/html/menus
sudo mkdir -p /var/www/html/scripts

# === 5. Set ownership & permissions ===
echo "Setting permissions..."
# Copy permissions script to temp location and run it
cp "$TEMP_DIR/314Sign/scripts/permissions.sh" /tmp/314sign-permissions.sh
chmod +x /tmp/314sign-permissions.sh
/tmp/314sign-permissions.sh /var/www/html
rm /tmp/314sign-permissions.sh

# === 6. Configure lighttpd ===
LIGHTTPD_CONF="/etc/lighttpd/lighttpd.conf"
WEBDAV_CONF="/etc/lighttpd/conf-enabled/10-webdav.conf"

# Enable ETag
if ! grep -q "server.etag" "$LIGHTTPD_CONF"; then
  echo 'server.etag = "enable"' | sudo tee -a "$LIGHTTPD_CONF"
fi

# WebDAV: only allow safe files
sudo tee "$WEBDAV_CONF" > /dev/null << 'EOF'
server.modules += ( "mod_webdav" )

# Enable WebDAV for specific editable files
$HTTP["url"] =~ "^/(index\.html|config\.json|rules\.json)$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}

# Enable WebDAV for menu files
$HTTP["url"] =~ "^/menus/(breakfast|lunch|dinner|closed)\.txt$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}

# Enable WebDAV for editor pages
$HTTP["url"] =~ "^/(edit|design|rules)/index\.html$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}
EOF

# === 7. Generate QR codes ===
echo "Generating QR codes..."
HOSTNAME=$(hostname)
cd /var/www/html
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://${HOSTNAME}.local/edit/"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://${HOSTNAME}.local/design/"
[ ! -f qr-rules.png ] && qrencode -o qr-rules.png -s 10 "http://${HOSTNAME}.local/rules/"

# === 8. Restart services ===
echo "Restarting lighttpd..."
sudo systemctl restart lighttpd

# === 9. Cleanup ===
rm -rf "$TEMP_DIR"

echo ""
echo "✅ 314Sign installed successfully!"
echo ""
echo "📺 Kiosk Display:"
echo "   http://${HOSTNAME}.local"
echo ""
echo "📱 Staff Editors:"
echo "   • Menu Editor:   http://${HOSTNAME}.local/edit/"
echo "   • Style Config:  http://${HOSTNAME}.local/design/"
echo "   • Auto Schedule: http://${HOSTNAME}.local/rules/"
echo ""
echo "🔧 Monitoring:"
echo "   • Health Check:  http://${HOSTNAME}.local/status.php"
echo "   • Run Backup:    sudo /var/www/html/scripts/backup.sh"
echo ""
echo "Print QR codes from /var/www/html/qr-*.png"
echo ""
