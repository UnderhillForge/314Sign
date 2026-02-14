#!/bin/bash
###############################################################################
# 314Sign Installer (Node.js/TypeScript + HTTPS)
#
# Compatible with:
#   - Raspberry Pi OS Lite 64-bit
#   - Raspberry Pi OS Desktop (manual kiosk setup required)
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh
#   chmod +x setup-kiosk.sh
#   sudo ./setup-kiosk.sh
###############################################################################

set -e

echo "=== 314Sign Installer ==="
echo ""

# === 1. Install required packages ===
echo "Installing packages..."
sudo apt update
sudo apt install -y curl ca-certificates git qrencode avahi-daemon sqlite3 openssl

# Install Node.js (NodeSource repository for latest LTS)
echo "Installing Node.js..."
if ! curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -; then
  echo "Failed to add NodeSource repository, trying alternative..."
  sudo apt install -y nodejs npm || {
    echo "ERROR: Failed to install Node.js"
    echo "Please install Node.js manually: https://nodejs.org/"
    exit 1
  }
else
  sudo apt install -y nodejs
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js installation failed"
  exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "OK Node.js $NODE_VERSION installed"
echo "OK npm $NPM_VERSION installed"

# Optional packages (skip on headless systems)
echo "Installing optional packages..."
sudo apt install -y inotify-tools xdotool 2>/dev/null || echo "Note: Some optional packages unavailable"

# === 2. Clone 314Sign from GitHub ===
TEMP_DIR=$(mktemp -d)
echo "Cloning 314Sign into $TEMP_DIR..."

if ! ping -c 1 github.com >/dev/null 2>&1; then
  echo "ERROR: Cannot reach github.com - check internet connection"
  echo "Try: ping github.com"
  exit 1
fi

if ! git clone --depth 1 https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign" 2>&1; then
  echo ""
  echo "ERROR: Git clone failed"
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

if [ ! -d "/var/www/html" ]; then
  echo "Creating /var/www/html directory..."
  sudo mkdir -p /var/www/html
fi

if command -v rsync >/dev/null 2>&1; then
  echo "Using rsync to copy files..."
  if ! sudo rsync -av \
    --exclude='.git' \
    --exclude='*.md' \
    --exclude='setup-kiosk.sh' \
    "$TEMP_DIR/314Sign/" /var/www/html/ 2>&1; then
    echo ""
    echo "ERROR: rsync failed"
    echo "Trying alternative copy method..."
    sudo cp -r "$TEMP_DIR/314Sign/"* /var/www/html/ 2>&1 || {
      echo "ERROR: Copy failed"
      exit 1
    }
  fi
else
  echo "rsync not found, using cp instead..."
  sudo cp -r "$TEMP_DIR/314Sign/"* /var/www/html/ 2>&1 || {
    echo "ERROR: Copy failed"
    exit 1
  }
fi

echo ""
echo "Files copied. Verifying..."
COPIED_COUNT=$(find /var/www/html -type f | wc -l)
echo "Found $COPIED_COUNT files in /var/www/html"
ls -la /var/www/html/ | head -20

if [ "$COPIED_COUNT" -lt 10 ]; then
  echo "WARNING: Very few files in /var/www/html - installation may be incomplete"
  ls -la /var/www/html/
fi

# === 3b. Install Node.js dependencies and build ===
echo ""
echo "Installing Node.js dependencies..."

if [ ! -f "/var/www/html/package.json" ]; then
  echo "ERROR: package.json not found in /var/www/html"
  echo "Installation incomplete - missing package.json"
  exit 1
fi

cd /var/www/html
if ! npm install; then
  echo "ERROR: npm install failed"
  exit 1
fi

echo "OK Dependencies installed"

echo "Building TypeScript..."
if ! npm run build; then
  echo "ERROR: TypeScript build failed"
  exit 1
fi

echo "OK TypeScript compiled"
sudo mkdir -p /var/www/html/dist
sudo cp -r dist/* /var/www/html/dist/

# === 4. Create required directories and defaults ===
sudo mkdir -p /var/www/html/logs
sudo mkdir -p /var/www/html/bg
sudo mkdir -p /var/www/html/fonts
sudo mkdir -p /var/www/html/history
sudo mkdir -p /var/www/html/menus
sudo mkdir -p /var/www/html/slideshows/media
sudo mkdir -p /var/www/html/slideshows/sets
sudo mkdir -p /var/www/html/ssl

if [ ! -f /var/www/html/reload.txt ]; then
  echo "0" | sudo tee /var/www/html/reload.txt > /dev/null
fi

if [ ! -f /var/www/html/demo-command.txt ]; then
  echo "idle" | sudo tee /var/www/html/demo-command.txt > /dev/null
fi

if [ ! -f /var/www/html/current-menu.json ]; then
  echo '{"menu":"menus/dinner.txt"}' | sudo tee /var/www/html/current-menu.json > /dev/null
fi

if [ ! -f /var/www/html/page.json ]; then
  echo '{"page":"index"}' | sudo tee /var/www/html/page.json > /dev/null
  sudo chown www-data:www-data /var/www/html/page.json || true
  sudo chmod 644 /var/www/html/page.json || true
fi

# === 5. Set ownership & permissions ===
echo ""
echo "Setting permissions..."

if [ -f "$TEMP_DIR/314Sign/scripts/permissions.sh" ]; then
  cp "$TEMP_DIR/314Sign/scripts/permissions.sh" /tmp/314sign-permissions.sh
  chmod +x /tmp/314sign-permissions.sh
  /tmp/314sign-permissions.sh /var/www/html
  rm /tmp/314sign-permissions.sh
elif [ -f "/var/www/html/scripts/permissions.sh" ]; then
  chmod +x /var/www/html/scripts/permissions.sh
  /var/www/html/scripts/permissions.sh /var/www/html
else
  echo "WARNING: permissions.sh not found, setting basic permissions manually..."
  sudo chown -R www-data:www-data /var/www/html
  sudo find /var/www/html -type d -exec chmod 755 {} \;
  sudo find /var/www/html -type f -exec chmod 644 {} \;
  sudo chmod 775 /var/www/html/bg 2>/dev/null || true
  sudo chmod 775 /var/www/html/menus 2>/dev/null || true
  sudo chmod 775 /var/www/html/logs 2>/dev/null || true
  sudo chmod 664 /var/www/html/*.json 2>/dev/null || true
  sudo chmod 664 /var/www/html/index.html 2>/dev/null || true
fi

echo "Creating backup directory..."
sudo mkdir -p /var/www/backups/314sign
sudo chown -R www-data:www-data /var/www/backups
sudo chmod 755 /var/www/backups

# === 6. Configure sudo access for maintenance actions ===
echo ""
echo "Configuring sudo access for web-based maintenance..."

if [ -f "$TEMP_DIR/314Sign/sudoers-314sign" ]; then
  sudo cp "$TEMP_DIR/314Sign/sudoers-314sign" /etc/sudoers.d/314sign
  sudo chmod 0440 /etc/sudoers.d/314sign
  if sudo visudo -cf /etc/sudoers.d/314sign; then
    echo "OK Sudo access configured"
  else
    echo "WARNING: Sudoers validation failed - removing file"
    sudo rm -f /etc/sudoers.d/314sign
  fi
elif [ -f "/var/www/html/sudoers-314sign" ]; then
  sudo cp /var/www/html/sudoers-314sign /etc/sudoers.d/314sign
  sudo chmod 0440 /etc/sudoers.d/314sign
  if sudo visudo -cf /etc/sudoers.d/314sign; then
    echo "OK Sudo access configured from existing file"
  else
    sudo rm -f /etc/sudoers.d/314sign
  fi
else
  echo "WARNING: sudoers-314sign not found - maintenance actions will require SSH"
fi

# === 7. Install and configure PM2 for Node.js service management ===
echo ""
echo "Installing PM2..."

if ! sudo npm install -g pm2; then
  echo "ERROR: Failed to install PM2"
  exit 1
fi

echo "OK PM2 installed"

if ! pm2 startup; then
  echo "WARNING: PM2 startup configuration failed"
  echo "You may need to run:"
  echo "  sudo env PATH=\$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $(whoami) --hp /home/$(whoami)"
fi

cat > /var/www/html/ecosystem.config.js << 'EOF'
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

sudo mkdir -p /var/www/html/logs
sudo chown www-data:www-data /var/www/html/logs

echo "Starting 314Sign server with PM2..."
cd /var/www/html
if pm2 start ecosystem.config.js; then
  pm2 save
  echo "OK 314Sign server started"
else
  echo "WARNING: Failed to start 314Sign with PM2"
  echo "Try: cd /var/www/html && node dist/server.js"
fi

echo ""
pm2 list

# === 8. Generate TLS certificate (self-signed) ===
echo ""
echo "Generating HTTPS certificate..."
HOSTNAME=$(hostname)
HOST_IP=$(hostname -I | awk '{print $1}')
SAN_LIST="DNS:${HOSTNAME}.local,DNS:localhost,IP:127.0.0.1"
if [ -n "$HOST_IP" ]; then
  SAN_LIST="$SAN_LIST,IP:${HOST_IP}"
fi

if [ ! -f "/var/www/html/ssl/314sign.crt" ] || [ ! -f "/var/www/html/ssl/314sign.key" ]; then
  sudo openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout /var/www/html/ssl/314sign.key \
    -out /var/www/html/ssl/314sign.crt \
    -subj "/CN=${HOSTNAME}.local" \
    -addext "subjectAltName=${SAN_LIST}"
  echo "OK HTTPS certificate created"
else
  echo "HTTPS certificate already exists"
fi

# Optional: Trust certificate for kiosk browser
echo ""
read -p "Install certificate into kiosk trust store? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  sudo cp /var/www/html/ssl/314sign.crt /usr/local/share/ca-certificates/314sign.crt
  sudo update-ca-certificates

  if ! command -v certutil >/dev/null 2>&1; then
    sudo apt install -y libnss3-tools
  fi

  KIOSK_USER=""
  if [ -d "/home/pi" ]; then
    KIOSK_USER="pi"
  fi

  if [ -n "$KIOSK_USER" ]; then
    sudo -u "$KIOSK_USER" mkdir -p "/home/$KIOSK_USER/.pki/nssdb"
    sudo -u "$KIOSK_USER" certutil -d sql:"/home/$KIOSK_USER/.pki/nssdb" -L | grep -q "314sign.local" || \
      sudo -u "$KIOSK_USER" certutil -d sql:"/home/$KIOSK_USER/.pki/nssdb" -A -t "C,," -n "314sign.local" -i /var/www/html/ssl/314sign.crt
    echo "OK Certificate trusted for kiosk user $KIOSK_USER"
  else
    echo "WARNING: Could not determine kiosk user for NSS import"
  fi
fi

# === 9. Configure Plymouth boot splash screen ===
echo ""
echo "=== Boot Splash Screen Setup ==="
echo ""
read -p "Set up 314Sign splash screen during boot? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Configuring Plymouth boot splash..."
  
  # Install Plymouth if not already installed
  if ! command -v plymouthctrl >/dev/null 2>&1; then
    echo "Installing Plymouth..."
    sudo apt install -y plymouth plymouth-themes
  fi
  
  # Create custom 314sign theme
  THEME_DIR="/usr/share/plymouth/themes/314sign"
  sudo mkdir -p "$THEME_DIR"
  
  # Copy logo image
  if [ -f "/var/www/html/media/314sign.png" ]; then
    sudo cp /var/www/html/media/314sign.png "$THEME_DIR/314sign.png"
    echo "OK Logo copied to Plymouth theme directory"
  else
    echo "WARNING: /var/www/html/media/314sign.png not found"
    echo "Skipping Plymouth configuration"
  fi
  
  # Create Plymouth theme script
  if [ -f "$THEME_DIR/314sign.png" ]; then
    sudo tee "$THEME_DIR/314sign.script" > /dev/null << 'PLYMOUTH_SCRIPT'
# 314Sign Plymouth Theme
# Simple fullscreen logo display during boot

background.image = Image("314sign.png");
background.scale = "stretch";
screen.background = background.image;
PLYMOUTH_SCRIPT

    # Create theme.plymouth metadata file
    sudo tee "$THEME_DIR/theme.plymouth" > /dev/null << 'THEME_METADATA'
[Plymouth Theme]
Name=314Sign
Description=314Sign Kiosk Boot Screen
ModuleType=script

[script]
ImageDir=/usr/share/plymouth/themes/314sign
ScriptFile=/usr/share/plymouth/themes/314sign/314sign.script
THEME_METADATA

    chmod +x "$THEME_DIR/314sign.script" 2>/dev/null || true
    echo "OK Plymouth theme created"
    
    # Set Plymouth theme
    if sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth "$THEME_DIR/theme.plymouth" 100; then
      echo "OK Plymouth theme registered"
    fi
    
    # Update boot parameters for quiet splash
    if [ -f "/boot/firmware/cmdline.txt" ]; then
      # Backup original
      sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline.txt.bak
      
      # Add quiet splash if not already present
      if ! grep -q "quiet splash" /boot/firmware/cmdline.txt; then
        CMDLINE=$(cat /boot/firmware/cmdline.txt | sed 's/[[:space:]]*$//')
        echo "$CMDLINE quiet splash" | sudo tee /boot/firmware/cmdline.txt > /dev/null
        echo "OK Boot parameters updated (quiet splash enabled)"
      else
        echo "Boot parameters already configured"
      fi
      
      echo "Backup saved to: /boot/firmware/cmdline.txt.bak"
    else
      echo "WARNING: /boot/firmware/cmdline.txt not found"
      echo "Manual boot parameter update may be needed"
    fi
    
    echo ""
    echo "Plymouth splash screen configured."
    echo "Reboot required for changes to take effect."
    echo "To disable later: sudo plymouth-set-default-theme spinner"
  fi
fi

# === 10. Generate QR codes ===
echo "Generating QR codes..."
cd /var/www/html
[ ! -f qr-menu.png ] && qrencode -o qr-menu.png -s 6 -m 1 "http://${HOSTNAME}.local/?guest=1"
[ ! -f qr-start.png ] && qrencode -o qr-start.png -s 10 "http://${HOSTNAME}.local/start/"
[ ! -f qr-edit.png ] && qrencode -o qr-edit.png -s 10 "http://${HOSTNAME}.local/edit/"
[ ! -f qr-design.png ] && qrencode -o qr-design.png -s 10 "http://${HOSTNAME}.local/design/"
[ ! -f qr-rules.png ] && qrencode -o qr-rules.png -s 10 "http://${HOSTNAME}.local/rules/"

# === 11. Ensure avahi-daemon is running ===
echo ""
echo "Ensuring avahi-daemon is running..."
if sudo systemctl is-active --quiet avahi-daemon; then
  echo "OK Avahi-daemon is already running"
else
  echo "Starting avahi-daemon..."
  if sudo systemctl enable avahi-daemon && sudo systemctl start avahi-daemon; then
    echo "OK Avahi-daemon started"
  else
    echo "WARNING: Avahi-daemon failed to start"
  fi
fi

# === 12. Optional: Set up Kiosk Display Mode ===
echo ""
echo "=== Optional Kiosk Display Setup ==="
echo ""
echo "The server is running, but the Pi will not auto-display on HDMI."
echo "This can install a minimal X11 + Chromium kiosk setup."
echo ""
read -p "Set up kiosk display mode now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  KIOSK_SCRIPT=""
  if [ -f "$TEMP_DIR/314Sign/scripts/os-lite-kiosk.sh" ]; then
    KIOSK_SCRIPT="$TEMP_DIR/314Sign/scripts/os-lite-kiosk.sh"
  elif [ -f "/var/www/html/scripts/os-lite-kiosk.sh" ]; then
    KIOSK_SCRIPT="/var/www/html/scripts/os-lite-kiosk.sh"
  fi

  if [ -n "$KIOSK_SCRIPT" ]; then
    chmod +x "$KIOSK_SCRIPT"
    "$KIOSK_SCRIPT"
  else
    echo "Kiosk script not found locally, downloading..."
    if ! curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | bash; then
      echo "ERROR: Failed to run kiosk setup"
      exit 1
    fi
  fi

  echo ""
  echo "Kiosk display mode configured. Reboot required."
fi

# === 13. Cleanup ===
rm -rf "$TEMP_DIR"

echo ""
echo "OK 314Sign installed successfully"
echo ""

# Final verification
echo "=== Installation Verification ==="
FINAL_COUNT=$(find /var/www/html -type f -name "*.html" -o -name "*.php" -o -name "*.json" | wc -l)
echo "Core files found: $FINAL_COUNT"

MISSING_FILES=()
for file in "index.html" "config.json" "rules.json" "edit/index.html" "design/index.html" "rules/index.html" "maintenance/index.html" "start/index.html"; do
  if [ ! -f "/var/www/html/$file" ]; then
    MISSING_FILES+=("$file")
  fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
  echo ""
  echo "WARNING: Some critical files are missing:"
  for file in "${MISSING_FILES[@]}"; do
    echo "  - $file"
  done
  echo ""
else
  echo "OK All critical files present"
fi

echo ""
echo "Kiosk display:"
echo "  http://${HOSTNAME}.local"
echo ""
echo "Staff editors:"
echo "  - Start:   http://${HOSTNAME}.local/start/"
echo "  - Edit:    http://${HOSTNAME}.local/edit/"
echo "  - Design:  http://${HOSTNAME}.local/design/"
echo "  - Rules:   http://${HOSTNAME}.local/rules/"
echo ""
echo "Monitoring:"
echo "  - Health:  http://${HOSTNAME}.local/api/status"
echo "  - Logs:    pm2 logs 314sign"
echo "  - Backup:  sudo /var/www/html/scripts/backup.sh"
echo ""
echo "Server management:"
echo "  - Restart: pm2 restart 314sign"
echo "  - Stop:    pm2 stop 314sign"
echo "  - Status:  pm2 list"
echo ""
echo "Print QR codes from /var/www/html/qr-*.png"
echo ""
