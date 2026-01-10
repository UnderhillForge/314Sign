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
echo "Script starting at $(date)"
echo "Running as user: $(whoami)"
echo "SUDO_USER: ${SUDO_USER:-not set}"
echo ""

# Detect the correct user (not root when run with sudo)
if [ "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
  TARGET_USER="$SUDO_USER"
  TARGET_HOME=$(eval echo ~$SUDO_USER)
elif [ "$(whoami)" = "root" ]; then
  # Running as root, try to find the correct user
  # Check for common users on Raspberry Pi
  for user in pi raspberry; do
    if id "$user" >/dev/null 2>&1 && [ -d "/home/$user" ]; then
      TARGET_USER="$user"
      TARGET_HOME="/home/$user"
      break
    fi
  done
  # If no common user found, look for any non-root user with a home directory
  if [ -z "$TARGET_USER" ]; then
    for user in $(ls /home 2>/dev/null); do
      if [ "$user" != "root" ] && id "$user" >/dev/null 2>&1; then
        TARGET_USER="$user"
        TARGET_HOME="/home/$user"
        break
      fi
    done
  fi
  # If still no user found, use pi as default (create home if needed)
  if [ -z "$TARGET_USER" ]; then
    TARGET_USER="pi"
    TARGET_HOME="/home/pi"
    if [ ! -d "/home/pi" ]; then
      echo "Creating home directory for user pi..."
      sudo mkdir -p /home/pi
      sudo chown pi:pi /home/pi 2>/dev/null || true
    fi
  fi
else
  TARGET_USER=$(whoami)
  TARGET_HOME=$HOME
fi

echo "Setting up kiosk for user: $TARGET_USER (home: $TARGET_HOME)"
echo "Current user running script: $(whoami)"
echo "SUDO_USER: ${SUDO_USER:-none}"

# Check if already configured
if [ -f "$TARGET_HOME/.config/openbox/autostart" ]; then
  echo "⚠️  Kiosk mode already configured."
  echo "This will update rotation and browser settings."
  echo ""
fi

echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Detect hostname for kiosk URL
HOSTNAME=$(hostname)
KIOSK_URL="http://localhost/index.html"

# Ask about screen rotation
echo ""
echo "Screen Orientation:"
echo "  0 = Normal (landscape)"
echo "  1 = 90° clockwise (portrait)"
echo "  2 = 180° (upside down)"
echo "  3 = 270° clockwise (portrait, other direction)"
echo ""
read -p "Enter rotation for HDMI-1 (0-3) [default: 0]: " ROTATION_HDMI1
ROTATION_HDMI1=${ROTATION_HDMI1:-0}

read -p "Enter rotation for HDMI-2 (0-3) [default: 0]: " ROTATION_HDMI2
ROTATION_HDMI2=${ROTATION_HDMI2:-0}

# Validate input
if ! [[ "$ROTATION_HDMI1" =~ ^[0-3]$ ]]; then
  echo "Invalid HDMI-1 rotation. Using 0 (normal)."
  ROTATION_HDMI1=0
fi

if ! [[ "$ROTATION_HDMI2" =~ ^[0-3]$ ]]; then
  echo "Invalid HDMI-2 rotation. Using 0 (normal)."
  ROTATION_HDMI2=0
fi

echo "HDMI-1 rotation: $ROTATION_HDMI1"
echo "HDMI-2 rotation: $ROTATION_HDMI2"

echo "Setting screen rotation to: $ROTATION"

# Check if packages already installed
echo "Checking installed packages..."
NEED_INSTALL=false
echo "Checking for packages: xserver-xorg xinit openbox unclutter"
for pkg in xserver-xorg xinit openbox unclutter; do
  echo "Checking package: $pkg"
  if ! dpkg -l | grep -q "^ii  $pkg "; then
    echo "Package $pkg not found, will install"
    NEED_INSTALL=true
    break
  else
    echo "Package $pkg already installed"
  fi
done
echo "NEED_INSTALL=$NEED_INSTALL"

if [ "$NEED_INSTALL" = true ]; then
  echo "Installing minimal X11 and web browser..."
  if ! sudo apt update; then
    echo "Warning: apt update failed, trying to continue..."
  fi
  if ! sudo apt install -y \
    xserver-xorg \
    xinit \
    openbox \
    unclutter; then
    echo "ERROR: Failed to install required packages"
    echo "Please check your internet connection and package repositories"
    exit 1
  fi
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
  if ! sudo apt install -y chromium; then
    echo "ERROR: Failed to install chromium"
    exit 1
  fi
  CHROMIUM_CMD="chromium"
elif apt-cache show chromium-browser >/dev/null 2>&1; then
  echo "Installing chromium-browser..."
  if ! sudo apt install -y chromium-browser; then
    echo "ERROR: Failed to install chromium-browser"
    exit 1
  fi
  CHROMIUM_CMD="chromium-browser"
elif apt-cache show firefox-esr >/dev/null 2>&1; then
  echo "Chromium not available, installing Firefox ESR as fallback..."
  if ! sudo apt install -y firefox-esr; then
    echo "ERROR: Failed to install firefox-esr"
    exit 1
  fi
  CHROMIUM_CMD="firefox-esr"
else
  echo "Error: No suitable browser found (tried chromium, chromium-browser, firefox-esr)"
  echo "Please install a browser manually: sudo apt install chromium"
  exit 1
fi

echo "Installed browser: ${CHROMIUM_CMD}"

echo "Configuring auto-login..."
# Enable auto-login to console
echo "Running: sudo raspi-config nonint do_boot_behaviour B2"
sudo raspi-config nonint do_boot_behaviour B2
echo "Checking boot behavior after config:"
BOOT_RESULT=$(sudo raspi-config nonint get_boot_cli)
echo "Boot CLI result: $BOOT_RESULT"
if [ "$BOOT_RESULT" != "1" ]; then
  echo "Warning: Auto-login may not be configured correctly (expected 1, got $BOOT_RESULT)"
  echo "Trying alternative: setting up systemd service for autologin..."
  # Alternative: create systemd service for autologin
  sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
  sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $TARGET_USER --noclear %I \$TERM
EOF
  sudo systemctl daemon-reload
  sudo systemctl enable getty@tty1.service
  echo "Systemd autologin service created for user $TARGET_USER"
fi

echo "About to create kiosk configuration files..."
echo "TARGET_USER: $TARGET_USER"
echo "TARGET_HOME: $TARGET_HOME"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Testing write permissions to TARGET_HOME..."
if touch "$TARGET_HOME/test_write_permissions.tmp" 2>/dev/null; then
  rm "$TARGET_HOME/test_write_permissions.tmp" 2>/dev/null
  echo "Write test: SUCCESS - can write to $TARGET_HOME"
else
  echo "Write test: FAILED - cannot write to $TARGET_HOME"
  echo "This will prevent kiosk file creation!"
  exit 1
fi

echo "Creating kiosk startup script..."
echo "Target directory: $TARGET_HOME/.config/openbox"
echo "Current working directory: $(pwd)"
echo "TARGET_HOME exists: $(ls -ld "$TARGET_HOME" 2>/dev/null || echo "NO")"
echo "Creating directory..."
mkdir -p "$TARGET_HOME/.config/openbox"
DIR_CREATE_RESULT=$?
echo "mkdir result: $DIR_CREATE_RESULT"
echo "Directory created, listing contents:"
ls -la "$TARGET_HOME/.config/" 2>/dev/null || echo "Parent directory doesn't exist or is not accessible: $TARGET_HOME/.config"
ls -la "$TARGET_HOME/.config/openbox/" 2>/dev/null || echo "Openbox directory not accessible: $TARGET_HOME/.config/openbox"

cat > "$TARGET_HOME/.config/openbox/autostart" <<EOF
# Disable screen blanking
xset s off
xset s noblank
xset -dpms

# Set screen rotation
xrandr --output HDMI-1 --rotate $(case $ROTATION_HDMI1 in 0) echo "normal";; 1) echo "right";; 2) echo "inverted";; 3) echo "left";; esac) 2>/dev/null || true
xrandr --output HDMI-2 --rotate $(case $ROTATION_HDMI2 in 0) echo "normal";; 1) echo "right";; 2) echo "inverted";; 3) echo "left";; esac) 2>/dev/null || true

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
    --remote-debugging-port=9222 \\
    --remote-debugging-address=0.0.0.0 \\
    --no-sandbox \\
    --disable-dev-shm-usage \\
    --noerrdialogs \\
    --disable-infobars \\
    --disable-session-crashed-bubble \\
    --disable-translate \\
    --check-for-update-interval=31536000 \\
    ${KIOSK_URL}
fi
EOF

CAT_RESULT=$?
echo "cat command result: $CAT_RESULT"
echo "Autostart file created, checking:"
ls -la "$TARGET_HOME/.config/openbox/autostart" 2>/dev/null || echo "Autostart file not found! Path: $TARGET_HOME/.config/openbox/autostart"

echo "Configuring display rotation in boot config..."
# Set display rotation in /boot/firmware/config.txt or /boot/config.txt
BOOT_CONFIG="/boot/firmware/config.txt"
[ ! -f "$BOOT_CONFIG" ] && BOOT_CONFIG="/boot/config.txt"

if [ -f "$BOOT_CONFIG" ]; then
  # Remove any existing display_rotate or display_hdmi_rotate settings
  sudo sed -i '/^display_rotate=/d' "$BOOT_CONFIG"
  sudo sed -i '/^display_hdmi_rotate=/d' "$BOOT_CONFIG"
  # Add new rotation settings for each HDMI port
  echo "display_hdmi_rotate:0=$ROTATION_HDMI1" | sudo tee -a "$BOOT_CONFIG" > /dev/null
  echo "display_hdmi_rotate:1=$ROTATION_HDMI2" | sudo tee -a "$BOOT_CONFIG" > /dev/null
  echo "Display rotation set in $BOOT_CONFIG (HDMI-1: $ROTATION_HDMI1, HDMI-2: $ROTATION_HDMI2)"
else
  echo "Warning: Boot config not found, skipping console rotation"
fi

# Detect Raspberry Pi model for GPU driver selection
echo "Detecting Raspberry Pi model for GPU driver configuration..."
PI_MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null | grep -o "Raspberry Pi [0-9]" | grep -o "[0-9]" || echo "unknown")

if [ "$PI_MODEL" = "5" ]; then
  GPU_DRIVER="fbdev"
  GPU_DEVICE="/dev/fb0"
  echo "✓ Detected Raspberry Pi 5 - using fbdev driver"
elif [ "$PI_MODEL" = "4" ] || [ "$PI_MODEL" = "3" ] || [ "$PI_MODEL" = "2" ] || [ "$PI_MODEL" = "1" ]; then
  GPU_DRIVER="vc4"
  GPU_DEVICE="/dev/dri/card0"
  echo "✓ Detected Raspberry Pi $PI_MODEL - using vc4 driver"
else
  GPU_DRIVER="modesetting"
  GPU_DEVICE="/dev/dri/card0"
  echo "⚠️  Could not detect Pi model (got: $PI_MODEL) - using generic modesetting driver"
fi

echo "Configuring X11 to use $GPU_DRIVER driver..."
sudo mkdir -p /etc/X11/xorg.conf.d

# Map display_rotate values to X11 rotation names for each port
case "$ROTATION_HDMI1" in
  0) XROTATE_HDMI1="normal" ;;
  1) XROTATE_HDMI1="left" ;;
  2) XROTATE_HDMI1="inverted" ;;
  3) XROTATE_HDMI1="right" ;;
  *) XROTATE_HDMI1="normal" ;;
esac

case "$ROTATION_HDMI2" in
  0) XROTATE_HDMI2="normal" ;;
  1) XROTATE_HDMI2="left" ;;
  2) XROTATE_HDMI2="inverted" ;;
  3) XROTATE_HDMI2="right" ;;
  *) XROTATE_HDMI2="normal" ;;
esac

if [ "$GPU_DRIVER" = "fbdev" ]; then
  # fbdev driver configuration
  sudo tee /etc/X11/xorg.conf.d/99-gpu.conf > /dev/null <<XCONF
Section "Device"
  Identifier "Raspberry Pi FB"
  Driver "fbdev"
  Option "fbdev" "$GPU_DEVICE"
EndSection

Section "Screen"
  Identifier "Default Screen"
  Device "Raspberry Pi FB"
EndSection
XCONF
else
  # KMS driver configuration (vc4/modesetting)
  sudo tee /etc/X11/xorg.conf.d/99-gpu.conf > /dev/null <<XCONF
Section "ServerFlags"
  Option "AutoAddGPU" "false"
EndSection

Section "Device"
  Identifier "$GPU_DRIVER"
  Driver "$GPU_DRIVER"
  Option "kmsdev" "$GPU_DEVICE"
  BusID "platform:axi:gpu"
EndSection

Section "Monitor"
  Identifier "HDMI-1"
  Option "Rotate" "$XROTATE_HDMI1"
EndSection

Section "Monitor"
  Identifier "HDMI-2"
  Option "Rotate" "$XROTATE_HDMI2"
EndSection

Section "Screen"
  Identifier "Default Screen"
  Device "$GPU_DRIVER"
  Monitor "HDMI-1"
EndSection
XCONF
fi

echo "Setting up X11 auto-start..."
cat > "$TARGET_HOME/.xinitrc" <<'EOF'
#!/bin/sh
# Start openbox window manager
exec openbox-session
EOF

echo "xinitrc file created, checking:"
ls -la "$TARGET_HOME/.xinitrc" 2>/dev/null || echo "xinitrc file not found!"

cat > "$TARGET_HOME/.bash_profile" <<'EOF'
# Auto-start X11 on login (console only)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx -- -nocursor
fi
EOF

echo "bash_profile file created, checking:"
ls -la "$TARGET_HOME/.bash_profile" 2>/dev/null || echo "bash_profile file not found!"

chmod +x "$TARGET_HOME/.xinitrc"

# Set correct ownership
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.config"
chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.xinitrc"
chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.bash_profile"

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
echo "   sudo rm -rf $TARGET_HOME/.bash_profile $TARGET_HOME/.xinitrc $TARGET_HOME/.config/openbox"
echo ""