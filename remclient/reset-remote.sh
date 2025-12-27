#!/bin/bash
###############################################################################
# 314Sign Remote Reset Script
#
# Resets a Raspberry Pi back to clean state after remote kiosk installation
# Removes all kiosk-related packages, configs, and files
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/reset-remote.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/reset-remote.sh
#   chmod +x reset-remote.sh
#   sudo ./reset-remote.sh
###############################################################################

set -e

echo "=== 314Sign Remote Reset ==="
echo "This will remove all kiosk-related packages and configurations."
echo ""
echo "WARNING: This will:"
echo "  - Stop and remove kiosk services"
echo "  - Remove lighttpd, X server, Chromium"
echo "  - Delete web files in /var/www/html"
echo "  - Reset hostname and network settings"
echo "  - Remove kiosk user configurations"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Reset cancelled."
    exit 1
fi

echo ""
echo "Starting reset process..."

# Stop kiosk-related services
echo "Stopping services..."
sudo systemctl stop lighttpd 2>/dev/null || true
sudo systemctl disable lighttpd 2>/dev/null || true

# Remove packages
echo "Removing packages..."
sudo apt remove -y lighttpd php-cgi 2>/dev/null || true
sudo apt remove -y xserver-xorg xinit openbox unclutter chromium chromium-browser 2>/dev/null || true
sudo apt autoremove -y

# Remove web files
echo "Removing web files..."
sudo rm -rf /var/www/html/*

# Reset hostname
echo "Resetting hostname..."
if [ -f /etc/hostname ]; then
    sudo sed -i 's/remote-.*/raspberrypi/' /etc/hostname
fi
if [ -f /etc/hosts ]; then
    sudo sed -i '/remote-/d' /etc/hosts
fi

# Remove kiosk user configs
echo "Removing kiosk configurations..."
sudo rm -rf /home/pi/.config/openbox
sudo rm -f /home/pi/.xinitrc
sudo rm -f /home/pi/.bash_profile
sudo rm -rf /home/pi/.local/share/xorg

# Reset boot config (remove kiosk settings)
echo "Resetting boot configuration..."
if [ -f /boot/firmware/config.txt ]; then
    sudo sed -i '/display_hdmi_rotate/d' /boot/firmware/config.txt
    sudo sed -i '/gpu_mem=/d' /boot/firmware/config.txt
    sudo sed -i '/hdmi_force_hotplug/d' /boot/firmware/config.txt
    sudo sed -i '/hdmi_group/d' /boot/firmware/config.txt
    sudo sed -i '/hdmi_mode/d' /boot/firmware/config.txt
fi

# Remove X11 configs
echo "Removing X11 configurations..."
sudo rm -f /etc/X11/xorg.conf.d/99-v3d.conf

# Clean package cache
echo "Cleaning package cache..."
sudo apt clean
sudo apt autoclean

echo ""
echo "✅ Reset complete!"
echo ""
echo "The Raspberry Pi has been reset to pre-kiosk state."
echo "To reinstall, run:"
echo "  curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/remote-setup.sh | sudo bash"
echo ""
echo "Reboot recommended: sudo reboot"
