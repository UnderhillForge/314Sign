#!/bin/bash
set -e  # Exit on any error

echo "Installing PiSign from GitHub..."

# === 1. Install required packages ===
sudo apt update
sudo apt install -y lighttpd php-cgi git qrencode inotify-tools xdotool

# Enable PHP
sudo lighty-enable-mod fastcgi
sudo lighty-enable-mod fastcgi-php

# === 2. Clone PiSign from GitHub ===
TEMP_DIR=$(mktemp -d)
echo "Cloning PiSign into $TEMP_DIR..."
git clone --depth 1 https://github.com/UnderhillForge/PiSign.git "$TEMP_DIR/PiSign"

# === 3. Copy files to web root ===
sudo rsync -av --delete "$TEMP_DIR/PiSign/web/" /var/www/html/

# === 4. Set ownership & permissions ===
sudo chown -R www-data:www-data /var/www/html
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;
sudo chmod 775 /var/www/html/bg
sudo chmod 664 /var/www/html/specials.txt /var/www/html/config.json 2>/dev/null || true

# === 5. Configure lighttpd ===
LIGHTTPD_CONF="/etc/lighttpd/lighttpd.conf"
WEBDAV_CONF="/etc/lighttpd/conf-enabled/10-webdav.conf"

# Enable ETag
if ! grep -q "server.etag" "$LIGHTTPD_CONF"; then
  echo 'server.etag = "enable"' | sudo tee -a "$LIGHTTPD_CONF"
fi

# WebDAV: only allow safe files
sudo tee "$WEBDAV_CONF" > /dev/null << 'EOF'
server.modules += ( "mod_webdav" )

$HTTP["url"] =~ "^/(index\.html|config\.json|specials\.txt)$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}
EOF

# === 6. Generate QR codes ===
cd /var/www/html
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://raspberrypi.local/edit.html"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://raspberrypi.local/design.html"

# === 7. Restart services ===
sudo systemctl restart lighttpd

# === 8. Cleanup ===
rm -rf "$TEMP_DIR"

echo ""
echo "PiSign installed successfully!"
echo ""
echo "Open in browser:"
echo "   http://raspberrypi.local"
echo ""
echo "Staff Editors:"
echo "   • Menu: http://raspberrypi.local/edit.html"
echo "   • Design: http://raspberrypi.local/design.html"
echo ""
echo "Print QR codes from /var/www/html/qr-*.png"
echo ""
