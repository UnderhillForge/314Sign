#!/bin/bash
set -e  # Exit on any error

echo "Installing 314Sign from GitHub..."

# === 1. Install required packages ===
sudo apt update
sudo apt install -y lighttpd php-cgi git qrencode inotify-tools xdotool

# Enable PHP and WebDAV
sudo lighty-enable-mod fastcgi
sudo lighty-enable-mod fastcgi-php
sudo lighty-enable-mod webdav

# === 2. Clone 314Sign from GitHub ===
TEMP_DIR=$(mktemp -d)
echo "Cloning 314Sign into $TEMP_DIR..."
git clone --depth 1 https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign"

# === 3. Copy files to web root ===
echo "Copying files to /var/www/html..."
sudo rsync -av --delete \
  --exclude='.git' \
  --exclude='*.md' \
  --exclude='permissions.sh' \
  --exclude='setup-kiosk.sh' \
  "$TEMP_DIR/314Sign/" /var/www/html/

# === 4. Create required directories ===
sudo mkdir -p /var/www/html/logs
sudo mkdir -p /var/www/html/bg
sudo mkdir -p /var/www/html/menus

# === 5. Set ownership & permissions ===
echo "Setting permissions..."
# Copy permissions script to temp location and run it
cp "$TEMP_DIR/314Sign/permissions.sh" /tmp/314sign-permissions.sh
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
cd /var/www/html
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://raspberrypi.local/edit/"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://raspberrypi.local/design/"
[ ! -f qr-rules.png ] && qrencode -o qr-rules.png -s 10 "http://raspberrypi.local/rules/"

# === 8. Restart services ===
sudo systemctl restart lighttpd

# === 9. Cleanup ===
rm -rf "$TEMP_DIR"

echo ""
echo "314Sign installed successfully!"
echo ""
echo "Open in browser:"
echo "   http://raspberrypi.local"
echo ""
echo "Staff Editors:"
echo "   • Menu: http://raspberrypi.local/edit/"
echo "   • Design: http://raspberrypi.local/design/"
echo "   • Schedule: http://raspberrypi.local/rules/"
echo ""
echo "Print QR codes from /var/www/html/qr-*.png"
echo ""
