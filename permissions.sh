#!/bin/bash
# Set correct permissions for 314Sign files
# Can be run standalone or called from setup-kiosk.sh

WEB_ROOT="${1:-/var/www/html}"

echo "Setting permissions for 314Sign in $WEB_ROOT..."

# Ensure web root exists
if [ ! -d "$WEB_ROOT" ]; then
    echo "Error: $WEB_ROOT does not exist"
    exit 1
fi

# Set base ownership
sudo chown -R www-data:www-data "$WEB_ROOT"

# Set base permissions for all directories and files
sudo find "$WEB_ROOT" -type d -exec chmod 755 {} \;
sudo find "$WEB_ROOT" -type f -exec chmod 644 {} \;

# Writable directories (need to accept uploads/writes)
sudo chmod 775 "$WEB_ROOT/bg" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/menus" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/logs" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/history" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/slideshows/media" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/slideshows/sets" 2>/dev/null || true

# Editable files (need WebDAV write access)
sudo chmod 664 "$WEB_ROOT/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/config.json" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/rules.json" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/menus-config.json" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/reload.txt" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/demo-command.txt" 2>/dev/null || true

# Menu files
sudo chmod 664 "$WEB_ROOT/menus/breakfast.txt" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/menus/lunch.txt" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/menus/dinner.txt" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/menus/closed.txt" 2>/dev/null || true

# Editor pages
sudo chmod 664 "$WEB_ROOT/edit/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/design/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/rules/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/slideshows/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/maintenance/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/start/index.html" 2>/dev/null || true

# PHP scripts should be executable
sudo chmod 755 "$WEB_ROOT/bg/index.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/design/upload-bg.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/design/purge-history.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/status.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/check-updates.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/apply-updates.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/restart-server.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/create-backup.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/trigger-reload.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/save-menu-history.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/get-menu-history.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/fonts/index.php" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/slideshows/upload-media.php" 2>/dev/null || true

# Set permissions for fonts directory (needs to be writable for uploads)
if [ -d "$WEB_ROOT/fonts" ]; then
  sudo chown www-data:www-data "$WEB_ROOT/fonts"
  sudo chmod 775 "$WEB_ROOT/fonts"
  sudo find "$WEB_ROOT/fonts" -type f -name "*.ttf" -exec chmod 644 {} \;
fi

# Make all scripts in scripts/ directory executable
if [ -d "$WEB_ROOT/scripts" ]; then
  sudo find "$WEB_ROOT/scripts" -type f -name "*.sh" -exec chmod 755 {} \;
fi

# Make setup scripts in root executable
sudo chmod 755 "$WEB_ROOT/setup-kiosk.sh" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/permissions.sh" 2>/dev/null || true
sudo chmod 755 "$WEB_ROOT/create-webdav-user.sh" 2>/dev/null || true

echo "Permissions set successfully!"
