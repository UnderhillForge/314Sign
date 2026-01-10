#!/bin/bash
# Setup script for 314Sign Remote Kiosk on Raspberry Pi Zero 2W
# Installs lightweight display-only application optimized for minimal hardware

set -e

echo "314Sign Remote Kiosk Setup for Raspberry Pi Zero 2W"
echo "==================================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi systems"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect Pi model
PI_MODEL=""
if grep -q "Raspberry Pi Zero 2" /proc/device-tree/model 2>/dev/null; then
    PI_MODEL="pi02w"
    echo "Detected Raspberry Pi Zero 2 W"
elif grep -q "Raspberry Pi Zero" /proc/device-tree/model 2>/dev/null; then
    PI_MODEL="pi0w"
    echo "Detected Raspberry Pi Zero W"
elif grep -q "Raspberry Pi 3" /proc/device-tree/model 2>/dev/null; then
    PI_MODEL="pi3"
    echo "Detected Raspberry Pi 3 (compatible)"
else
    echo "Warning: Could not detect compatible Pi Zero model"
    PI_MODEL="unknown"
fi

# Update system
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install minimal Python and dependencies
echo "Installing Python and minimal dependencies..."
sudo apt install -y python3 python3-pip python3-dev
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y libffi-dev libssl-dev libjpeg-dev zlib1g-dev

# Install minimal Python packages
echo "Installing Python packages..."
sudo pip3 install pygame requests

# Create 314sign user and directories
echo "Setting up 314sign user and directories..."
sudo useradd -r -s /bin/false 314sign 2>/dev/null || true

# Create directories
sudo mkdir -p /opt/314sign
sudo mkdir -p /tmp/314sign_cache  # Use /tmp for cache on low-storage device
sudo mkdir -p /var/log/314sign
sudo mkdir -p /etc/314sign

# Set permissions
sudo chown -R 314sign:314sign /opt/314sign
sudo chown -R 314sign:314sign /tmp/314sign_cache
sudo chown -R 314sign:314sign /var/log/314sign

# Copy remote kiosk files
echo "Installing 314Sign remote kiosk..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the remote application
sudo cp "$SCRIPT_DIR/remote_kiosk.py" /opt/314sign/
sudo cp -r "$SCRIPT_DIR/render" /opt/314sign/
sudo cp -r "$SCRIPT_DIR/lms" /opt/314sign/

# Set permissions
sudo chown -R 314sign:314sign /opt/314sign

# Create default configuration
echo "Creating default configuration..."
# Prompt for main kiosk URL
echo "Please enter the main kiosk server URL (e.g., http://192.168.1.100:80):"
read -r MAIN_KIOSK_URL
if [ -z "$MAIN_KIOSK_URL" ]; then
    echo "Using default localhost URL"
    MAIN_KIOSK_URL="http://192.168.1.100:80"
fi

cat > /tmp/remote_kiosk_config.json << EOF
{
  "device_code": "REMOTE001",
  "main_kiosk_url": "$MAIN_KIOSK_URL",
  "display_size": [1920, 1080],
  "orientation": "landscape",
  "cache_dir": "/tmp/314sign_cache",
  "config_poll_interval": 120,
  "content_poll_interval": 600,
  "debug": false,
  "offline_mode": false
}
EOF

sudo mv /tmp/remote_kiosk_config.json /etc/314sign/remote_kiosk.json
sudo chown 314sign:314sign /etc/314sign/remote_kiosk.json

# Configure boot for minimal resource usage
echo "Configuring system for remote kiosk..."

# Minimal boot configuration
sudo tee -a /boot/config.txt > /dev/null << 'EOF'

# 314Sign Remote Kiosk Configuration (Pi Zero optimized)
# Minimal GPU memory for low-power operation
gpu_mem=64

# Framebuffer configuration
framebuffer_width=1920
framebuffer_height=1080
framebuffer_depth=16  # Reduced color depth for performance

# Disable unnecessary features for power savings
disable_splash=1
boot_delay=0
force_turbo=0

# HDMI configuration (adjust as needed)
hdmi_mode=16
hdmi_group=2
disable_overscan=1
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /tmp/314sign-remote-kiosk.service << 'EOF'
[Unit]
Description=314Sign Remote Kiosk
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=314sign
Group=314sign
ExecStart=/usr/bin/python3 /opt/314sign/remote_kiosk.py --config /etc/314sign/remote_kiosk.json
Restart=always
RestartSec=10
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
StandardOutput=journal
StandardError=journal
# Memory limits for Pi Zero
MemoryLimit=150M
MemoryMax=200M

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/314sign-remote-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 314sign-remote-kiosk.service

# Configure log rotation for limited storage
echo "Configuring log rotation..."
cat > /tmp/314sign-remote-logrotate << 'EOF'
/var/log/314sign/*.log {
    daily
    missingok
    rotate 3
    compress
    notifempty
    create 0644 314sign 314sign
    postrotate
        systemctl reload 314sign-remote-kiosk.service || true
    endscript
}

/tmp/314sign_cache/* {
    daily
    missingok
    rotate 1
    compress
    notifempty
    postrotate
        find /tmp/314sign_cache -name "*.gz" -type f -mtime +1 -delete 2>/dev/null || true
    endscript
}
EOF

sudo mv /tmp/314sign-remote-logrotate /etc/logrotate.d/314sign-remote

# Setup device identification
echo "Setting up device identification..."
if [ ! -f /etc/314sign/device_id ]; then
    # Generate unique device ID based on CPU serial
    if [ -f /proc/cpuinfo ]; then
        CPU_SERIAL=$(grep "Serial" /proc/cpuinfo | awk '{print $3}' | head -1)
        if [ -n "$CPU_SERIAL" ]; then
            DEVICE_ID="REMOTE_${CPU_SERIAL: -8}"
        else
            DEVICE_ID="REMOTE_$(date +%s | tail -c 8)"
        fi
    else
        DEVICE_ID="REMOTE_$(date +%s | tail -c 8)"
    fi

    echo "$DEVICE_ID" | sudo tee /etc/314sign/device_id > /dev/null
    sudo chown 314sign:314sign /etc/314sign/device_id

    # Update config with device ID
    sudo sed -i "s/\"device_code\": \"[^\"]*\"/\"device_code\": \"$DEVICE_ID\"/" /etc/314sign/remote_kiosk.json
fi

# Create helper scripts
echo "Creating helper scripts..."

# Remote kiosk status script
cat > /tmp/314sign-remote-status.sh << 'EOF'
#!/bin/bash
echo "314Sign Remote Kiosk Status"
echo "============================"
echo "Service status:"
sudo systemctl status 314sign-remote-kiosk.service --no-pager -l
echo
echo "System resources:"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}' | sed 's/^ *//')"
echo "Temperature: $(vcgencmd measure_temp 2>/dev/null || echo "N/A")"
echo
echo "Logs (last 10 lines):"
sudo journalctl -u 314sign-remote-kiosk.service -n 10 --no-pager
echo
echo "Device ID: $(cat /etc/314sign/device_id 2>/dev/null || echo 'Unknown')"
echo "Configuration: /etc/314sign/remote_kiosk.json"
echo "Cache usage: $(du -sh /tmp/314sign_cache 2>/dev/null || echo 'N/A')"
EOF

# Remote kiosk control script
cat > /tmp/314sign-remote-control.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        sudo systemctl start 314sign-remote-kiosk.service
        ;;
    stop)
        sudo systemctl stop 314sign-remote-kiosk.service
        ;;
    restart)
        sudo systemctl restart 314sign-remote-kiosk.service
        ;;
    status)
        sudo systemctl status 314sign-remote-kiosk.service
        ;;
    logs)
        sudo journalctl -u 314sign-remote-kiosk.service -f
        ;;
    clear-cache)
        sudo rm -rf /tmp/314sign_cache/*
        echo "Cache cleared"
        ;;
    configure)
        sudo nano /etc/314sign/remote_kiosk.json
        sudo systemctl restart 314sign-remote-kiosk.service
        ;;
    test)
        echo "Testing main kiosk connectivity..."
        MAIN_URL=$(grep '"main_kiosk_url"' /etc/314sign/remote_kiosk.json | sed 's/.*"main_kiosk_url": "\([^"]*\)".*/\1/')
        if [ -n "$MAIN_URL" ]; then
            DEVICE_CODE=$(grep '"device_code"' /etc/314sign/remote_kiosk.json | sed 's/.*"device_code": "\([^"]*\)".*/\1/')
            TEST_URL="${MAIN_URL}/api/remotes/config/${DEVICE_CODE}"
            echo "Testing: $TEST_URL"
            curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$TEST_URL"
        else
            echo "Main kiosk URL not configured"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|clear-cache|configure|test}"
        echo
        echo "Commands:"
        echo "  start       - Start the remote kiosk service"
        echo "  stop        - Stop the remote kiosk service"
        echo "  restart     - Restart the remote kiosk service"
        echo "  status      - Show service status"
        echo "  logs        - Show live logs"
        echo "  clear-cache - Clear content cache"
        echo "  configure   - Edit configuration file"
        echo "  test        - Test connectivity to main kiosk"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/314sign-remote-status.sh /usr/local/bin/314sign-remote-status
sudo mv /tmp/314sign-remote-control.sh /usr/local/bin/314sign-remote-control
sudo chmod +x /usr/local/bin/314sign-remote-status
sudo chmod +x /usr/local/bin/314sign-remote-control

# Disable unnecessary services for power savings
echo "Optimizing system for power efficiency..."

# Disable Bluetooth if not needed
sudo systemctl disable bluetooth.service 2>/dev/null || true
sudo systemctl disable hciuart.service 2>/dev/null || true

# Disable unnecessary network services
sudo systemctl disable avahi-daemon.service 2>/dev/null || true

# Configure CPU governor for power efficiency
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo "powersave" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1 || true
fi

# Setup complete
echo
echo "Remote Kiosk Setup Complete!"
echo "============================"
echo
echo "Device ID: $(cat /etc/314sign/device_id)"
echo "Main Kiosk URL: $MAIN_KIOSK_URL"
echo
echo "Services installed:"
echo "  • 314Sign Remote Kiosk (framebuffer display)"
echo
echo "Optimizations applied:"
echo "  • Minimal memory footprint (~150MB)"
echo "  • Power-efficient polling intervals"
echo "  • Reduced color depth for performance"
echo "  • Disabled unnecessary services"
echo
echo "Helper commands:"
echo "  314sign-remote-status    - Show system status"
echo "  314sign-remote-control   - Control kiosk service"
echo
echo "Next steps:"
echo "1. Register this device on your main kiosk"
echo "2. Use device code: $(cat /etc/314sign/device_id)"
echo "3. Start service: sudo systemctl start 314sign-remote-kiosk.service"
echo "4. Test connectivity: 314sign-remote-control test"
echo
echo "The remote kiosk is ready for operation!"
echo "System will reboot in 10 seconds to apply optimizations..."

# Countdown and reboot
for i in {10..1}; do
    echo -ne "\rRebooting in $i seconds... "
    sleep 1
done
echo

sudo reboot