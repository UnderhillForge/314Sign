#!/bin/bash
###############################################################################
# 314Sign Remote Reset Script for FullPageOS
#
# Resets a FullPageOS system back to clean state after 314Sign remote installation
# Removes web server files and configurations while preserving FullPageOS setup
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/reset-remote.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/reset-remote.sh
#   chmod +x reset-remote.sh
#   sudo ./reset-remote.sh
###############################################################################

echo "=== 314Sign Remote Reset for FullPageOS ==="
echo ""
echo "This will remove 314Sign remote configurations while preserving FullPageOS."
echo ""
echo "WARNING: This will:"
echo "  - Stop lighttpd web server"
echo "  - Remove 314Sign files from /var/www/html"
echo "  - Reset hostname back to default"
echo "  - Reset FullPageOS browser to default"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Reset cancelled."
    exit 1
fi

echo ""
echo "Starting reset process..."

# Stop web server
echo "Stopping web server..."
sudo systemctl stop lighttpd 2>/dev/null || true

# Remove 314Sign web files (preserve any other files)
echo "Removing 314Sign web files..."
sudo rm -f /var/www/html/device.json
sudo rm -f /var/www/html/remote-config.json
sudo rm -f /var/www/html/remote.html
sudo rm -f /var/www/html/remote.js
sudo rm -f /var/www/html/reset-remote.sh
sudo rm -f /var/www/html/update-remote-config.php
sudo rm -rf /var/www/html/cache 2>/dev/null || true
sudo rm -rf /var/www/html/remote-data 2>/dev/null || true

# Reset hostname
echo "Resetting hostname..."
if [ -f /etc/hostname ]; then
    sudo sed -i 's/remote-.*/raspberrypi/' /etc/hostname
fi
if [ -f /etc/hosts ]; then
    sudo sed -i '/remote-/d' /etc/hosts
fi

# Reset FullPageOS browser configuration
echo "Resetting FullPageOS browser..."
if [ -f "/boot/fullpageos.txt" ]; then
    # Clear the file (FullPageOS will use default)
    sudo tee /boot/fullpageos.txt > /dev/null <<EOF
EOF
    echo "FullPageOS browser reset to default"
else
    echo "FullPageOS config file not found"
fi

# Optional: Remove web server packages
echo ""
echo "Remove web server packages (lighttpd/php)? This will completely remove the web server."
read -p "Remove web server packages? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing web server packages..."
    sudo apt remove -y lighttpd php-cgi 2>/dev/null || true
    sudo apt autoremove -y
    sudo apt clean
    sudo apt autoclean
    echo "Web server packages removed"
else
    echo "Keeping web server packages installed"
fi

echo ""
echo "✅ Reset complete!"
echo ""
echo "314Sign remote configurations have been removed."
echo "FullPageOS is restored to default state."
echo ""
echo "To reinstall 314Sign remote:"
echo "  curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/remote-setup.sh | sudo bash"
echo ""
echo "Reboot recommended: sudo reboot"