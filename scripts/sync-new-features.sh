#!/bin/bash
# Quick sync script to copy slideshow and demo directories to /var/www/html
# This version downloads directly from GitHub

set -e

echo "================================"
echo "314Sign - Sync New Features"
echo "================================"
echo ""

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
  echo "Please run WITHOUT sudo (script will prompt when needed)"
  exit 1
fi

WEB_ROOT="/var/www/html"
TEMP_DIR="/tmp/314sign-sync-$$"
GITHUB_RAW="https://raw.githubusercontent.com/UnderhillForge/314Sign/main"

echo "Web root: $WEB_ROOT"
echo "Temp dir: $TEMP_DIR"
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Download slideshow files
echo "Downloading slideshow files..."
mkdir -p slideshows/sets
curl -sL "$GITHUB_RAW/slideshows/index.html" -o slideshows/index.html
curl -sL "$GITHUB_RAW/slideshows/upload-media.php" -o slideshows/upload-media.php
curl -sL "$GITHUB_RAW/slideshows/sets/example.json" -o slideshows/sets/example.json 2>/dev/null || true

# Download demo files
echo "Downloading demo files..."
mkdir -p demo
curl -sL "$GITHUB_RAW/demo/index.html" -o demo/index.html

# Download updated index.html
echo "Downloading main index.html..."
curl -sL "$GITHUB_RAW/index.html" -o index.html

# Download demo-command.txt template
echo "Downloading demo-command.txt..."
echo "idle" > demo-command.txt

echo ""
echo "Files downloaded. Installing..."

# Copy slideshow directory
echo "Installing slideshows/..."
sudo mkdir -p "$WEB_ROOT/slideshows/media"
sudo mkdir -p "$WEB_ROOT/slideshows/sets"
sudo cp slideshows/index.html "$WEB_ROOT/slideshows/"
sudo cp slideshows/upload-media.php "$WEB_ROOT/slideshows/"
if [ -f slideshows/sets/example.json ]; then
  sudo cp slideshows/sets/example.json "$WEB_ROOT/slideshows/sets/"
fi
echo "✓ Slideshows installed"

# Copy demo directory
echo "Installing demo/..."
sudo mkdir -p "$WEB_ROOT/demo"
sudo cp demo/index.html "$WEB_ROOT/demo/"
echo "✓ Demo installed"

# Copy demo-command.txt if it doesn't exist
if [ ! -f "$WEB_ROOT/demo-command.txt" ]; then
  sudo cp demo-command.txt "$WEB_ROOT/demo-command.txt"
  echo "✓ Created demo-command.txt"
fi

# Copy updated index.html
echo "Updating main index.html..."
sudo cp index.html "$WEB_ROOT/index.html"
echo "✓ Main kiosk display updated"

# Set permissions
echo ""
echo "Setting permissions..."
sudo chown -R www-data:www-data "$WEB_ROOT/slideshows"
sudo chown -R www-data:www-data "$WEB_ROOT/demo"
sudo chmod 775 "$WEB_ROOT/slideshows/media"
sudo chmod 775 "$WEB_ROOT/slideshows/sets"
sudo chmod 664 "$WEB_ROOT/slideshows/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/demo/index.html" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/demo-command.txt" 2>/dev/null || true
sudo chmod 664 "$WEB_ROOT/index.html" 2>/dev/null || true

echo "✓ Permissions set"

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "================================"
echo "Sync Complete!"
echo "================================"
echo ""
echo "New features available:"
echo "  • Slideshows: http://$(hostname).local/slideshows/"
echo "  • Demo Control: http://$(hostname).local/demo/"
echo ""
echo "Note: You may need to update WebDAV config"
echo "Run: sudo nano /etc/lighttpd/conf-enabled/10-webdav.conf"
echo "Add demo-command.txt to the first regex pattern"
echo ""
echo "Then restart lighttpd: sudo systemctl restart lighttpd"
echo ""
