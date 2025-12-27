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
  # Interactive mode - prompt for input
  read -p "Enter rotation for HDMI-1 (0-3) [default: 0]: " ROTATION_HDMI1
  ROTATION_HDMI1=${ROTATION_HDMI1:-0}

  read -p "Enter rotation for HDMI-2 (0-3) [default: 0]: " ROTATION_HDMI2
  ROTATION_HDMI2=${ROTATION_HDMI2:-0}
else
  # Non-interactive mode - use defaults
  echo "Non-interactive mode detected, using default orientations..."
  ROTATION_HDMI1=0
  ROTATION_HDMI2=0
fi

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
echo ""

# === 3. Install required packages ===
echo "Installing packages..."
sudo apt update

# Install Apache2 for static file serving
echo "Installing Apache2..."
sudo apt install -y apache2

# Verify Apache2 installation
if ! command -v apache2ctl >/dev/null 2>&1; then
  echo "ERROR: Apache2 installation failed"
  exit 1
fi

echo "✓ Apache2 installed"

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

# Clone repository
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

# Check if rsync is available, fall back to cp if not
if command -v rsync >/dev/null 2>&1; then
  echo "Using rsync to copy files..."
  if ! sudo rsync -av \
    --exclude='.git' \
    --exclude='*.md' \
    --exclude='setup-kiosk.sh' \
    --exclude='remote-setup.sh' \
    "$TEMP_DIR/314Sign/" /var/www/html/ 2>&1; then
    echo ""
    echo "ERROR: rsync failed!"
    echo "Trying alternative copy method..."
    # Fallback to cp
    sudo cp -r "$TEMP_DIR/314Sign/"* /var/www/html/ 2>&1 || {
      echo "ERROR: Copy failed!"
      exit 1
    }
  fi
else
  echo "rsync not found, using cp instead..."
  sudo cp -r "$TEMP_DIR/314Sign/"* /var/www/html/ 2>&1 || {
    echo "ERROR: Copy failed!"
    exit 1
  }
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
    "hdmi1": $ROTATION_HDMI1,
    "hdmi2": $ROTATION_HDMI2
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

# === 7. Configure Apache2 for static file serving ===
echo ""
echo "Configuring Apache2..."

# Enable required Apache modules
sudo a2enmod rewrite
sudo a2enmod headers

# Configure Apache to serve from /var/www/html
sudo tee /etc/apache2/sites-available/314sign.conf > /dev/null <<EOF
<VirtualHost *:80>
    DocumentRoot /var/www/html
    <Directory /var/www/html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
EOF

# Enable the site
sudo a2ensite 314sign
sudo a2dissite 000-default

# Restart Apache2
sudo systemctl restart apache2
sudo systemctl enable apache2

echo "✓ Apache2 configured and started"
echo "✓ Static file serving ready"

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

# === 11. Generate QR codes ===
echo "Generating QR codes..."
HOSTNAME=$(hostname)
cd /var/www/html
[ ! -f qr-emergency-admin.png ] && qrencode -o qr-emergency-admin.png -s 10 "http://${HOSTNAME}.local/emergency-admin/"
echo "✓ Emergency admin QR code generated"

# === 12. Ensure avahi-daemon is running ===
echo ""
echo "Ensuring avahi-daemon is running..."
if sudo systemctl is-active --quiet avahi-daemon; then
  echo "✓ Avahi-daemon is already running"
else
  echo "Starting avahi-daemon..."
  if sudo systemctl enable avahi-daemon && sudo systemctl start avahi-daemon; then
    echo "✓ Avahi-daemon started and enabled successfully"
  else
    echo ""
    echo "⚠️  Avahi-daemon failed to start"
    echo "This may affect .local hostname resolution"
    echo "Manual commands:"
    echo "  sudo systemctl enable avahi-daemon"
    echo "  sudo systemctl start avahi-daemon"
    echo "  sudo systemctl status avahi-daemon"
    echo ""
  fi
fi

# === 13. Set up Kiosk Display Mode ===
echo ""
echo "=== Kiosk Display Setup ==="
echo ""
echo "Setting up auto-boot kiosk mode with Chromium browser."
echo "The Pi will boot directly to fullscreen remote kiosk display showing the device code."
echo ""

echo "Setting up kiosk display mode..."

# Check if kiosk script exists in temp directory or installed location
KIOSK_SCRIPT=""
if [ -f "$TEMP_DIR/314Sign/scripts/os-lite-kiosk.sh" ]; then
  KIOSK_SCRIPT="$TEMP_DIR/314Sign/scripts/os-lite-kiosk.sh"
elif [ -f "/var/www/html/scripts/os-lite-kiosk.sh" ]; then
  KIOSK_SCRIPT="/var/www/html/scripts/os-lite-kiosk.sh"
fi

if [ -n "$KIOSK_SCRIPT" ]; then
  echo "Running kiosk setup script..."
  chmod +x "$KIOSK_SCRIPT"
  # Pass rotation parameters to kiosk script
  ROTATION="$ROTATION_HDMI1" "$KIOSK_SCRIPT"
else
  echo "Kiosk script not found locally, downloading from GitHub..."
  if ! curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | ROTATION="$ROTATION_HDMI1" bash; then
    echo "❌ Failed to download or run kiosk setup script"
    echo "You can try manually:"
    echo "  curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash"
    exit 1
  fi
fi

echo ""
echo "✅ Kiosk display mode configured!"
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
echo "🛠️  Emergency Admin:"
echo "   http://${HOSTNAME}.local/emergency-admin/"
echo "   (QR code: /var/www/html/qr-emergency-admin.png)"
echo ""
echo "🔧 Monitoring:"
echo "   • Apache Status: sudo systemctl status apache2"
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
