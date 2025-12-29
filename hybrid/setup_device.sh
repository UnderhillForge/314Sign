#!/bin/bash
#
# Direct Framebuffer Setup for Pi Devices
# Configures Pi Zero 2W and Pi 5 for direct hardware rendering (no X11)
#

set -e

echo "🚀 Setting up Direct Framebuffer Display (No X11)"
echo "=================================================="

# Detect device type - support entire Raspberry Pi lineup
if grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi5"
    DEVICE_NAME="Raspberry Pi 5"
    CPU_CORES=4
    HAS_WIFI=true
    HAS_BT=true
elif grep -q "Raspberry Pi 4" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi4"
    DEVICE_NAME="Raspberry Pi 4"
    CPU_CORES=4
    HAS_WIFI=true
    HAS_BT=true
elif grep -q "Raspberry Pi Zero 2" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi02w"
    DEVICE_NAME="Raspberry Pi Zero 2 W"
    CPU_CORES=4
    HAS_WIFI=true
    HAS_BT=true
elif grep -q "Raspberry Pi Zero W" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi0w"
    DEVICE_NAME="Raspberry Pi Zero W"
    CPU_CORES=1
    HAS_WIFI=true
    HAS_BT=true
elif grep -q "Raspberry Pi Zero" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi0"
    DEVICE_NAME="Raspberry Pi Zero"
    CPU_CORES=1
    HAS_WIFI=false
    HAS_BT=false
elif grep -q "Raspberry Pi 3" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi3"
    DEVICE_NAME="Raspberry Pi 3"
    CPU_CORES=4
    HAS_WIFI=true
    HAS_BT=true
elif grep -q "Raspberry Pi 2" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi2"
    DEVICE_NAME="Raspberry Pi 2"
    CPU_CORES=4
    HAS_WIFI=false
    HAS_BT=false
elif grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    DEVICE_TYPE="pi1"
    DEVICE_NAME="Raspberry Pi 1"
    CPU_CORES=1
    HAS_WIFI=false
    HAS_BT=false
else
    DEVICE_TYPE="unknown"
    DEVICE_NAME="Unknown Device"
    CPU_CORES=1
    HAS_WIFI=false
    HAS_BT=false
    echo "⚠️  Not a Raspberry Pi device - framebuffer setup may not work"
fi

echo "📱 Detected: $DEVICE_NAME"
echo "   CPU Cores: $CPU_CORES"
echo "   WiFi: $([ "$HAS_WIFI" = true ] && echo "Yes" || echo "No")"
echo "   Bluetooth: $([ "$HAS_BT" = true ] && echo "Yes" || echo "No")"

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-pygame \
    python3-requests \
    python3-pil \
    git \
    vim \
    htop \
    screen \
    openssh-server \
    avahi-daemon \
    avahi-utils \
    fbi \
    imagemagick

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install --user \
    pygame \
    requests \
    pillow \
    numpy

# Create application directories
echo "📁 Creating application directories..."
sudo mkdir -p /opt/314sign
sudo mkdir -p /var/lib/314sign/images
sudo mkdir -p /var/lib/314sign/backgrounds
sudo mkdir -p /home/pi/lms
sudo mkdir -p /home/pi/fonts

# Set permissions
sudo chown -R pi:pi /opt/314sign
sudo chown -R pi:pi /var/lib/314sign
sudo chown -R pi:pi /home/pi/lms
sudo chown -R pi:pi /home/pi/fonts

# Copy application files
echo "📋 Installing application files..."
if [ -d "hybrid" ]; then
    sudo cp -r hybrid/* /opt/314sign/
    sudo chown -R pi:pi /opt/314sign
    echo "✓ Copied hybrid system to /opt/314sign/"

    # Set proper permissions for logo file
    if [ -f "/opt/314sign/314sign2.png" ]; then
        sudo chmod 644 /opt/314sign/314sign2.png
        echo "✓ Logo file ready: /opt/314sign/314sign2.png"
    fi
else
    echo "! hybrid/ directory not found in current location"
    echo "  Make sure to run this from the project root"
fi

# Setup splash screen if requested
read -p "🎨 Install professional boot splash screen? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎨 Setting up boot splash screen..."

    # Create splash screen service
    SPLASH_SERVICE="/etc/systemd/system/314sign-splash.service"

    sudo bash -c "cat > $SPLASH_SERVICE" << EOF
[Unit]
Description=314Sign Boot Splash Screen
After=local-fs.target
Before=kiosk.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
ExecStart=/usr/bin/python3 /opt/314sign/splash_screen.py --config /opt/314sign/splash_config.json
Restart=no
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable 314sign-splash.service

    # Copy default splash configuration
    sudo cp /opt/314sign/splash_config.json /opt/314sign/splash_config.json.default

    echo "✓ Boot splash screen installed"
    echo "  Edit /opt/314sign/splash_config.json to customize branding"
    echo "  Run: sudo systemctl start 314sign-splash.service (to test)"
fi

# Configure boot for direct framebuffer
echo "🔧 Configuring boot for direct framebuffer..."

# Backup existing config
sudo cp /boot/config.txt /boot/config.txt.backup.$(date +%Y%m%d_%H%M%S)

# Add framebuffer configuration
if ! grep -q "framebuffer_width" /boot/config.txt; then
    echo "" | sudo tee -a /boot/config.txt
    echo "# Direct Framebuffer Configuration" | sudo tee -a /boot/config.txt
    echo "framebuffer_width=1920" | sudo tee -a /boot/config.txt
    echo "framebuffer_height=1080" | sudo tee -a /boot/config.txt
    echo "framebuffer_depth=32" | sudo tee -a /boot/config.txt
fi

# Disable unnecessary services for minimal memory usage
echo "🔧 Optimizing for minimal memory usage..."

# Disable Bluetooth (saves ~10MB RAM on Pi Zero)
if [ "$DEVICE_TYPE" = "pi02w" ]; then
    sudo systemctl disable hciuart.service 2>/dev/null || true
    sudo systemctl disable bluetooth.service 2>/dev/null || true
fi

# Configure device hostname and type
echo "🏷️  Configuring device identity..."

# Generate unique device ID from CPU serial
CPU_SERIAL=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2 2>/dev/null || echo "unknown")
DEVICE_ID=$(echo -n "$CPU_SERIAL" | sha256sum | cut -c1-6)
NEW_HOSTNAME="kiosk-${DEVICE_ID}"

echo "Device ID: $DEVICE_ID"
echo "Hostname: $NEW_HOSTNAME"

sudo hostnamectl set-hostname "$NEW_HOSTNAME"
sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/" /etc/hosts

# Configure mDNS
echo "🌐 Configuring mDNS..."
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Create device configuration
echo "⚙️  Creating device configuration..."

# Auto-detect mode based on device capabilities
# Higher-end Pis can run web server, lower-end focus on display
if [ "$CPU_CORES" -ge 4 ] && [ "$HAS_WIFI" = true ]; then
    # Pi 3, 4, 5, Zero 2W - can handle web server
    DEFAULT_MODE="main"
    WEB_SERVER=true
    echo "Main kiosk mode (with web server capability)"
elif [ "$CPU_CORES" -ge 1 ]; then
    # Pi 1, 2, Zero, Zero W - display only
    DEFAULT_MODE="remote"
    WEB_SERVER=false
    echo "Remote display mode (optimized for display)"
else
    # Fallback
    DEFAULT_MODE="remote"
    WEB_SERVER=false
    echo "Remote display mode (limited capabilities)"
fi

echo "   Mode: $DEFAULT_MODE"
echo "   Web Server: $([ "$WEB_SERVER" = true ] && echo "Enabled" || echo "Disabled")"

cat > /home/pi/kiosk_config.json << EOF
{
  "mode": "$DEFAULT_MODE",
  "device_id": "$DEVICE_ID",
  "hostname": "$NEW_HOSTNAME",
  "display_size": [1920, 1080],
  "kiosk_url": "http://kiosk-${DEVICE_ID}.local:80",
  "lms_directory": "/home/pi/lms",
  "update_interval": 300,
  "web_server_enabled": $WEB_SERVER,
  "web_server_port": 80,
  "fullscreen": true,
  "debug": false,
  "device_type": "$DEVICE_TYPE",
  "direct_framebuffer": true
}
EOF

# Create systemd service
echo "🔧 Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/314sign-kiosk.service"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=314Sign Unified Kiosk Application
After=network.target local-fs.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
ExecStart=/usr/bin/python3 /opt/314sign/kiosk_main.py --config /home/pi/kiosk_config.json
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=314sign-kiosk

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable 314sign-kiosk.service

# Create utility scripts
echo "🛠️  Creating utility scripts..."

# Status check script
cat > /home/pi/check_status.sh << 'EOF'
#!/bin/bash
echo "=== 314Sign Kiosk Status ==="
echo "Device: $(hostname)"
echo "Uptime: $(uptime)"
echo "CPU Temp: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo ""

echo "Service Status:"
sudo systemctl status 314sign-kiosk.service --no-pager -l
echo ""

echo "Disk Usage:"
df -h / | tail -1
echo ""

echo "Network:"
ip addr show | grep "inet " | grep -v "127.0.0.1"
echo ""

echo "Recent Logs:"
journalctl -u 314sign-kiosk.service -n 10 --no-pager
echo ""

echo "Configuration:"
cat /home/pi/kiosk_config.json | python3 -m json.tool
EOF

chmod +x /home/pi/check_status.sh

# Content management script
cat > /home/pi/manage_content.sh << 'EOF'
#!/bin/bash
echo "=== 314Sign Content Management ==="
echo "LMS Directory: /home/pi/lms"
echo "Images Directory: /var/lib/314sign/images"
echo "Backgrounds Cache: /var/lib/314sign/backgrounds"
echo ""

echo "Current LMS Files:"
ls -la /home/pi/lms/*.lms 2>/dev/null || echo "No LMS files found"
echo ""

echo "Cached Images:"
ls -la /var/lib/314sign/images/ | head -10
echo ""

echo "Cached Backgrounds:"
ls -la /var/lib/314sign/backgrounds/ | head -10
echo ""

echo "Usage:"
echo "  Place .lms files in /home/pi/lms/ for automatic display"
echo "  Background images are downloaded automatically"
echo "  Run: journalctl -u 314sign-kiosk.service -f  (to watch logs)"
EOF

chmod +x /home/pi/manage_content.sh

# Setup complete
echo ""
echo "🎉 Direct Framebuffer Setup Complete!"
echo "======================================"
echo ""
echo "Device Configuration:"
echo "  Type: $DEVICE_TYPE"
echo "  Mode: $DEFAULT_MODE"
echo "  Hostname: $NEW_HOSTNAME"
echo "  Device ID: $DEVICE_ID"
echo ""
echo "Directories Created:"
echo "  /opt/314sign/          - Application files"
echo "  /var/lib/314sign/      - Data and cache"
echo "  /home/pi/lms/          - LMS content files"
echo "  /home/pi/fonts/        - Custom fonts"
echo ""
echo "Next Steps:"
if [ "$DEFAULT_MODE" = "main" ]; then
    echo "1. The web interface will be available after reboot"
    echo "2. Access at: http://$NEW_HOSTNAME/"
    echo "3. Create LMS content files in /home/pi/lms/"
else
    echo "1. Copy LMS content files to /home/pi/lms/"
    echo "2. The display will start showing content automatically"
fi
echo "3. Reboot: sudo reboot"
echo "4. Check status: ~/check_status.sh"
echo "5. Manage content: ~/manage_content.sh"
echo ""
echo "Useful Commands:"
echo "  Start service: sudo systemctl start 314sign-kiosk.service"
echo "  Stop service: sudo systemctl stop 314sign-kiosk.service"
echo "  View logs: journalctl -u 314sign-kiosk.service -f"
echo "  Restart: sudo systemctl restart 314sign-kiosk.service"
echo ""
echo "🚀 Your device is now configured for direct framebuffer display!"
echo "   No X11, no web browsers, maximum reliability and performance."