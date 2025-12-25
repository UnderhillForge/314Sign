#!/bin/bash
# ====================================================================
# OPTIONAL SECURITY ENHANCEMENT - NOT REQUIRED FOR BASIC SETUP
# ====================================================================
# This script creates a dedicated user for WebDAV write operations.
# 
# WHEN TO USE:
#   - You're exposing the kiosk to the internet (NOT recommended)
#   - You need additional security isolation
#   - You want to audit WebDAV changes separately from web serving
#
# WHEN TO SKIP:
#   - Local network only (typical use case) ✓ RECOMMENDED
#   - Small trusted staff group
#   - Simplicity is preferred
#
# The default setup using www-data is perfectly fine for most cases.
# Only run this if you have specific security requirements.
# ====================================================================

set -e

WEBDAV_USER="pisign"
WEB_ROOT="/var/www/html"

echo "Creating WebDAV user: $WEBDAV_USER"

# Create system user (no login shell, no home directory for security)
if ! id "$WEBDAV_USER" &>/dev/null; then
    sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$WEBDAV_USER"
    echo "Created user: $WEBDAV_USER"
else
    echo "User $WEBDAV_USER already exists"
fi

# Add webdav user to www-data group so it can read web files
sudo usermod -a -G www-data "$WEBDAV_USER"

# Create a shared group for write access (both users can write, but tracked separately)
if ! getent group pisign-writers &>/dev/null; then
    sudo groupadd pisign-writers
    echo "Created group: pisign-writers"
fi

# Add both users to the writers group
# www-data: serves web content and runs PHP
# pisign: handles WebDAV write operations
sudo usermod -a -G pisign-writers www-data
sudo usermod -a -G pisign-writers "$WEBDAV_USER"

echo "Setting up permissions for $WEB_ROOT..."

# Set ownership: www-data owns files, but pisign-writers group can write
sudo chown -R www-data:pisign-writers "$WEB_ROOT"

# Directories readable by web server, writable by group
sudo find "$WEB_ROOT" -type d -exec chmod 775 {} \;

# Files readable by web server, writable by group where needed
sudo find "$WEB_ROOT" -type f -exec chmod 664 {} \;

# Writable directories
sudo chmod 775 "$WEB_ROOT/bg" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/menus" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/logs" 2>/dev/null || true

# Editable files
sudo chmod 664 "$WEB_ROOT/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/config.json" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/rules.json" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/menus/"*.txt 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/edit/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/design/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/rules/index.html" 2>/dev/null || true

# PHP scripts should be executable
sudo chmod 775 "$WEB_ROOT/bg/index.php" 2>/dev/null || true
sudo chmod 775 "$WEB_ROOT/design/upload-bg.php" 2>/dev/null || true

echo ""
echo "WebDAV user setup complete!"
echo ""
echo "User: $WEBDAV_USER (member of pisign-writers group)"
echo "Web files owned by: www-data:pisign-writers"
echo ""
echo "IMPORTANT: This script alone does NOT enable the separate user."
echo "Lighttpd's WebDAV module will still use www-data by default."
echo ""
echo "To fully separate WebDAV operations, you would need to:"
echo "  1. Run WebDAV through a separate process/port"
echo "  2. Use a reverse proxy to route WebDAV requests"
echo "  3. Or use a different WebDAV server (e.g., nginx with DAV)"
echo ""
echo "For most 314Sign installations, this added complexity isn't necessary."
echo "The shared pisign-writers group provides audit capability without"
echo "requiring complex server reconfiguration."
echo ""
