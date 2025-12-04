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
#   - Screen rotation configuration
#
# Usage (after running main setup-kiosk.sh):
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash
#
# Or if already cloned:
#   sudo /var/www/html/scripts/os-lite-kiosk.sh
#
# Re-run anytime to change screen rotation - already installed packages will be skipped
# After running, Pi will boot directly to fullscreen kiosk display
###############################################################################

set -e

echo "=== 314Sign Kiosk Mode Setup ==="
echo ""

# Check if already configured
if [ -f ~/.config/openbox/autostart ]; then
  echo "⚠️  Kiosk mode already configured."
  echo "This will update rotation and browser settings."
  echo ""
fi

echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Detect hostname for kiosk URL
HOSTNAME=$(hostname)
KIOSK_URL="http://${HOSTNAME}.local/index.html"

# Ask about screen rotation
echo ""
echo "Screen Orientation:"
echo "  0 = Normal (landscape)"
echo "  1 = 90° clockwise (portrait)"
echo "  2 = 180° (upside down)"
echo "  3 = 270° clockwise (portrait, other direction)"
echo ""
read -p "Enter rotation (0-3) [default: 0]: " ROTATION
ROTATION=${ROTATION:-0}

# Validate input
if ! [[ "$ROTATION" =~ ^[0-3]$ ]]; then
  echo "Invalid rotation. Using 0 (normal)."
  ROTATION=0
fi

echo "Setting screen rotation to: $ROTATION"

# Check if packages already installed
echo "Checking installed packages..."
NEED_INSTALL=false
for pkg in xserver-xorg xinit openbox unclutter; do
  if ! dpkg -l | grep -q "^ii  $pkg "; then
    NEED_INSTALL=true
    break
  fi
done

if [ "$NEED_INSTALL" = true ]; then
  echo "Installing minimal X11 and web browser..."
  sudo apt update
  sudo apt install -y \
    xserver-xorg \
    xinit \
    openbox \
    unclutter
else
  echo "✓ X11 packages already installed, skipping..."
fi

# Detect or install browser
CHROMIUM_CMD=""
if command -v chromium >/dev/null 2>&1; then
  CHROMIUM_CMD="chromium"
  echo "✓ Using installed: chromium"
elif command -v chromium-browser >/dev/null 2>&1; then
  CHROMIUM_CMD="chromium-browser"
  echo "✓ Using installed: chromium-browser"
elif command -v firefox-esr >/dev/null 2>&1; then
  CHROMIUM_CMD="firefox-esr"
  echo "✓ Using installed: firefox-esr"
elif apt-cache show chromium >/dev/null 2>&1; then
  echo "Installing chromium..."
  sudo apt install -y chromium
  CHROMIUM_CMD="chromium"
elif apt-cache show chromium-browser >/dev/null 2>&1; then
  echo "Installing chromium-browser..."
  sudo apt install -y chromium-browser
  CHROMIUM_CMD="chromium-browser"
elif apt-cache show firefox-esr >/dev/null 2>&1; then
  echo "Chromium not available, installing Firefox ESR as fallback..."
  sudo apt install -y firefox-esr
  CHROMIUM_CMD="firefox-esr"
else
  echo "Error: No suitable browser found (tried chromium, chromium-browser, firefox-esr)"
  echo "Please install a browser manually: sudo apt install firefox-esr"
  exit 1
fi

echo "Installed browser: ${CHROMIUM_CMD}"

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

# Set screen rotation
xrandr --output HDMI-1 --rotate $(case $ROTATION in 0) echo "normal";; 1) echo "right";; 2) echo "inverted";; 3) echo "left";; esac) 2>/dev/null || xrandr --output HDMI-2 --rotate $(case $ROTATION in 0) echo "normal";; 1) echo "right";; 2) echo "inverted";; 3) echo "left";; esac) 2>/dev/null || true

# Hide mouse cursor after 1 second
unclutter -idle 1 -root &

# Start browser in kiosk mode (use detected command)
if [[ "${CHROMIUM_CMD}" == "firefox-esr" ]]; then
  # Firefox ESR kiosk mode
  firefox-esr --kiosk ${KIOSK_URL}
else
  # Chromium-based kiosk mode
  ${CHROMIUM_CMD} \\
    --kiosk \\
    --noerrdialogs \\
    --disable-infobars \\
    --disable-session-crashed-bubble \\
    --disable-translate \\
    --check-for-update-interval=31536000 \\
    --app=${KIOSK_URL}
fi
EOF

echo "Configuring display rotation in boot config..."
# Set display rotation in /boot/firmware/config.txt or /boot/config.txt
BOOT_CONFIG="/boot/firmware/config.txt"
[ ! -f "$BOOT_CONFIG" ] && BOOT_CONFIG="/boot/config.txt"

if [ -f "$BOOT_CONFIG" ]; then
  # Remove any existing display_rotate setting
  sudo sed -i '/^display_rotate=/d' "$BOOT_CONFIG"
  # Add new rotation setting
  echo "display_rotate=$ROTATION" | sudo tee -a "$BOOT_CONFIG" > /dev/null
  echo "Display rotation set in $BOOT_CONFIG"
else
  echo "Warning: Boot config not found, skipping console rotation"
fi

echo "Configuring X11 to use correct GPU..."
sudo mkdir -p /etc/X11/xorg.conf.d

# Map display_rotate values to X11 rotation names
# 0 = normal, 1 = 90 degrees (left), 2 = 180 degrees (inverted), 3 = 270 degrees (right)
case "$ROTATION" in
  0) XROTATE="normal" ;;
  1) XROTATE="left" ;;
  2) XROTATE="inverted" ;;
  3) XROTATE="right" ;;
  *) XROTATE="normal" ;;
esac

sudo tee /etc/X11/xorg.conf.d/99-v3d.conf > /dev/null <<XCONF
Section "ServerFlags"
  Option "AutoAddGPU" "false"
EndSection

Section "Device"
  Identifier "vc4"
  Driver "modesetting"
  Option "kmsdev" "/dev/dri/card1"
  BusID "platform:axi:gpu"
EndSection

Section "Monitor"
  Identifier "HDMI-1"
  Option "Rotate" "$XROTATE"
EndSection

Section "Screen"
  Identifier "Default Screen"
  Device "vc4"
  Monitor "HDMI-1"
EndSection
XCONF

echo "Setting up X11 auto-start..."
cat > ~/.xinitrc <<'EOF'
#!/bin/sh
# Start openbox window manager
exec openbox-session
EOF

cat > ~/.bash_profile <<'EOF'
# Auto-start X11 on login (console only)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx -- -nocursor
fi
EOF

chmod +x ~/.xinitrc

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
