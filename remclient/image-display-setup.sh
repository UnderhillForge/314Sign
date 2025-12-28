#!/bin/bash
#
# Image-Based Display Setup for Pi Zero 2 W
# Installs dependencies and configures for image display system
#

set -e

echo "🚀 Setting up Pi Zero 2 W for Image-Based Display"
echo "================================================="

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
    python3-pathlib \
    git \
    vim \
    htop \
    screen \
    openssh-server \
    avahi-daemon \
    avahi-utils

# Install additional Python packages
echo "🐍 Installing Python packages..."
pip3 install --user \
    pygame \
    requests \
    pathlib

# Create directories
echo "📁 Creating directories..."
mkdir -p ~/images
mkdir -p ~/scripts
mkdir -p ~/logs

# Copy display engine
echo "📋 Setting up display engine..."
if [ -f "display_engine.py" ]; then
    cp display_engine.py ~/scripts/
    chmod +x ~/scripts/display_engine.py
    echo "✓ Copied display_engine.py to ~/scripts/"
else
    echo "! display_engine.py not found in current directory"
    echo "  Make sure to copy it from the kiosk system"
fi

# Configure auto-start
echo "🔄 Setting up auto-start..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/image-display.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Image Display Engine
Exec=python3 /home/pi/scripts/display_engine.py
Icon=display
Comment=Image-based display system
X-GNOME-Autostart-enabled=true
EOF

# Disable screen blanking
echo "🖥️  Configuring display settings..."
sudo raspi-config nonint do_blanking 1  # Disable screen blanking

# Configure HDMI
echo "📺 Configuring HDMI output..."
HDMI_CONFIG="/boot/config.txt"
sudo cp "$HDMI_CONFIG" "${HDMI_CONFIG}.backup"

# Add HDMI configuration if not present
if ! grep -q "hdmi_force_hotplug=1" "$HDMI_CONFIG"; then
    echo "" | sudo tee -a "$HDMI_CONFIG"
    echo "# HDMI configuration for image display" | sudo tee -a "$HDMI_CONFIG"
    echo "hdmi_force_hotplug=1" | sudo tee -a "$HDMI_CONFIG"
    echo "hdmi_group=1" | sudo tee -a "$HDMI_CONFIG"
    echo "hdmi_mode=16" | sudo tee -a "$HDMI_CONFIG"  # 1920x1080 @ 60Hz
fi

# Set hostname based on CPU serial
echo "🏷️  Setting device hostname..."
CPU_SERIAL=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2)
DEVICE_ID=$(echo -n "$CPU_SERIAL" | sha256sum | cut -c1-6)
NEW_HOSTNAME="remote-${DEVICE_ID}"

echo "Device ID: $DEVICE_ID"
echo "New hostname: $NEW_HOSTNAME"

sudo hostnamectl set-hostname "$NEW_HOSTNAME"
sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/" /etc/hosts

# Configure Avahi (mDNS)
echo "🌐 Configuring mDNS..."
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Create display configuration
echo "⚙️  Creating display configuration..."
cat > ~/display_config.json << EOF
{
  "device_id": "$DEVICE_ID",
  "hostname": "$NEW_HOSTNAME",
  "kiosk_url": "http://kiosk.local:80",
  "display_resolution": [1920, 1080],
  "update_interval": 300,
  "orientation": 0,
  "power_saving": true,
  "slideshow_mode": "single"
}
EOF

# Create systemd service for display engine
echo "🔧 Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/image-display.service"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Image-Based Display Engine
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/scripts/display_engine.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable image-display.service

# Create utility scripts
echo "🛠️  Creating utility scripts..."

# Status check script
cat > ~/scripts/check_status.sh << 'EOF'
#!/bin/bash
echo "=== Image Display System Status ==="
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime)"
echo "CPU Temp: $(vcgencmd measure_temp)"
echo ""
echo "Display Service:"
sudo systemctl status image-display.service --no-pager -l
echo ""
echo "Images Available: $(ls -1 ~/images/*.png ~/images/*.jpg 2>/dev/null | wc -l)"
echo "Disk Usage: $(df -h / | tail -1)"
echo ""
echo "Network:"
ip addr show | grep "inet "
echo ""
echo "Recent Logs:"
journalctl -u image-display.service -n 10 --no-pager
EOF

chmod +x ~/scripts/check_status.sh

# Manual image sync script
cat > ~/scripts/sync_images.sh << 'EOF'
#!/bin/bash
# Manual image sync from kiosk
KIOSK_HOST="${1:-kiosk.local}"

echo "Syncing images from $KIOSK_HOST..."

# Get latest image (this is a placeholder - would need kiosk API)
# For now, just create a test image
convert -size 1920x1080 xc:blue -pointsize 72 -fill white -gravity center -annotate +0+0 "Remote Display\n$(hostname)\n$(date)" ~/images/test_display.png

echo "Created test display image"
EOF

chmod +x ~/scripts/sync_images.sh

# Setup complete
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Device Information:"
echo "  Hostname: $NEW_HOSTNAME"
echo "  Device ID: $DEVICE_ID"
echo "  IP Address: $(hostname -I | awk '{print $1}')"
echo ""
echo "Next Steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. The display engine will start automatically"
echo "3. Copy images to ~/images/ directory"
echo "4. Check status with: ~/scripts/check_status.sh"
echo ""
echo "Useful Commands:"
echo "  Start display: sudo systemctl start image-display.service"
echo "  Stop display: sudo systemctl stop image-display.service"
echo "  View logs: journalctl -u image-display.service -f"
echo "  Edit config: nano ~/display_config.json"
echo ""
echo "🚀 Your Pi Zero 2 W is now configured for image-based display!"