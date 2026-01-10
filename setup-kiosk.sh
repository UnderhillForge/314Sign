#!/bin/bash
###############################################################################
# 314Sign Installer (Node.js/TypeScript Version)
#
# Compatible with:
#   - Raspberry Pi OS Lite 64-bit with Node.js
#   - Raspberry Pi OS Desktop (manual kiosk setup required)
#
# Features:
#   - Node.js/Express server with TypeScript
#   - SQLite database for user authentication
#   - Web-based admin interface
#   - Optional kiosk display mode
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh
#   chmod +x setup-kiosk.sh
#   sudo ./setup-kiosk.sh
###############################################################################

set -e  # Exit on any error

echo "=== 314Sign Installer ==="
echo ""

# === 1. Install required packages ===
echo "Installing packages..."

# Clean up any existing NodeSource repositories that might be unreachable
echo "Cleaning up any problematic NodeSource repositories..."
sudo rm -f /etc/apt/sources.list.d/nodesource.list
sudo rm -f /etc/apt/sources.list.d/nodesource*.list

# Clear apt cache for NodeSource repositories
echo "Clearing apt cache for NodeSource..."
sudo rm -rf /var/lib/apt/lists/*nodesource*
sudo rm -rf /var/lib/apt/lists/*node*

# Update package lists (with timeout to prevent hanging)
echo "Updating package lists..."
timeout 300 sudo apt update || {
  echo "Warning: apt update timed out or failed, but continuing with installation..."
}

# Install Node.js (NodeSource repository for latest LTS)
echo "Installing Node.js..."

# Get the latest LTS version dynamically
LATEST_LTS_JSON=$(curl -s --connect-timeout 10 https://nodejs.org/dist/index.json)
if [ -z "$LATEST_LTS_JSON" ]; then
  echo "Failed to fetch Node.js version data, falling back to Node.js 24.x"
  NODE_MAJOR_VERSION="24"
else
  # Find the first LTS version (look for lts that is not false)
  LATEST_LTS_VERSION=$(echo "$LATEST_LTS_JSON" | grep -A1 '"lts":"[^"]*"' | grep '"version"' | head -1 | sed 's/.*"version":"v\([^"]*\)".*/v\1/')
  if [ -z "$LATEST_LTS_VERSION" ]; then
    echo "Failed to determine latest LTS version, falling back to Node.js 24.x"
    NODE_MAJOR_VERSION="24"
  else
    # Extract major version (e.g., v24.12.0 -> 24)
    NODE_MAJOR_VERSION=$(echo "$LATEST_LTS_VERSION" | sed 's/v\([0-9]*\).*/\1/')
    echo "Latest LTS version: $LATEST_LTS_VERSION (major version: $NODE_MAJOR_VERSION)"
  fi
fi

# Try NodeSource first, but with better error handling
NODEJS_INSTALLED=false
echo "Attempting to install Node.js $NODE_MAJOR_VERSION.x from NodeSource..."
if curl -fsSL --connect-timeout 30 "https://deb.nodesource.com/setup_${NODE_MAJOR_VERSION}.x" | sudo -E bash - 2>/dev/null; then
  if sudo apt install -y nodejs 2>/dev/null; then
    echo "✓ Node.js installed successfully from NodeSource"
    NODEJS_INSTALLED=true
  else
    echo "NodeSource repository setup succeeded but package installation failed, trying fallback..."
    if sudo apt install -y nodejs npm 2>/dev/null; then
      echo "✓ Node.js installed from system repositories"
      NODEJS_INSTALLED=true
    fi
  fi
else
  echo "NodeSource setup failed, trying system repositories..."
  if sudo apt install -y nodejs npm 2>/dev/null; then
    echo "✓ Node.js installed from system repositories"
    NODEJS_INSTALLED=true
  fi
fi

# Check Node.js installation
if [ "$NODEJS_INSTALLED" = true ] && command -v node >/dev/null 2>&1; then
  NODE_VERSION=$(node --version)
  NPM_VERSION=$(npm --version)
  echo "✓ Node.js $NODE_VERSION installed"
  echo "✓ npm $NPM_VERSION installed"
else
  echo ""
  echo "⚠️  WARNING: Node.js installation failed!"
  echo "   This may be due to network issues or incompatible system repositories."
  echo ""
  echo "   To install Node.js manually:"
  echo "   1. Download from: https://nodejs.org/dist/v${NODE_MAJOR_VERSION}.12.0/"
  echo "   2. Extract and install, or use Node Version Manager (nvm):"
  echo "      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
  echo "      source ~/.bashrc"
  echo "      nvm install ${NODE_MAJOR_VERSION}"
  echo "      nvm use ${NODE_MAJOR_VERSION}"
  echo ""
  echo "   Continuing with installation - Node.js-dependent features will be skipped..."
  echo ""
fi

# Install additional packages
sudo apt install -y git qrencode avahi-daemon sqlite3

# Optional packages (needed for kiosk automation features, skip on headless systems)
echo "Installing optional packages..."
sudo apt install -y inotify-tools xdotool 2>/dev/null || echo "Note: Some optional packages unavailable (normal for headless systems)"

# === 2. Clone 314Sign from GitHub ===
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

# === 3. Copy files to web root ===
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

# === 3b. Install Node.js dependencies and build ===
echo ""
if [ "$NODEJS_INSTALLED" = true ] && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  echo "Installing Node.js dependencies..."
  cd /var/www/html

  # Check if package.json exists
  if [ ! -f "package.json" ]; then
    echo "ERROR: package.json not found in /var/www/html"
    echo "Installation incomplete - missing package.json"
    exit 1
  fi

  # Install dependencies
  if ! npm install; then
    echo "ERROR: npm install failed"
    echo "Check your internet connection and npm configuration"
    exit 1
  fi

  echo "✓ Dependencies installed"

  # Ensure dist directory has proper permissions for build
  echo "Ensuring dist directory permissions..."
  if [ -d "dist" ]; then
    sudo chown -R $(whoami):$(whoami) dist/ 2>/dev/null || true
  fi

  # Fix permissions for locally installed binaries
  echo "Fixing permissions for installed binaries..."
  chmod +x node_modules/.bin/* 2>/dev/null || true

  # Build TypeScript
  echo "Building TypeScript..."
  if ! npm run build; then
    echo "ERROR: TypeScript build failed"
    echo "Check the build output above for errors"
    exit 1
  fi

  echo "✓ TypeScript compiled successfully"
  echo "✓ 314Sign Node.js server ready"
else
  echo "Skipping Node.js dependencies installation (Node.js not available)"
  echo "⚠️  To complete the installation later:"
  echo "   1. Install Node.js manually"
  echo "   2. Run: cd /var/www/html && npm install && npm run build"
  echo "   3. Run: pm2 start ecosystem.config.js"
fi

# === 4. Create required directories ===
sudo mkdir -p /var/www/html/logs
sudo mkdir -p /var/www/html/bg
sudo mkdir -p /var/www/html/fonts
sudo mkdir -p /var/www/html/history
sudo mkdir -p /var/www/html/menus
sudo mkdir -p /var/www/html/scripts
sudo mkdir -p /var/www/html/start
sudo mkdir -p /var/www/html/slideshows/media
sudo mkdir -p /var/www/html/slideshows/sets

# Database handles reload triggers and demo commands - no files needed
echo "Using database for reload triggers and demo commands"

# Ensure page.json exists to allow external page selection (default to index)
if [ ! -f /var/www/html/page.json ]; then
  echo '{"page":"index"}' | sudo tee /var/www/html/page.json > /dev/null
  sudo chown www-data:www-data /var/www/html/page.json || true
  sudo chmod 644 /var/www/html/page.json || true
  echo "Created page.json"
fi

# === 5. Set ownership & permissions ===
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
  sudo chmod 775 /var/www/html/bg 2>/dev/null || true
  sudo chmod 775 /var/www/html/menus 2>/dev/null || true
  sudo chmod 775 /var/www/html/logs 2>/dev/null || true
  sudo chmod 664 /var/www/html/*.json 2>/dev/null || true
  sudo chmod 664 /var/www/html/index.html 2>/dev/null || true
  echo "Basic permissions set"
fi

# Create backup directory (web-accessible location to avoid sudo issues in PHP)
echo "Creating backup directory..."
sudo mkdir -p /var/www/backups/314sign
sudo chown -R www-data:www-data /var/www/backups
sudo chmod 755 /var/www/backups
echo "✓ Backup directory created at /var/www/backups/314sign"

# === 5b. Configure sudo access for maintenance actions ===
echo ""
echo "Configuring sudo access for web-based maintenance..."

# Check if sudoers file exists in temp directory
if [ -f "$TEMP_DIR/314Sign/sudoers-314sign" ]; then
  # Copy to /etc/sudoers.d/
  sudo cp "$TEMP_DIR/314Sign/sudoers-314sign" /etc/sudoers.d/314sign
  sudo chmod 0440 /etc/sudoers.d/314sign
  
  # Validate the sudoers file
  if sudo visudo -cf /etc/sudoers.d/314sign; then
    echo "✓ Sudo access configured for maintenance actions"
    echo "  - Web interface can now restart server and apply updates"
  else
    echo "⚠ Sudoers file validation failed - removing invalid file"
    sudo rm -f /etc/sudoers.d/314sign
  fi
elif [ -f "/var/www/html/sudoers-314sign" ]; then
  # Fallback if already installed
  sudo cp /var/www/html/sudoers-314sign /etc/sudoers.d/314sign
  sudo chmod 0440 /etc/sudoers.d/314sign
  
  if sudo visudo -cf /etc/sudoers.d/314sign; then
    echo "✓ Sudo access configured from existing file"
  else
    sudo rm -f /etc/sudoers.d/314sign
  fi
else
  echo "⚠ sudoers-314sign not found - maintenance actions will require SSH"
  echo "  To enable later, copy sudoers-314sign to /etc/sudoers.d/314sign"
fi

# === 6. Install and configure PM2 for Node.js service management ===
echo ""
if [ "$NODEJS_INSTALLED" = true ] && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  echo "Installing PM2 process manager..."

  # Install PM2 globally
  if ! sudo npm install -g pm2; then
    echo "ERROR: Failed to install PM2"
    echo "Please install PM2 manually: sudo npm install -g pm2"
    exit 1
  fi

  echo "✓ PM2 installed successfully"

  # Configure PM2 startup (creates systemd service)
  echo "Configuring PM2 startup..."
  # Get the actual user (not root when running with sudo)
  PM2_USER=${SUDO_USER:-$(whoami)}
  PM2_HOME_DIR=$(eval echo ~$PM2_USER 2>/dev/null || echo "/home/$PM2_USER")

  if ! pm2 startup systemd -u "$PM2_USER" --hp "$PM2_HOME_DIR"; then
    echo "⚠️  PM2 startup configuration failed"
    echo "You may need to run: sudo env PATH=\$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $PM2_USER --hp $PM2_HOME_DIR"
  else
    echo "✓ PM2 startup configured for user: $PM2_USER"
  fi

  # Create PM2 ecosystem file for 314Sign (CommonJS syntax with .cjs extension)
  cat > /var/www/html/ecosystem.config.cjs << 'EOF'
module.exports = {
  apps: [{
    name: '314sign',
    script: 'dist/server.js',
    cwd: '/var/www/html',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_log: '/var/www/html/logs/314sign-error.log',
    out_log: '/var/www/html/logs/314sign-out.log',
    log_log: '/var/www/html/logs/314sign-combined.log',
    time: true
  }]
};
EOF

  echo "✓ PM2 ecosystem configuration created"

  # Create logs directory with correct ownership for PM2 user
  sudo mkdir -p /var/www/html/logs
  sudo chown "$PM2_USER:$PM2_USER" /var/www/html/logs

  # Start 314Sign with PM2
  echo "Starting 314Sign server with PM2..."
  cd /var/www/html
  if pm2 start ecosystem.config.cjs; then
    echo "✓ 314Sign server started successfully"
    pm2 save
    echo "✓ PM2 configuration saved"
  else
    echo "⚠️  Failed to start 314Sign with PM2"
    echo "You can try starting manually:"
    echo "  cd /var/www/html && npm start"
  fi

  # Show PM2 status
  echo ""
  echo "PM2 Status:"
  pm2 list
else
  echo "Skipping PM2 installation and server startup (Node.js not available)"
  echo "⚠️  To complete the server setup later:"
  echo "   1. Install Node.js and npm"
  echo "   2. Install PM2: sudo npm install -g pm2"
  echo "   3. Configure PM2: sudo env PATH=\$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi"
  echo "   4. Start server: cd /var/www/html && pm2 start ecosystem.config.cjs"
fi

# === 7. Generate QR codes ===
echo "Generating QR codes..."
HOSTNAME=$(hostname)
cd /var/www/html
[ ! -f qr-start.png ] && qrencode -o qr-start.png -s 10 "http://${HOSTNAME}.local/start/"
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://${HOSTNAME}.local/edit/"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://${HOSTNAME}.local/design/"
[ ! -f qr-rules.png ] && qrencode -o qr-rules.png -s 10 "http://${HOSTNAME}.local/rules/"

# === 8b. Ensure avahi-daemon is running ===
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

# === 9. Optional: Disable Undervoltage Warnings ===
echo ""
echo "=== Optional Configuration ==="
echo ""
echo "Raspberry Pi can show undervoltage warnings even with adequate power supplies."
echo "If you're using a good quality power supply and want to disable these warnings,"
echo "this will add 'avoid_warnings=1' to /boot/config.txt"
echo ""
read -p "Disable undervoltage warnings? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  CONFIG_FILE="/boot/config.txt"
  if [ -f "$CONFIG_FILE" ]; then
    # Check if avoid_warnings is already set
    if grep -q "^avoid_warnings=" "$CONFIG_FILE"; then
      echo "Undervoltage warnings already configured in $CONFIG_FILE"
      grep "^avoid_warnings=" "$CONFIG_FILE"
    else
      echo "Adding avoid_warnings=1 to $CONFIG_FILE..."
      echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
      echo "# Disable undervoltage warnings (314Sign installer)" | sudo tee -a "$CONFIG_FILE" > /dev/null
      echo "avoid_warnings=1" | sudo tee -a "$CONFIG_FILE" > /dev/null
      echo "✓ Undervoltage warnings disabled"
      echo "⚠️  Changes take effect after reboot"
    fi
  else
    echo "⚠️  /boot/config.txt not found - skipping undervoltage configuration"
    echo "   This is normal if not running on Raspberry Pi OS"
  fi
else
  echo "Undervoltage warnings left enabled (recommended for troubleshooting)"
fi

# === 9. Optional: Set up Kiosk Display Mode ===
echo ""
echo "=== Optional Kiosk Display Setup ==="
echo ""
echo "The web server is now running, but the Pi won't automatically display"
echo "the kiosk on HDMI. To set up auto-boot kiosk mode with Chromium browser:"
echo ""
echo "This will install minimal X11 + Chromium and configure auto-start."
echo "The Pi will boot directly to fullscreen kiosk display."
echo ""
read -p "Set up kiosk display mode now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
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
    "$KIOSK_SCRIPT"
  else
    echo "Kiosk script not found locally, downloading from GitHub..."
    if ! curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | bash; then
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
  else
    echo "❌ Kiosk setup script not found!"
    echo "You can install it manually later:"
    echo "  curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash"
  fi
else
  echo "Kiosk display setup skipped."
  echo "To set up kiosk mode later, run:"
  echo "  curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash"
fi

# === 10. Cleanup ===
rm -rf "$TEMP_DIR"

echo ""
if [ "$NODEJS_INSTALLED" = true ] && command -v node >/dev/null 2>&1; then
  echo "✅ 314Sign installed successfully!"
  echo "   Node.js server is running and ready to use."
else
  echo "⚠️  314Sign files installed, but Node.js server setup incomplete!"
  echo "   Install Node.js manually to complete the setup."
fi
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
  if [ "$NODEJS_INSTALLED" = true ]; then
    echo "   Web server is running, but Pi won't display on HDMI"
  else
    echo "   Web server not started (Node.js not available)"
  fi
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
for file in "index.html" "config.json" "rules.json" "public/edit/index.html" "public/design/index.html" "public/rules/index.html" "public/maintenance/index.html" "public/start/index.html"; do
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
  echo "Troubleshooting steps:"
  echo "  1. Check if clone worked: ls -la /tmp/"
  echo "  2. Check internet: ping github.com"
  echo "  3. Try manual install:"
  echo "     cd /tmp && git clone https://github.com/UnderhillForge/314Sign.git"
  echo "     sudo cp -r 314Sign/* /var/www/html/"
  echo ""
else
  echo "✓ All critical files present"
  echo ""
fi

echo "📺 Kiosk Display:"
echo "   http://${HOSTNAME}.local"
echo ""
echo "📱 Staff Editors:"
echo "   • Quick Start:   http://${HOSTNAME}.local/start/"
echo "   • Menu Editor:   http://${HOSTNAME}.local/edit/"
echo "   • Style Config:  http://${HOSTNAME}.local/design/"
echo "   • Auto Schedule: http://${HOSTNAME}.local/rules/"
echo ""
echo "🔧 Monitoring:"
echo "   • Health Check:  http://${HOSTNAME}.local/api/status"
echo "   • Server Logs:   pm2 logs 314sign"
echo "   • Run Backup:    sudo /var/www/html/scripts/backup.sh"
echo ""
echo "🖥️  Server Management:"
echo "   • Restart:       pm2 restart 314sign"
echo "   • Stop:          pm2 stop 314sign"
echo "   • Status:        pm2 list"
echo ""
echo "Print QR codes from /var/www/html/qr-*.png"
echo ""
echo "📋 PM2 Commands:"
echo "   pm2 start ecosystem.config.cjs   # Start server"
echo "   pm2 stop ecosystem.config.cjs    # Stop server"
echo "   pm2 restart ecosystem.config.cjs # Restart server"
echo "   pm2 logs 314sign                 # View logs"
echo "   pm2 monit                        # Monitor processes"
echo ""