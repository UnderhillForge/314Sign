#!/bin/bash
###############################################################################
# 314Sign Remote Kiosk Setup for Raspberry Pi Zero 2 W
#
# Sets up a remote kiosk viewer that connects to a main 314Sign kiosk
# Generates hardware-based unique device ID for registration
# Includes emergency admin panel for troubleshooting
#
# Compatible with:
#   - Raspberry Pi OS Lite 32-bit
#
# Features:
#   - Hardware-based unique device identification
#   - Lightweight remote display client
#   - Emergency admin panel (/emergency-admin)
#   - Orientation selection (vertical/horizontal)
#   - Automatic connection to main kiosk
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remote-setup.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remote-setup.sh
#   chmod +x remote-setup.sh
#   sudo ./remote-setup.sh
###############################################################################

set -e  # Exit on any error

echo "=== 314Sign Remote Kiosk Setup ==="
echo ""

# === 0. Generate Hardware-Based Device ID ===
echo "Generating hardware-based device identifier..."

# Get CPU serial number (unique per Raspberry Pi)
if [ -f /proc/cpuinfo ]; then
  CPU_SERIAL=$(grep "Serial" /proc/cpuinfo | awk '{print $3}' | tr '[:lower:]' '[:upper:]')
  if [ -z "$CPU_SERIAL" ]; then
    echo "ERROR: Could not read CPU serial number"
    echo "This script requires a Raspberry Pi with accessible CPU info"
    exit 1
  fi
else
  echo "ERROR: /proc/cpuinfo not found - not running on Linux?"
  exit 1
fi

echo "CPU Serial: $CPU_SERIAL"

# Generate a 6-character display code from the serial (deterministic but human-friendly)
# Use a simple hash of the serial to create a 6-char code
DISPLAY_CODE=$(echo "$CPU_SERIAL" | md5sum | cut -c1-6 | tr '[:lower:]' '[:upper:]')
echo "Display Code: $DISPLAY_CODE"
echo "This code will be shown on-screen for registration with the main kiosk"
echo ""

# Store both the full serial (for internal use) and display code
DEVICE_SERIAL="$CPU_SERIAL"
DEVICE_CODE="$DISPLAY_CODE"

# === 0b. Set Hostname to Device Identifier ===
echo "Setting hostname to device identifier..."
NEW_HOSTNAME="remote-$DEVICE_CODE"
echo "New hostname: $NEW_HOSTNAME"

# Set hostname using hostnamectl (modern method)
if command -v hostnamectl >/dev/null 2>&1; then
  sudo hostnamectl set-hostname "$NEW_HOSTNAME"
  echo "✓ Hostname set using hostnamectl"
else
  # Fallback to old method
  sudo hostname "$NEW_HOSTNAME"
  echo "$NEW_HOSTNAME" | sudo tee /etc/hostname > /dev/null
  echo "✓ Hostname set using legacy method"
fi

# Update /etc/hosts to include the new hostname
if [ -f /etc/hosts ]; then
  # Remove any existing entries for the current hostname
  CURRENT_HOSTNAME=$(hostname)
  sudo sed -i "/\b${CURRENT_HOSTNAME}\b/d" /etc/hosts
  # Add new hostname entry
  echo "127.0.0.1 localhost $NEW_HOSTNAME" | sudo tee -a /etc/hosts > /dev/null
  echo "✓ Hosts file updated"
fi

echo "Device will be discoverable as: $NEW_HOSTNAME.local"
echo ""

# === 1. Main Kiosk Configuration ===
# NOTE: Main kiosk identifier is not needed during initial setup.
# Remote devices will be registered and configured through the main kiosk's web interface.
# The remote will discover the main kiosk via mDNS/avahi or get configured during registration.

# Commented out for future mDNS auto-discovery implementation:
# echo "Main Kiosk Configuration:"
# echo "Enter a simple identifier for your main 314Sign kiosk (e.g., 'kitchen', 'main', 'dining')"
# echo "This will be used to automatically discover the kiosk on your network."
# read -p "Main kiosk identifier: " MAIN_KIOSK_IDENTIFIER
#
# if [ -z "$MAIN_KIOSK_IDENTIFIER" ]; then
#   echo "ERROR: Main kiosk identifier is required"
#   exit 1
# fi
#
# # Validate identifier (alphanumeric, dashes, underscores only)
# if ! echo "$MAIN_KIOSK_IDENTIFIER" | grep -q "^[a-zA-Z0-9_-]\+$"; then
#   echo "ERROR: Identifier must contain only letters, numbers, dashes, and underscores"
#   exit 1
# fi
#
# # Construct main kiosk URL using mDNS discovery
# MAIN_KIOSK_URL="http://$MAIN_KIOSK_IDENTIFIER.local"
# echo "Main kiosk identifier: $MAIN_KIOSK_IDENTIFIER"
# echo "Will connect to: $MAIN_KIOSK_URL"
# echo ""

# === 2. Orientation Selection ===
# For non-interactive setup, use defaults. Orientation can be configured later via main kiosk.
echo "Screen Orientation:"
echo "  0 = Normal (landscape)"
echo "  1 = 90° clockwise (portrait)"
echo "  2 = 180° (upside down)"
echo "  3 = 270° clockwise (portrait, other direction)"
echo ""

# Check if running interactively
if [ -t 0 ]; then
  # Interactive mode - prompt for input (default to landscape)
  read -p "Enter rotation for HDMI (0-3) [default: 0]: " ROTATION_HDMI1
  ROTATION_HDMI1=${ROTATION_HDMI1:-0}
else
  # Non-interactive mode - use portrait default for automated setup
  echo "Non-interactive mode detected, using portrait orientation for remotes..."
  ROTATION_HDMI1=3
fi

# Validate input
if ! [[ "$ROTATION_HDMI1" =~ ^[0-3]$ ]]; then
  echo "Invalid HDMI rotation. Using 0 (normal)."
  ROTATION_HDMI1=0
fi

echo "HDMI rotation: $ROTATION_HDMI1"
echo ""

# === 3. Install required packages ===
echo "Installing packages..."
sudo apt update

# Install lighttpd for lightweight static file serving
echo "Installing lighttpd..."
sudo apt install -y lighttpd php-cgi

# Verify lighttpd installation
if ! command -v lighttpd >/dev/null 2>&1; then
  echo "ERROR: lighttpd installation failed"
  exit 1
fi

echo "✓ lighttpd installed"

# Install additional packages
sudo apt install -y git qrencode avahi-daemon wget curl jq

# Optional packages (needed for kiosk automation features, skip on headless systems)
echo "Installing optional packages..."
sudo apt install -y inotify-tools xdotool 2>/dev/null || echo "Note: Some optional packages unavailable (normal for headless systems)"

# === 4. Clone 314Sign from GitHub ===
TEMP_DIR=$(mktemp -d)
echo "Cloning 314Sign into $TEMP_DIR..."
echo "Temp directory: $TEMP_DIR"

# Test internet connectivity first
if ! ping -c 1 github.com >/dev/null 2>&1; then
  echo "ERROR: Cannot reach github.com - check internet connection"
  echo "Try: ping github.com"
  exit 1
fi

# Clone repository with minimal sparse checkout (only essential files)
echo "Using sparse checkout to download only essential files..."
if ! git clone --depth 1 --filter=tree:0 --sparse https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign" 2>&1; then
  echo "Sparse checkout failed, trying alternative method..."
  # Fallback: Clone and remove unnecessary files
  if ! git clone --depth 1 https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign" 2>&1; then
    echo ""
    echo "ERROR: Git clone failed!"
    echo "Troubleshooting:"
    echo "  1. Check internet connection: ping github.com"
    echo "  2. Verify git is installed: git --version"
    echo "  3. Try manual clone: git clone https://github.com/UnderhillForge/314Sign.git"
    echo "  4. Check disk space: df -h"
    rm -rf "$TEMP_DIR"
    exit 1
  fi
else
  # Configure sparse checkout to only include essential directories
  cd "$TEMP_DIR/314Sign"
  git sparse-checkout add remclient/
  git sparse-checkout add scripts/
  git sparse-checkout add docs/
  cd - >/dev/null
fi

echo ""
echo "Clone successful. Checking contents..."
if [ ! -d "$TEMP_DIR/314Sign" ]; then
  echo "ERROR: Clone directory not created at $TEMP_DIR/314Sign"
  ls -la "$TEMP_DIR/"
  exit 1
fi

FILE_COUNT=$(find "$TEMP_DIR/314Sign" -type f | wc -l)
echo "Found $FILE_COUNT files in repository"
ls -la "$TEMP_DIR/314Sign/" | head -20

if [ "$FILE_COUNT" -lt 10 ]; then
  echo "WARNING: Very few files found - clone may be incomplete"
fi

# === 5. Copy files to web root ===
echo ""
echo "Copying files to /var/www/html..."

# Ensure web root exists
if [ ! -d "/var/www/html" ]; then
  echo "Creating /var/www/html directory..."
  sudo mkdir -p /var/www/html
fi

# Copy remote client files to web root
echo "Copying remote client files..."
if ! sudo cp -r "$TEMP_DIR/314Sign/remclient/"* /var/www/html/ 2>&1; then
  echo "ERROR: Failed to copy remote client files!"
  exit 1
fi

# Copy scripts for permissions setup
if [ -d "$TEMP_DIR/314Sign/scripts" ]; then
  sudo mkdir -p /var/www/html/scripts
  sudo cp -r "$TEMP_DIR/314Sign/scripts/"* /var/www/html/scripts/ 2>&1 || true
fi

echo ""
echo "Files copied. Verifying..."
COPIED_COUNT=$(find /var/www/html -type f | wc -l)
echo "Found $COPIED_COUNT files in /var/www/html"
ls -la /var/www/html/ | head -20

if [ "$COPIED_COUNT" -lt 10 ]; then
  echo ""
  echo "WARNING: Very few files in /var/www/html - installation may be incomplete"
  echo "Contents of /var/www/html:"
  ls -la /var/www/html/
fi

# === 6. Create remote-specific configuration ===
echo ""
echo "Creating remote kiosk configuration..."

# Create device info file
cat > /var/www/html/device.json <<EOF
{
  "serial": "$DEVICE_SERIAL",
  "code": "$DEVICE_CODE",
  "type": "remote",
  "orientation": {
    "hdmi1": $ROTATION_HDMI1
  },
  "setupDate": "$(date -Iseconds)",
  "version": "remote-1.0.0"
}
EOF

echo "✓ Device configuration created"

# Create initial remote config (will be updated by main kiosk after registration)
cat > /var/www/html/remote-config.json <<EOF
{
  "registered": false,
  "mode": "unregistered",
  "lastUpdate": "$(date -Iseconds)",
  "displayName": "Remote $DEVICE_CODE"
}
EOF

echo "✓ Remote configuration initialized"

# === 7. Configure lighttpd for static file serving ===
echo ""
echo "Configuring lighttpd..."

# Enable PHP support
sudo lighttpd-enable-mod fastcgi
sudo lighttpd-enable-mod fastcgi-php

# Configure lighttpd to serve from /var/www/html
sudo tee /etc/lighttpd/lighttpd.conf > /dev/null <<EOF
server.modules = (
	"mod_indexfile",
	"mod_access",
	"mod_alias",
	"mod_redirect",
	"mod_fastcgi"
)

server.document-root        = "/var/www/html"
server.upload-dirs          = ( "/var/cache/lighttpd/uploads" )
server.errorlog             = "/var/log/lighttpd/error.log"
server.pid-file             = "/var/run/lighttpd.pid"
server.username             = "www-data"
server.groupname            = "www-data"
server.port                 = 80

index-file.names            = ( "index.php", "index.html" )
url.access-deny             = ( "~", ".inc" )
static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

# Basic MIME types
mimetype.assign = (
  ".html" => "text/html",
  ".txt" => "text/plain",
  ".jpg" => "image/jpeg",
  ".png" => "image/png",
  ".gif" => "image/gif",
  ".css" => "text/css",
  ".js" => "application/javascript",
  ".json" => "application/json"
)

# FastCGI for PHP
fastcgi.server = ( ".php" => ((
	"bin-path" => "/usr/bin/php-cgi",
	"socket" => "/tmp/php.socket",
	"max-procs" => 1
)))
EOF

# Restart lighttpd with fallbacks (critical for script to continue)
echo "Starting lighttpd service..."

# Enable lighttpd to start on boot
sudo systemctl enable lighttpd 2>/dev/null || echo "Note: systemctl enable failed, continuing..."

# Try systemctl restart first
if sudo systemctl restart lighttpd 2>/dev/null; then
  echo "✓ lighttpd started via systemctl"
elif sudo service lighttpd restart 2>/dev/null; then
  echo "✓ lighttpd started via service command"
else
  # Fallback: Try to start lighttpd manually
  echo "systemctl failed, trying manual start..."
  if sudo lighttpd -f /etc/lighttpd/lighttpd.conf; then
    echo "✓ lighttpd started manually"
  else
    echo "⚠️  lighttpd failed to start - web interface may not be available"
    echo "   You can try: sudo systemctl restart lighttpd"
    echo "   Or: sudo lighttpd -f /etc/lighttpd/lighttpd.conf"
  fi
fi

# Verify lighttpd is responding (don't fail script if not)
if curl -s -f http://localhost/ >/dev/null 2>&1; then
  echo "✓ lighttpd responding on localhost"
else
  echo "⚠️  lighttpd not responding - web interface unavailable"
fi

echo "✓ Static file serving configured with PHP support"

# === 8. Create required directories ===
sudo mkdir -p /var/www/html/logs
sudo mkdir -p /var/www/html/cache
sudo mkdir -p /var/www/html/remote-data

# Create cache directories for offline content
sudo mkdir -p /var/www/html/cache/menus
sudo mkdir -p /var/www/html/cache/slideshows
sudo mkdir -p /var/www/html/cache/config

# Ensure page.json exists to allow external page selection (default to remote)
if [ ! -f /var/www/html/page.json ]; then
  echo '{"page":"remote"}' | sudo tee /var/www/html/page.json > /dev/null
  sudo chown www-data:www-data /var/www/html/page.json || true
  sudo chmod 644 /var/www/html/page.json || true
  echo "Created page.json"
fi

# === 9. Set ownership & permissions ===
echo ""
echo "Setting permissions..."

# Check if permissions script exists
if [ -f "$TEMP_DIR/314Sign/scripts/permissions.sh" ]; then
  # Copy permissions script to temp location and run it
  cp "$TEMP_DIR/314Sign/scripts/permissions.sh" /tmp/314sign-permissions.sh
  chmod +x /tmp/314sign-permissions.sh
  /tmp/314sign-permissions.sh /var/www/html
  rm /tmp/314sign-permissions.sh
  echo "Permissions script executed successfully"
elif [ -f "/var/www/html/scripts/permissions.sh" ]; then
  # Use the already-copied permissions script
  chmod +x /var/www/html/scripts/permissions.sh
  /var/www/html/scripts/permissions.sh /var/www/html
  echo "Permissions script executed successfully"
else
  echo "WARNING: permissions.sh not found, setting basic permissions manually..."
  # Set basic permissions manually
  sudo chown -R www-data:www-data /var/www/html
  sudo find /var/www/html -type d -exec chmod 755 {} \;
  sudo find /var/www/html -type f -exec chmod 644 {} \;
  sudo chmod 775 /var/www/html/cache 2>/dev/null || true
  sudo chmod 775 /var/www/html/remote-data 2>/dev/null || true
  sudo chmod 664 /var/www/html/*.json 2>/dev/null || true
  echo "Basic permissions set"
fi

# Note: Remote functionality is entirely client-side, no server process needed

# Note: QR codes not needed for remotes - only for main kiosk emergency admin access

# === 12. Ensure avahi-daemon is running (optional service) ===
echo ""
echo "Ensuring avahi-daemon is running..."
if sudo systemctl is-active --quiet avahi-daemon 2>/dev/null; then
  echo "✓ Avahi-daemon is already running"
else
  echo "Starting avahi-daemon..."
  if sudo systemctl enable avahi-daemon 2>/dev/null && sudo systemctl start avahi-daemon 2>/dev/null; then
    echo "✓ Avahi-daemon started and enabled successfully"
  else
    echo "⚠️  Avahi-daemon failed to start - .local hostnames may not work"
    echo "   This is optional - remote will still work via IP address"
  fi
fi

# === 13. Set up Remote Kiosk Display Mode ===
echo ""
echo "=== Remote Kiosk Display Setup ==="
echo ""
echo "Setting up auto-boot kiosk mode with Chromium browser."
echo "The remote will display the remote interface showing device code until registered,"
echo "then mirror the main kiosk content."
echo ""

echo "Setting up remote kiosk display mode..."

# Install X server components for remote kiosk
echo "Installing X server components..."
sudo apt install -y xserver-xorg xinit openbox unclutter chromium

# Detect or install browser (prefer chromium)
CHROMIUM_CMD=""
if command -v chromium >/dev/null 2>&1; then
  CHROMIUM_CMD="chromium"
  echo "✓ Using chromium"
elif command -v chromium-browser >/dev/null 2>&1; then
  CHROMIUM_CMD="chromium-browser"
  echo "✓ Using chromium-browser"
elif apt-cache show chromium >/dev/null 2>&1; then
  echo "Installing chromium..."
  sudo apt install -y chromium
  CHROMIUM_CMD="chromium"
elif apt-cache show chromium-browser >/dev/null 2>&1; then
  echo "Installing chromium-browser..."
  sudo apt install -y chromium-browser
  CHROMIUM_CMD="chromium-browser"
else
  echo "ERROR: No suitable browser found for kiosk mode"
  echo "Install chromium manually: sudo apt install chromium"
  exit 1
fi

# Get the target user (usually pi)
TARGET_USER="pi"
if [ -d "/home/pi" ]; then
  TARGET_USER="pi"
elif [ -d "/home/raspberry" ]; then
  TARGET_USER="raspberry"
fi

TARGET_HOME="/home/$TARGET_USER"
echo "Setting up kiosk for user: $TARGET_USER (home: $TARGET_HOME)"

# Create X11 configuration for remote kiosk
sudo mkdir -p /etc/X11/xorg.conf.d
sudo tee /etc/X11/xorg.conf.d/99-v3d.conf > /dev/null <<EOF
Section "OutputClass"
    Identifier "vc4"
    MatchDriver "vc4"
    Driver "modesetting"
    Option "kmsdev" "/dev/dri/card1"
EndSection
EOF

# Set GPU memory and HDMI configuration for Pi Zero 2 W
BOOT_CONFIG="/boot/firmware/config.txt"
[ ! -f "$BOOT_CONFIG" ] && BOOT_CONFIG="/boot/config.txt"

if [ -f "$BOOT_CONFIG" ]; then
  # Remove any existing display settings
  sudo sed -i '/^display_rotate=/d' "$BOOT_CONFIG"
  sudo sed -i '/^display_hdmi_rotate/d' "$BOOT_CONFIG"
  sudo sed -i '/^gpu_mem=/d' "$BOOT_CONFIG"
  sudo sed -i '/^hdmi_force_hotplug=/d' "$BOOT_CONFIG"
  sudo sed -i '/^hdmi_group=/d' "$BOOT_CONFIG"
  sudo sed -i '/^hdmi_mode=/d' "$BOOT_CONFIG"

  # Add GPU memory for X server (critical for Pi Zero)
  echo "gpu_mem=128" | sudo tee -a "$BOOT_CONFIG" > /dev/null

  # Force HDMI hotplug detection (single HDMI port on Pi Zero 2 W)
  echo "hdmi_force_hotplug=1" | sudo tee -a "$BOOT_CONFIG" > /dev/null
  echo "hdmi_group=1" | sudo tee -a "$BOOT_CONFIG" > /dev/null
  echo "hdmi_mode=16" | sudo tee -a "$BOOT_CONFIG" > /dev/null

  # Set display rotation for single HDMI port
  echo "display_hdmi_rotate=$ROTATION_HDMI1" | sudo tee -a "$BOOT_CONFIG" > /dev/null

  echo "GPU memory and HDMI configuration set in $BOOT_CONFIG"
fi

# Configure auto-login to console
echo "Configuring auto-login..."
sudo raspi-config nonint do_boot_behaviour B2

# Create kiosk startup script for remote display
mkdir -p "$TARGET_HOME/.config/openbox"
cat > "$TARGET_HOME/.config/openbox/autostart" <<EOF
# Disable screen blanking
xset s off
xset s noblank
xset -dpms

# Set screen rotation (single HDMI port on Pi Zero 2 W)
xrandr --output HDMI-1 --rotate $(case $ROTATION_HDMI1 in 0) echo "normal";; 1) echo "right";; 2) echo "inverted";; 3) echo "left";; esac) 2>/dev/null || true

# Hide mouse cursor after 1 second
unclutter -idle 1 -root &

# Start Chromium in kiosk mode pointing to remote page
$CHROMIUM_CMD \\
  --kiosk \\
  --remote-debugging-port=9222 \\
  --remote-debugging-address=0.0.0.0 \\
  --no-sandbox \\
  --disable-dev-shm-usage \\
  --noerrdialogs \\
  --disable-infobars \\
  --check-for-update-interval=31536000 \\
  http://localhost/remote/
EOF

# Create X11 auto-start
cat > "$TARGET_HOME/.xinitrc" <<'EOF'
#!/bin/sh
# Start openbox window manager for remote kiosk
exec openbox-session
EOF

# Configure bash to start X on login
cat > "$TARGET_HOME/.bash_profile" <<'EOF'
# Auto-start X11 on login (console only)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx -- -nocursor
fi
EOF

# Set proper ownership and permissions
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.config"
chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.xinitrc"
chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.bash_profile"
chmod +x "$TARGET_HOME/.xinitrc"

echo ""
echo "✅ Remote kiosk display mode configured!"
echo "⚠️  Reboot required for changes to take effect"
echo "   sudo reboot"

# === 14. Cleanup ===
rm -rf "$TEMP_DIR"

echo ""
echo "✅ 314Sign Remote Kiosk installed successfully!"
echo ""

# Check if kiosk mode was set up (check common user directories)
KIOSK_CONFIGURED=false
for user_home in /home/pi /home/raspberry /root; do
  if [ -f "$user_home/.config/openbox/autostart" ]; then
    KIOSK_CONFIGURED=true
    break
  fi
done

if [ "$KIOSK_CONFIGURED" = true ]; then
  echo "📺 Kiosk display mode: CONFIGURED"
  echo "   The Pi will boot directly to fullscreen display"
  echo "   ⚠️  sudo reboot required to activate"
else
  echo "📺 Kiosk display mode: NOT CONFIGURED"
  echo "   Web server is running, but Pi won't display on HDMI"
  echo "   Run kiosk setup later if needed:"
  echo "   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash"
fi
echo ""

# Final verification
echo "=== Installation Verification ==="
FINAL_COUNT=$(find /var/www/html -type f -name "*.html" -o -name "*.php" -o -name "*.json" | wc -l)
echo "Core files found: $FINAL_COUNT"

# Check critical files
MISSING_FILES=()
for file in "remote.html" "device.json" "remote-config.json" "emergency-admin.html"; do
  if [ ! -f "/var/www/html/$file" ]; then
    MISSING_FILES+=("$file")
  fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  WARNING: Some critical files are missing:"
  for file in "${MISSING_FILES[@]}"; do
    echo "   ✗ $file"
  done
  echo ""
  echo "These files will be created in the next steps."
else
  echo "✓ All critical files present"
  echo ""
fi

echo "🆔 Device ID: $DEVICE_CODE"
echo "   (Register this code with your main kiosk)"
echo ""
echo "🌐 Remote Display:"
echo "   http://${HOSTNAME}.local/remote/"
echo ""
# Note: Emergency admin not available on remotes - only on main kiosk
echo "🔧 Monitoring:"
echo "   • lighttpd Status: sudo systemctl status lighttpd"
echo "   • Device Info: cat /var/www/html/device.json"
echo "   • Remote Config: cat /var/www/html/remote-config.json"
echo ""
echo "📋 Next Steps:"
echo "   1. Register device code '$DEVICE_CODE' with your main kiosk"
echo "   2. Configure display mode (mirror/menu/slideshow) on main kiosk"
echo "   3. Reboot to activate kiosk mode: sudo reboot"
echo ""

# task_progress List (Optional - Plan Mode)

While in PLAN MODE, if you've outlined concrete steps or requirements for the user, you may include a preliminary todo list using the task_progress parameter.

Reminder on how to use the task_progress parameter:


1. To create or update a todo list, include the task_progress parameter in the next tool call
2. Review each item and update its status:
   - Mark completed items with: - [x]
   - Keep incomplete items as: - [ ]
   - Add new items if you discover additional steps
3. Modify the list as needed:
		- Add any new steps you've discovered
	 - Reorder if the sequence has changed
4. Ensure the list accurately reflects the current state

**Remember:** Keeping the task_progress list updated helps track progress and ensures nothing is missed.
