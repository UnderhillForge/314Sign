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
echo "Temp directory: $TEMP_DIR"

# Test internet connectivity first
if ! ping -c 1 github.com >/dev/null 2>&1; then
  echo "ERROR: Cannot reach github.com - check internet connection"
  echo "Try: ping github.com"
  exit 1
fi

# Clone repository
if ! git clone --depth 1 https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign" 2>&1; then
  echo ""
  echo "ERROR: Git clone failed!"
  echo "Troubleshooting:"
  echo "  1. Check internet connection: ping github.com"
  echo "  2. Verify git is installed: git --version"
  echo "  3. Try manual clone: git clone https://github.com/UnderhillForge/314Sign.git"
  echo "  4. Check disk space: df -h"
  rm -rf "$TEMP_DIR"
  exit 1
fi

echo ""
echo "Clone successful. Checking contents..."
if [ ! -d "$TEMP_DIR/314Sign" ]; then
  echo "ERROR: Clone directory not created at $TEMP_DIR/314Sign"
  ls -la "$TEMP_DIR/"
  exit 1
fi

FILE_COUNT=$(find "$TEMP_DIR/314Sign" -type f | wc -l)
echo "Found $FILE_COUNT files in repository"
ls -la "$TEMP_DIR/314Sign/" | head -20

if [ "$FILE_COUNT" -lt 10 ]; then
  echo "WARNING: Very few files found - clone may be incomplete"
fi

# === 3. Copy files to web root ===
echo ""
echo "Copying files to /var/www/html..."

# Ensure web root exists
if [ ! -d "/var/www/html" ]; then
  echo "Creating /var/www/html directory..."
  sudo mkdir -p /var/www/html
fi

# Check if rsync is available, fall back to cp if not
if command -v rsync >/dev/null 2>&1; then
  echo "Using rsync to copy files..."
  if ! sudo rsync -av \
    --exclude='.git' \
    --exclude='*.md' \
    --exclude='setup-kiosk.sh' \
    "$TEMP_DIR/314Sign/" /var/www/html/ 2>&1; then
    echo ""
    echo "ERROR: rsync failed!"
    echo "Trying alternative copy method..."
    # Fallback to cp
    sudo cp -r "$TEMP_DIR/314Sign/"* /var/www/html/ 2>&1 || {
      echo "ERROR: Copy failed!"
      exit 1
    }
  fi
else
  echo "rsync not found, using cp instead..."
  sudo cp -r "$TEMP_DIR/314Sign/"* /var/www/html/ 2>&1 || {
    echo "ERROR: Copy failed!"
    exit 1
  }
fi

echo ""
echo "Files copied. Verifying..."
COPIED_COUNT=$(find /var/www/html -type f | wc -l)
echo "Found $COPIED_COUNT files in /var/www/html"
ls -la /var/www/html/ | head -20

if [ "$COPIED_COUNT" -lt 10 ]; then
  echo ""
  echo "WARNING: Very few files in /var/www/html - installation may be incomplete"
  echo "Contents of /var/www/html:"
  ls -la /var/www/html/
fi

# === 4. Create required directories ===
sudo mkdir -p /var/www/html/logs
sudo mkdir -p /var/www/html/bg
sudo mkdir -p /var/www/html/menus
sudo mkdir -p /var/www/html/scripts

# === 5. Set ownership & permissions ===
echo ""
echo "Setting permissions..."

# Check if permissions script exists
if [ -f "$TEMP_DIR/314Sign/scripts/permissions.sh" ]; then
  # Copy permissions script to temp location and run it
  cp "$TEMP_DIR/314Sign/scripts/permissions.sh" /tmp/314sign-permissions.sh
  chmod +x /tmp/314sign-permissions.sh
  /tmp/314sign-permissions.sh /var/www/html
  rm /tmp/314sign-permissions.sh
  echo "Permissions script executed successfully"
elif [ -f "/var/www/html/scripts/permissions.sh" ]; then
  # Use the already-copied permissions script
  chmod +x /var/www/html/scripts/permissions.sh
  /var/www/html/scripts/permissions.sh /var/www/html
  echo "Permissions script executed successfully"
else
  echo "WARNING: permissions.sh not found, setting basic permissions manually..."
  # Set basic permissions manually
  sudo chown -R www-data:www-data /var/www/html
  sudo find /var/www/html -type d -exec chmod 755 {} \;
  sudo find /var/www/html -type f -exec chmod 644 {} \;
  sudo chmod 775 /var/www/html/bg 2>/dev/null || true
  sudo chmod 775 /var/www/html/menus 2>/dev/null || true
  sudo chmod 775 /var/www/html/logs 2>/dev/null || true
  sudo chmod 664 /var/www/html/*.json 2>/dev/null || true
  sudo chmod 664 /var/www/html/index.html 2>/dev/null || true
  echo "Basic permissions set"
fi

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

# Final verification
echo "=== Installation Verification ==="
FINAL_COUNT=$(find /var/www/html -type f -name "*.html" -o -name "*.php" -o -name "*.json" | wc -l)
echo "Core files found: $FINAL_COUNT"

# Check critical files
MISSING_FILES=()
for file in "index.html" "config.json" "rules.json" "edit/index.html" "design/index.html" "rules/index.html" "status.php"; do
  if [ ! -f "/var/www/html/$file" ]; then
    MISSING_FILES+=("$file")
  fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  WARNING: Some critical files are missing:"
  for file in "${MISSING_FILES[@]}"; do
    echo "   ✗ $file"
  done
  echo ""
  echo "Troubleshooting steps:"
  echo "  1. Check if clone worked: ls -la /tmp/"
  echo "  2. Check internet: ping github.com"
  echo "  3. Try manual install:"
  echo "     cd /tmp && git clone https://github.com/UnderhillForge/314Sign.git"
  echo "     sudo cp -r 314Sign/* /var/www/html/"
  echo ""
else
  echo "✓ All critical files present"
  echo ""
fi

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
