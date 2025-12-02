#!/bin/bash
set -e  # Exit on any error

echo "Installing 314Sign from GitHub..."

# === 2. Install required packages ===
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
sudo rsync -av --delete "$TEMP_DIR/314Sign/web/" /var/www/html/

# === 4. Set ownership & permissions ===
sudo chown -R www-data:www-data /var/www/html
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;
sudo chmod 775 /var/www/html/bg /var/www/html/menus
sudo chmod 664 /var/www/html/menus/breakfast.txt /var/www/html/menus/lunch.txt /var/www/html/menus/dinner.txt /var/www/html/menus/closed.txt /var/www/html/config.json /var/www/html/rules.json 2>/dev/null || true

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

# === 6. Generate QR codes ===
cd /var/www/html
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://raspberrypi.local/edit/"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://raspberrypi.local/design/"
[ ! -f qr-rules.png ] && qrencode -o qr-rules.png -s 10 "http://raspberrypi.local/rules/"

# === 7. Restart services ===
sudo systemctl restart lighttpd

# === 8. Cleanup ===
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
