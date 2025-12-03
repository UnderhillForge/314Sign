#!/bin/bash
###############################################################################
# 314Sign Kiosk Mode Setup for Raspberry Pi OS Lite (Optional)
# 
# Sets up lightweight X11 + Chromium kiosk on Raspberry Pi OS Lite
# Only needed if you want the Pi to auto-display the kiosk on boot
# 
# This installs:
#   - Minimal X11 server (no full desktop)
#   - Openbox window manager (super lightweight)
#   - Chromium browser in kiosk mode
#   - Auto-start configuration
#
# Usage (after running main setup-kiosk.sh):
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash
#
# Or if already cloned:
#   sudo /var/www/html/scripts/os-lite-kiosk.sh
#
# After running, Pi will boot directly to fullscreen kiosk display
###############################################################################

set -e

echo "=== 314Sign Kiosk Mode Setup ==="
echo ""
echo "This will configure your Pi to boot directly into fullscreen kiosk mode."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Detect hostname for kiosk URL
HOSTNAME=$(hostname)
KIOSK_URL="http://${HOSTNAME}.local/index.html"

echo "Installing minimal X11 and Chromium..."
sudo apt update
sudo apt install -y \
  xserver-xorg \
  xinit \
  openbox \
  unclutter

# Try chromium first (newer), fallback to chromium-browser (older)
if sudo apt install -y chromium 2>/dev/null; then
  echo "Installed: chromium"
  CHROMIUM_CMD="chromium"
elif sudo apt install -y chromium-browser 2>/dev/null; then
  echo "Installed: chromium-browser"
  CHROMIUM_CMD="chromium-browser"
else
  echo "Error: Neither 'chromium' nor 'chromium-browser' package found"
  exit 1
fi

echo "Configuring auto-login..."
# Enable auto-login to console
sudo raspi-config nonint do_boot_behaviour B2

echo "Creating kiosk startup script..."
mkdir -p ~/.config/openbox

cat > ~/.config/openbox/autostart <<EOF
# Disable screen blanking
xset s off
xset s noblank
xset -dpms

# Hide mouse cursor after 1 second
unclutter -idle 1 -root &

# Start Chromium in kiosk mode (use detected command)
${CHROMIUM_CMD} \\
  --kiosk \\
  --noerrdialogs \\
  --disable-infobars \\
  --disable-session-crashed-bubble \\
  --disable-translate \\
  --check-for-update-interval=31536000 \\
  --app=${KIOSK_URL}
EOF

echo "Setting up X11 auto-start..."
cat > ~/.bash_profile <<'EOF'
# Auto-start X11 on login (console only)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx -- -nocursor
fi
EOF

echo ""
echo "✅ Kiosk mode configured!"
echo ""
echo "The Pi will now boot directly to fullscreen display at:"
echo "   ${KIOSK_URL}"
echo ""
echo "To make this take effect:"
echo "   sudo reboot"
echo ""
echo "To disable kiosk mode later:"
echo "   sudo raspi-config → Boot Options → Desktop/CLI → Console"
echo "   rm ~/.bash_profile ~/.config/openbox/autostart"
echo ""
