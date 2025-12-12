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
sudo apt install -y lighttpd lighttpd-mod-webdav php-cgi git qrencode

# Optional packages (needed for kiosk automation features, skip on headless systems)
echo "Installing optional packages..."
sudo apt install -y inotify-tools xdotool 2>/dev/null || echo "Note: Some optional packages unavailable (normal for headless systems)"

# Enable PHP and WebDAV
echo "Enabling lighttpd modules..."
sudo lighty-enable-mod fastcgi || true
sudo lighty-enable-mod fastcgi-php || true
sudo lighty-enable-mod webdav || true
echo "Lighttpd modules configured"

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
sudo mkdir -p /var/www/html/fonts
sudo mkdir -p /var/www/html/history
sudo mkdir -p /var/www/html/menus
sudo mkdir -p /var/www/html/scripts
sudo mkdir -p /var/www/html/start
sudo mkdir -p /var/www/html/slideshows/media
sudo mkdir -p /var/www/html/slideshows/sets

# Create reload.txt if it doesn't exist (used by edit page to trigger kiosk reload)
if [ ! -f /var/www/html/reload.txt ]; then
  echo "0" | sudo tee /var/www/html/reload.txt > /dev/null
  echo "Created reload.txt"
fi

# Create demo-command.txt if it doesn't exist (used by demo panel for remote control)
if [ ! -f /var/www/html/demo-command.txt ]; then
  echo "idle" | sudo tee /var/www/html/demo-command.txt > /dev/null
  echo "Created demo-command.txt"
fi

# Ensure page.json exists to allow external page selection (default to index)
if [ ! -f /var/www/html/page.json ]; then
  echo '{"page":"index"}' | sudo tee /var/www/html/page.json > /dev/null
  sudo chown www-data:www-data /var/www/html/page.json || true
  sudo chmod 644 /var/www/html/page.json || true
  echo "Created page.json"
fi

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

# Create backup directory (web-accessible location to avoid sudo issues in PHP)
echo "Creating backup directory..."
sudo mkdir -p /var/www/backups/314sign
sudo chown -R www-data:www-data /var/www/backups
sudo chmod 755 /var/www/backups
echo "✓ Backup directory created at /var/www/backups/314sign"

# === 5b. Configure sudo access for maintenance actions ===
echo ""
echo "Configuring sudo access for web-based maintenance..."

# Check if sudoers file exists in temp directory
if [ -f "$TEMP_DIR/314Sign/sudoers-314sign" ]; then
  # Copy to /etc/sudoers.d/
  sudo cp "$TEMP_DIR/314Sign/sudoers-314sign" /etc/sudoers.d/314sign
  sudo chmod 0440 /etc/sudoers.d/314sign
  
  # Validate the sudoers file
  if sudo visudo -cf /etc/sudoers.d/314sign; then
    echo "✓ Sudo access configured for maintenance actions"
    echo "  - Web interface can now restart server and apply updates"
  else
    echo "⚠ Sudoers file validation failed - removing invalid file"
    sudo rm -f /etc/sudoers.d/314sign
  fi
elif [ -f "/var/www/html/sudoers-314sign" ]; then
  # Fallback if already installed
  sudo cp /var/www/html/sudoers-314sign /etc/sudoers.d/314sign
  sudo chmod 0440 /etc/sudoers.d/314sign
  
  if sudo visudo -cf /etc/sudoers.d/314sign; then
    echo "✓ Sudo access configured from existing file"
  else
    sudo rm -f /etc/sudoers.d/314sign
  fi
else
  echo "⚠ sudoers-314sign not found - maintenance actions will require SSH"
  echo "  To enable later, copy sudoers-314sign to /etc/sudoers.d/314sign"
fi

# === 6. Configure lighttpd ===
echo ""
echo "Configuring lighttpd..."
LIGHTTPD_CONF="/etc/lighttpd/lighttpd.conf"
WEBDAV_CONF="/etc/lighttpd/conf-enabled/10-webdav.conf"

# Enable ETag (check for existing to avoid duplicates)
if ! grep -q "server.etag" "$LIGHTTPD_CONF"; then
  echo 'server.etag = "enable"' | sudo tee -a "$LIGHTTPD_CONF" > /dev/null
  echo "Added ETag configuration"
else
  echo "ETag already configured"
fi

# Validate lighttpd config before proceeding
echo "Validating lighttpd configuration..."
if ! sudo lighttpd -t -f "$LIGHTTPD_CONF" 2>&1; then
  echo ""
  echo "⚠️  WARNING: lighttpd configuration has errors!"
  echo "Attempting to fix common issues..."
  
  # Check for duplicate server.etag
  ETAG_COUNT=$(grep -c "^[[:space:]]*server.etag" "$LIGHTTPD_CONF" || true)
  if [ "$ETAG_COUNT" -gt 1 ]; then
    echo "Found duplicate server.etag entries, removing duplicates..."
    # Keep only the first occurrence
    sudo sed -i '/server.etag/!b;n;:a;/server.etag/d;n;ba' "$LIGHTTPD_CONF"
  fi
  
  # Validate again
  if ! sudo lighttpd -t -f "$LIGHTTPD_CONF" 2>&1; then
    echo ""
    echo "❌ Configuration still has errors. Manual intervention required:"
    echo "   sudo lighttpd -t -f /etc/lighttpd/lighttpd.conf"
    echo "   sudo nano /etc/lighttpd/lighttpd.conf"
    echo ""
    echo "Common fixes:"
    echo "   - Remove duplicate 'server.etag' lines"
    echo "   - Check for syntax errors in configuration"
    echo ""
  fi
fi

# WebDAV: only allow safe files
sudo tee "$WEBDAV_CONF" > /dev/null << 'EOF'
server.modules += ( "mod_webdav" )

# Enable WebDAV for specific editable files (NOTE: config.json is intentionally excluded
# here so raw PUTs are not allowed; use scripts/merge-config.php for safe config updates)
$HTTP["url"] =~ "^/(index\.html|rules\.json|menus-config\.json|reload\.txt|demo-command\.txt)$" {
  webdav.activate = "enable"
  webdav.is-readonly = "disable"
}

# Enable WebDAV for menu files
$HTTP["url"] =~ "^/menus/(breakfast|lunch|dinner|closed)\.txt$" {
  webdav.activate = "enable"
  webdav.is-readonly = "disable"
}

# Enable WebDAV for slideshow files
$HTTP["url"] =~ "^/slideshows/(index\.html|upload-media\.php)$" {
  webdav.activate = "enable"
  webdav.is-readonly = "disable"
}

$HTTP["url"] =~ "^/slideshows/sets/.*\.json$" {
  webdav.activate = "enable"
  webdav.is-readonly = "disable"
}

# Enable WebDAV for editor pages
$HTTP["url"] =~ "^/(edit|design|rules|slideshows|maintenance|start)/index\.html$" {
  webdav.activate = "enable"
  webdav.is-readonly = "disable"
}

# Rewrite raw PUTs to /config.json to a small guard script that returns an instructive error
# This prevents accidental destructive PUTs; legitimate updates should POST to scripts/merge-config.php
$HTTP["url"] == "/config.json" {
  $HTTP["request-method"] == "PUT" {
    url.rewrite-once = ( "^/config.json$" => "/scripts/put-guard.php" )
  }
}
EOF

# === 7. Generate QR codes ===
echo "Generating QR codes..."
HOSTNAME=$(hostname)
cd /var/www/html
[ ! -f qr-start.png ] && qrencode -o qr-start.png -s 10 "http://${HOSTNAME}.local/start/"
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://${HOSTNAME}.local/edit/"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://${HOSTNAME}.local/design/"
[ ! -f qr-rules.png ] && qrencode -o qr-rules.png -s 10 "http://${HOSTNAME}.local/rules/"

# === 8. Restart services ===
echo ""
echo "Restarting lighttpd..."

# Final config validation before restart
if sudo lighttpd -t -f "$LIGHTTPD_CONF" 2>&1 | grep -q "Syntax OK"; then
  if sudo systemctl restart lighttpd; then
    echo "✓ Lighttpd restarted successfully"
  else
    echo ""
    echo "❌ Lighttpd failed to restart"
    echo ""
    echo "Diagnostic commands:"
    echo "  sudo systemctl status lighttpd"
    echo "  sudo journalctl -xeu lighttpd.service"
    echo "  sudo tail -50 /var/log/lighttpd/error.log"
    echo ""
    echo "Common issues:"
    echo "  - Port 80 already in use (check: sudo netstat -tulpn | grep :80)"
    echo "  - Permission issues on /var/www/html"
    echo "  - Module conflicts in configuration"
    echo ""
  fi
else
  echo ""
  echo "⚠️  Skipping restart - configuration has errors"
  echo "Fix the errors above and restart manually:"
  echo "  sudo systemctl restart lighttpd"
  echo ""
fi

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
for file in "index.html" "config.json" "rules.json" "edit/index.html" "design/index.html" "rules/index.html" "maintenance/index.html" "start/index.html" "status.php"; do
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
echo "   • Quick Start:   http://${HOSTNAME}.local/start/"
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
