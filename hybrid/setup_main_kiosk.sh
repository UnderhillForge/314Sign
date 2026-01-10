#!/bin/bash
# Setup script for 314Sign Main Kiosk on Raspberry Pi 4/5
# Installs full-featured kiosk with web server and admin interface

set -e

echo "314Sign Main Kiosk Setup for Raspberry Pi 4/5"
echo "=============================================="

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
if grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    PI_MODEL="pi5"
    echo "Detected Raspberry Pi 5"
elif grep -q "Raspberry Pi 4" /proc/device-tree/model 2>/dev/null; then
    PI_MODEL="pi4"
    echo "Detected Raspberry Pi 4"
else
    echo "Warning: Could not detect Pi 4/5 model"
    PI_MODEL="unknown"
fi

# Update system
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and system dependencies
echo "Installing Python and system dependencies..."
sudo apt install -y python3 python3-pip python3-dev python3-flask python3-psutil
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y libffi-dev libssl-dev libjpeg-dev zlib1g-dev
sudo apt install -y nginx redis-server sqlite3

# Install Python packages
echo "Installing Python packages..."
sudo pip3 install pygame requests flask-cors psutil

# Create 314sign user and directories
echo "Setting up 314sign user and directories..."
sudo useradd -r -s /bin/false 314sign 2>/dev/null || true

# Create directories
sudo mkdir -p /opt/314sign
sudo mkdir -p /var/cache/314sign
sudo mkdir -p /var/log/314sign
sudo mkdir -p /etc/314sign
sudo mkdir -p /var/www/314sign/templates
sudo mkdir -p /var/www/314sign/static/css
sudo mkdir -p /var/www/314sign/static/js
sudo mkdir -p /opt/314sign/lms
sudo mkdir -p /opt/314sign/slideshows

# Set permissions
sudo chown -R 314sign:314sign /opt/314sign
sudo chown -R 314sign:314sign /var/cache/314sign
sudo chown -R 314sign:314sign /var/log/314sign
sudo chown -R www-data:www-data /var/www/314sign

# Copy main kiosk files
echo "Installing 314Sign main kiosk..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the main application
sudo cp "$SCRIPT_DIR/main_kiosk.py" /opt/314sign/
sudo cp -r "$SCRIPT_DIR/render" /opt/314sign/
sudo cp -r "$SCRIPT_DIR/lms" /opt/314sign/

# Copy web interface files
sudo cp -r "$SCRIPT_DIR/../public/slideshows" /var/www/314sign/ 2>/dev/null || true
sudo cp -r "$SCRIPT_DIR/../public/remotes" /var/www/314sign/ 2>/dev/null || true

# Create basic web interface
cat > /tmp/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>314Sign Main Kiosk</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f0f0f0; }
        .status { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .links { display: flex; gap: 20px; flex-wrap: wrap; }
        .link { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        .link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>314Sign Main Kiosk</h1>
    <div class="status">
        <h2>System Status</h2>
        <p>Device: <span id="device">Loading...</span></p>
        <p>Hardware: <span id="hardware">Loading...</span></p>
        <p>Status: <span id="status">Starting...</span></p>
    </div>

    <h2>Management</h2>
    <div class="links">
        <a href="/slideshows/" class="link">📽️ Slideshow Editor</a>
        <a href="/remotes/" class="link">📺 Remote Displays</a>
        <a href="/mobile" class="link">📱 Mobile Access</a>
        <a href="/admin" class="link">⚙️ Admin Panel</a>
    </div>

    <script>
        // Update status
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('device').textContent = 'MAIN_KIOSK';
                document.getElementById('hardware').textContent = `${data.cpu_percent}% CPU, ${data.memory.percent}% RAM`;
                document.getElementById('status').textContent = 'Active';
            })
            .catch(() => {
                document.getElementById('status').textContent = 'Offline';
            });
    </script>
</body>
</html>
EOF

sudo mv /tmp/index.html /var/www/314sign/templates/

# Create mobile access template
cat > /tmp/mobile.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>314Sign Mobile View</title>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial; background: #000; color: white; }
        .content { max-width: 100%; }
        .header { text-align: center; margin-bottom: 20px; }
        .qr-notice { background: #333; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .timestamp { color: #ccc; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="content">
        <div class="header">
            <h1>314Sign Display</h1>
            <div class="qr-notice">
                📱 Mobile view of current display content
            </div>
        </div>

        <div id="display-content">
            <p>Loading current display content...</p>
        </div>

        <div class="timestamp" id="timestamp">
            Last updated: Loading...
        </div>
    </div>

    <script>
        function updateContent() {
            fetch('/api/current-content')
                .then(r => r.json())
                .then(data => {
                    const content = document.getElementById('display-content');
                    const timestamp = document.getElementById('timestamp');

                    if (data.type === 'standby') {
                        content.innerHTML = '<p style="text-align: center; color: #666;">Display is in standby mode</p>';
                    } else {
                        content.innerHTML = `<p style="text-align: center;">${data.type} content active</p>`;
                    }

                    timestamp.textContent = `Last updated: ${new Date(data.timestamp * 1000).toLocaleTimeString()}`;
                })
                .catch(err => {
                    document.getElementById('display-content').innerHTML =
                        '<p style="text-align: center; color: #666;">Unable to load display content</p>';
                });
        }

        // Update content every 5 seconds
        updateContent();
        setInterval(updateContent, 5000);
    </script>
</body>
</html>
EOF

sudo mv /tmp/mobile.html /var/www/314sign/templates/

# Create admin template
cat > /tmp/admin.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>314Sign Admin Panel</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f0f0; }
        .panel { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .remotes { margin-top: 20px; }
        .remote { padding: 10px; margin: 10px 0; background: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>314Sign Admin Panel</h1>

    <div class="panel">
        <h2>System Statistics</h2>
        <div class="stats" id="stats">
            <div class="stat">
                <div class="stat-value" id="cpu">--</div>
                <div>CPU Usage</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="memory">--</div>
                <div>Memory Usage</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="disk">--</div>
                <div>Disk Usage</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="temp">--</div>
                <div>Temperature</div>
            </div>
        </div>
    </div>

    <div class="panel">
        <h2>Remote Displays</h2>
        <div class="remotes" id="remotes">
            <p>Loading remote displays...</p>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('cpu').textContent = data.cpu_percent + '%';
                    document.getElementById('memory').textContent = data.memory.percent + '%';
                    document.getElementById('disk').textContent = data.disk.percent + '%';
                    document.getElementById('temp').textContent = data.temperature ? data.temperature + '°C' : '--';
                });
        }

        function updateRemotes() {
            fetch('/api/remotes')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('remotes');
                    if (data.remotes.length === 0) {
                        container.innerHTML = '<p>No remote displays registered</p>';
                        return;
                    }

                    container.innerHTML = data.remotes.map(remote => `
                        <div class="remote">
                            <strong>${remote.displayName || remote.code}</strong>
                            <br>Status: ${remote.status}
                            <br>Mode: ${remote.mode}
                            <br>Last seen: ${new Date(remote.lastSeen).toLocaleString()}
                        </div>
                    `).join('');
                });
        }

        // Update every 5 seconds
        updateStats();
        updateRemotes();
        setInterval(updateStats, 5000);
        setInterval(updateRemotes, 10000);
    </script>
</body>
</html>
EOF

sudo mv /tmp/admin.html /var/www/314sign/templates/

# Set permissions
sudo chown -R 314sign:314sign /opt/314sign
sudo chown -R www-data:www-data /var/www/314sign

# Create default configuration
echo "Creating default configuration..."
cat > /tmp/main_kiosk_config.json << EOF
{
  "device_code": "MAIN_KIOSK",
  "main_kiosk_url": "http://localhost:80",
  "display_size": [1920, 1080],
  "orientation": "landscape",
  "cache_dir": "/var/cache/314sign",
  "web_root": "/var/www/314sign",
  "web_port": 80,
  "admin_port": 8080,
  "mobile_enabled": true,
  "remote_management_enabled": true,
  "analytics_enabled": true,
  "debug": false,
  "lms_dir": "/opt/314sign/lms",
  "slideshow_dir": "/opt/314sign/slideshows"
}
EOF

sudo mv /tmp/main_kiosk_config.json /etc/314sign/main_kiosk.json
sudo chown 314sign:314sign /etc/314sign/main_kiosk.json

# Configure boot
echo "Configuring system for main kiosk..."

# Set GPU memory based on Pi model
if [ "$PI_MODEL" = "pi5" ]; then
    GPU_MEM=512
elif [ "$PI_MODEL" = "pi4" ]; then
    GPU_MEM=256
else
    GPU_MEM=128
fi

sudo tee -a /boot/config.txt > /dev/null << EOF

# 314Sign Main Kiosk Configuration
# GPU memory allocation
gpu_mem=$GPU_MEM

# Framebuffer configuration for high-quality display
framebuffer_width=1920
framebuffer_height=1080
framebuffer_depth=32

# Disable overscan for clean display
disable_overscan=1

# Set HDMI mode (adjust as needed for your display)
hdmi_mode=16
hdmi_group=2
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /tmp/314sign-main-kiosk.service << 'EOF'
[Unit]
Description=314Sign Main Kiosk
After=network-online.target nginx.service
Wants=network-online.target

[Service]
Type=simple
User=314sign
Group=314sign
ExecStart=/usr/bin/python3 /opt/314sign/main_kiosk.py --config /etc/314sign/main_kiosk.json
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

sudo mv /tmp/314sign-main-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 314sign-main-kiosk.service

# Configure Nginx (optional, for additional web serving)
echo "Configuring Nginx (optional)..."
sudo tee /etc/nginx/sites-available/314sign > /dev/null << 'EOF'
server {
    listen 80;
    server_name localhost;

    root /var/www/314sign;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/314sign /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl enable nginx

# Setup device identification
echo "Setting up device identification..."
if [ ! -f /etc/314sign/device_id ]; then
    # Generate unique device ID based on CPU serial
    if [ -f /proc/cpuinfo ]; then
        CPU_SERIAL=$(grep "Serial" /proc/cpuinfo | awk '{print $3}' | head -1)
        if [ -n "$CPU_SERIAL" ]; then
            DEVICE_ID="MAIN_${CPU_SERIAL: -8}"
        else
            DEVICE_ID="MAIN_$(date +%s | tail -c 8)"
        fi
    else
        DEVICE_ID="MAIN_$(date +%s | tail -c 8)"
    fi

    echo "$DEVICE_ID" | sudo tee /etc/314sign/device_id > /dev/null
    sudo chown 314sign:314sign /etc/314sign/device_id

    # Update config with device ID
    sudo sed -i "s/\"device_code\": \"[^\"]*\"/\"device_code\": \"$DEVICE_ID\"/" /etc/314sign/main_kiosk.json
fi

# Create helper scripts
echo "Creating helper scripts..."

# Main kiosk status script
cat > /tmp/314sign-main-status.sh << 'EOF'
#!/bin/bash
echo "314Sign Main Kiosk Status"
echo "=========================="
echo "Service status:"
sudo systemctl status 314sign-main-kiosk.service --no-pager -l
echo
echo "Web server status:"
sudo systemctl status nginx --no-pager -l
echo
echo "Logs (last 20 lines):"
sudo journalctl -u 314sign-main-kiosk.service -n 20 --no-pager
echo
echo "Device ID: $(cat /etc/314sign/device_id 2>/dev/null || echo 'Unknown')"
echo "Configuration: /etc/314sign/main_kiosk.json"
echo "Web interface: http://localhost/"
echo "Admin panel: http://localhost/admin"
echo "Mobile access: http://localhost/mobile"
EOF

# Main kiosk control script
cat > /tmp/314sign-main-control.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        sudo systemctl start 314sign-main-kiosk.service
        sudo systemctl start nginx
        ;;
    stop)
        sudo systemctl stop 314sign-main-kiosk.service
        sudo systemctl stop nginx
        ;;
    restart)
        sudo systemctl restart 314sign-main-kiosk.service
        sudo systemctl restart nginx
        ;;
    status)
        sudo systemctl status 314sign-main-kiosk.service
        ;;
    logs)
        sudo journalctl -u 314sign-main-kiosk.service -f
        ;;
    web-logs)
        sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
        ;;
    configure)
        sudo nano /etc/314sign/main_kiosk.json
        sudo systemctl restart 314sign-main-kiosk.service
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|web-logs|configure}"
        echo
        echo "Commands:"
        echo "  start     - Start kiosk and web services"
        echo "  stop      - Stop kiosk and web services"
        echo "  restart   - Restart kiosk and web services"
        echo "  status    - Show kiosk service status"
        echo "  logs      - Show kiosk application logs"
        echo "  web-logs  - Show web server logs"
        echo "  configure - Edit configuration file"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/314sign-main-status.sh /usr/local/bin/314sign-main-status
sudo mv /tmp/314sign-main-control.sh /usr/local/bin/314sign-main-control
sudo chmod +x /usr/local/bin/314sign-main-status
sudo chmod +x /usr/local/bin/314sign-main-control

# Setup complete
echo
echo "Main Kiosk Setup Complete!"
echo "=========================="
echo
echo "Device ID: $(cat /etc/314sign/device_id)"
echo
echo "Services installed:"
echo "  • 314Sign Main Kiosk (framebuffer display)"
echo "  • Nginx web server (port 80)"
echo "  • Flask API server (internal)"
echo
echo "Web interfaces:"
echo "  • Main interface: http://localhost/"
echo "  • Admin panel: http://localhost/admin"
echo "  • Mobile access: http://localhost/mobile"
echo "  • Slideshow editor: http://localhost/slideshows/"
echo "  • Remote management: http://localhost/remotes/"
echo
echo "Helper commands:"
echo "  314sign-main-status    - Show complete system status"
echo "  314sign-main-control   - Control kiosk services"
echo
echo "Next steps:"
echo "1. Edit configuration: sudo nano /etc/314sign/main_kiosk.json"
echo "2. Start services: sudo systemctl start 314sign-main-kiosk.service"
echo "3. Access admin panel at http://localhost/admin"
echo "4. Register remote displays in remote management interface"
echo
echo "The system is ready for production use!"
echo "System will reboot in 10 seconds to apply all changes..."

# Countdown and reboot
for i in {10..1}; do
    echo -ne "\rRebooting in $i seconds... "
    sleep 1
done
echo

sudo reboot