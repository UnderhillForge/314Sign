#!/bin/bash
# Quick sync script to copy slideshow and demo directories to /var/www/html

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

# Get the script's directory (should be in scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Repository: $REPO_ROOT"
echo "Web root: $WEB_ROOT"
echo ""

# Copy slideshow directory
echo "Copying slideshows/..."
sudo mkdir -p "$WEB_ROOT/slideshows/media"
sudo mkdir -p "$WEB_ROOT/slideshows/sets"
sudo cp "$REPO_ROOT/slideshows/index.html" "$WEB_ROOT/slideshows/" 2>/dev/null || true
sudo cp "$REPO_ROOT/slideshows/upload-media.php" "$WEB_ROOT/slideshows/" 2>/dev/null || true

# Copy example slideshow if it exists
if [ -f "$REPO_ROOT/slideshows/sets/example.json" ]; then
  sudo cp "$REPO_ROOT/slideshows/sets/example.json" "$WEB_ROOT/slideshows/sets/"
fi

echo "✓ Slideshows directory synced"

# Copy demo directory
echo "Copying demo/..."
sudo mkdir -p "$WEB_ROOT/demo"
sudo cp "$REPO_ROOT/demo/index.html" "$WEB_ROOT/demo/"
echo "✓ Demo directory synced"

# Copy demo-command.txt if it doesn't exist
if [ ! -f "$WEB_ROOT/demo-command.txt" ]; then
  echo "idle" | sudo tee "$WEB_ROOT/demo-command.txt" > /dev/null
  echo "✓ Created demo-command.txt"
fi

# Copy updated index.html (has demo polling code)
echo "Updating main index.html..."
sudo cp "$REPO_ROOT/index.html" "$WEB_ROOT/"
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

echo ""
echo "================================"
echo "Sync Complete!"
echo "================================"
echo ""
echo "New features available:"
echo "  • Slideshows: http://$(hostname).local/slideshows/"
echo "  • Demo Control: http://$(hostname).local/demo/"
echo ""
echo "Note: You may need to update WebDAV config in lighttpd"
echo "Run the full setup-kiosk.sh to update WebDAV settings"
echo ""
