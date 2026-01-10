#!/bin/bash
# Setup script for 314Sign Framebuffer Display on Raspberry Pi Zero 2W
# Installs dependencies and configures the system for direct framebuffer rendering

set -e

echo "314Sign Framebuffer Display Setup for Raspberry Pi Zero 2W"
echo "=========================================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi systems"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
echo "Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-dev
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y libffi-dev libssl-dev
sudo apt install -y libjpeg-dev zlib1g-dev  # For image processing

# Install Python packages
echo "Installing Python packages..."
sudo pip3 install pygame requests

# Create 314sign user and directories
echo "Setting up 314sign user and directories..."
sudo useradd -r -s /bin/false 314sign 2>/dev/null || true

# Create directories
sudo mkdir -p /opt/314sign
sudo mkdir -p /var/cache/314sign
sudo mkdir -p /var/log/314sign
sudo mkdir -p /etc/314sign

# Set permissions
sudo chown -R 314sign:314sign /opt/314sign
sudo chown -R 314sign:314sign /var/cache/314sign
sudo chown -R 314sign:314sign /var/log/314sign

# Copy files
echo "Installing 314Sign framebuffer display..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the main program
sudo cp "$SCRIPT_DIR/framebuffer_display.py" /opt/314sign/
sudo cp -r "$SCRIPT_DIR/render" /opt/314sign/
sudo cp -r "$SCRIPT_DIR/lms" /opt/314sign/

# Copy hybrid components we need
sudo cp "$SCRIPT_DIR/blockchain_security.py" /opt/314sign/
sudo cp "$SCRIPT_DIR/kiosk_main.py" /opt/314sign/  # For reference

# Set permissions
sudo chown -R 314sign:314sign /opt/314sign

# Create default configuration
echo "Creating default configuration..."
cat > /tmp/314sign_config.json << 'EOF'
{
  "device_code": "PIZERO001",
  "main_kiosk_url": "http://192.168.1.100:80",
  "display_size": [1920, 1080],
  "orientation": "landscape",
  "cache_dir": "/var/cache/314sign",
  "config_poll_interval": 60,
  "content_poll_interval": 300,
  "debug": false,
  "offline_mode": false,
  "clear_cache_on_exit": false
}
EOF

sudo mv /tmp/314sign_config.json /etc/314sign/config.json
sudo chown 314sign:314sign /etc/314sign/config.json

# Configure boot
echo "Configuring system for framebuffer display..."

# Disable X11 and desktop environment (if installed)
sudo systemctl set-default multi-user.target
sudo systemctl disable lightdm.service 2>/dev/null || true

# Configure framebuffer console
sudo tee -a /boot/config.txt > /dev/null << 'EOF'

# 314Sign Framebuffer Display Configuration
# Disable overscan
disable_overscan=1

# Set HDMI mode (adjust as needed for your display)
hdmi_mode=16
hdmi_group=2

# Framebuffer configuration
framebuffer_width=1920
framebuffer_height=1080
framebuffer_depth=32

# GPU memory (increase for better performance)
gpu_mem=128
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /tmp/314sign-display.service << 'EOF'
[Unit]
Description=314Sign Framebuffer Display
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=314sign
Group=314sign
ExecStart=/usr/bin/python3 /opt/314sign/framebuffer_display.py --config /etc/314sign/config.json
Restart=always
RestartSec=5
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/314sign-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 314sign-display.service

# Configure log rotation
echo "Configuring log rotation..."
cat > /tmp/314sign-logrotate << 'EOF'
/var/log/314sign/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 0644 314sign 314sign
    postrotate
        systemctl reload 314sign-display.service || true
    endscript
}
EOF

sudo mv /tmp/314sign-logrotate /etc/logrotate.d/314sign

# Setup device identification
echo "Setting up device identification..."
if [ ! -f /etc/314sign/device_id ]; then
    # Generate unique device ID based on CPU serial
    if [ -f /proc/cpuinfo ]; then
        CPU_SERIAL=$(grep "Serial" /proc/cpuinfo | awk '{print $3}' | head -1)
        if [ -n "$CPU_SERIAL" ]; then
            DEVICE_ID="PI_${CPU_SERIAL: -8}"
        else
            DEVICE_ID="PI_$(date +%s | tail -c 8)"
        fi
    else
        DEVICE_ID="PI_$(date +%s | tail -c 8)"
    fi

    echo "$DEVICE_ID" | sudo tee /etc/314sign/device_id > /dev/null
    sudo chown 314sign:314sign /etc/314sign/device_id

    # Update config with device ID
    sudo sed -i "s/\"device_code\": \"[^\"]*\"/\"device_code\": \"$DEVICE_ID\"/" /etc/314sign/config.json
fi

# Create helper scripts
echo "Creating helper scripts..."

# Status script
cat > /tmp/314sign-status.sh << 'EOF'
#!/bin/bash
echo "314Sign Framebuffer Display Status"
echo "==================================="
echo "Service status:"
sudo systemctl status 314sign-display.service --no-pager -l
echo
echo "Logs (last 20 lines):"
sudo journalctl -u 314sign-display.service -n 20 --no-pager
echo
echo "Device ID: $(cat /etc/314sign/device_id 2>/dev/null || echo 'Unknown')"
echo "Configuration: /etc/314sign/config.json"
EOF

# Control script
cat > /tmp/314sign-control.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        sudo systemctl start 314sign-display.service
        ;;
    stop)
        sudo systemctl stop 314sign-display.service
        ;;
    restart)
        sudo systemctl restart 314sign-display.service
        ;;
    status)
        sudo systemctl status 314sign-display.service
        ;;
    logs)
        sudo journalctl -u 314sign-display.service -f
        ;;
    configure)
        sudo nano /etc/314sign/config.json
        sudo systemctl restart 314sign-display.service
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|configure}"
        echo
        echo "Commands:"
        echo "  start     - Start the display service"
        echo "  stop      - Stop the display service"
        echo "  restart   - Restart the display service"
        echo "  status    - Show service status"
        echo "  logs      - Show live logs"
        echo "  configure - Edit configuration file"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/314sign-status.sh /usr/local/bin/314sign-status
sudo mv /tmp/314sign-control.sh /usr/local/bin/314sign-control
sudo chmod +x /usr/local/bin/314sign-status
sudo chmod +x /usr/local/bin/314sign-control

# Setup complete
echo
echo "Setup complete!"
echo "==============="
echo
echo "Device ID: $(cat /etc/314sign/device_id)"
echo
echo "Next steps:"
echo "1. Edit configuration: sudo nano /etc/314sign/config.json"
echo "2. Update main_kiosk_url to point to your 314Sign server"
echo "3. Register this device in your main kiosk web interface"
echo "4. Start the service: sudo systemctl start 314sign-display.service"
echo
echo "Helper commands:"
echo "  314sign-status    - Show service status and logs"
echo "  314sign-control   - Control the display service"
echo
echo "The system will reboot in 10 seconds to apply changes..."
echo "Press Ctrl+C to cancel reboot"

# Countdown and reboot
for i in {10..1}; do
    echo -ne "\rRebooting in $i seconds... "
    sleep 1
done
echo

sudo reboot