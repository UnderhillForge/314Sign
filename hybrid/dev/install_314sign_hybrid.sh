#!/bin/bash
#
# 314Sign Hybrid System Installer
# Complete deployment script for 314Sign digital signage platform
#
# This script installs the complete 314Sign hybrid system including:
# - LMS rendering engine with direct framebuffer support
# - Web content editor for visual LMS creation
# - Administration console for system management
# - Professional boot splash screens
# - Automated device configuration
#
# Version: 1.0.2.68
# Compatible with: Raspberry Pi 1-5, all Zero variants
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Emoji support
if [[ "$TERM" != "dumb" ]]; then
    ROCKET="🚀"
    CHECK="✅"
    CROSS="❌"
    GEAR="⚙️"
    COMPUTER="🖥️"
    WIFI="📶"
    SHIELD="🛡️"
    PAINT="🎨"
    BOOK="📚"
    GLOBE="🌐"
    LOCK="🔒"
    CHART="📊"
    TOOLS="🛠️"
else
    ROCKET="[ROCKET]"
    CHECK="[OK]"
    CROSS="[ERROR]"
    GEAR="[CONFIG]"
    COMPUTER="[SYSTEM]"
    WIFI="[NETWORK]"
    SHIELD="[SECURITY]"
    PAINT="[DISPLAY]"
    BOOK="[CONTENT]"
    GLOBE="[WEB]"
    LOCK="[SECURE]"
    CHART="[MONITOR]"
    TOOLS="[TOOLS]"
fi

# Script configuration
SCRIPT_VERSION="1.0.2.68"
REPO_URL="https://github.com/UnderhillForge/314Sign.git"
BRANCH="feature/hybrid-markup-system"
INSTALL_DIR="/opt/314sign"
CONFIG_DIR="/home/pi"
LMS_DIR="/home/pi/lms"
WEB_PORT=8080
KIOSK_PORT=80

# Default configuration
DEFAULT_MODE="main"  # 'main' or 'remote'
DEFAULT_ORIENTATION="portrait"  # 'landscape' or 'portrait'
ENABLE_SPLASH=true
ENABLE_WEB_EDITOR=true
ENABLE_ADMIN_CONSOLE=true

# Hardware detection
detect_hardware() {
    echo -e "${BLUE}${COMPUTER} Detecting hardware...${NC}"

    # Raspberry Pi model detection
    if grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi5"
        DEVICE_NAME="Raspberry Pi 5"
        CPU_CORES=4
        HAS_WIFI=true
        HAS_BT=true
        MEMORY_GB=4
    elif grep -q "Raspberry Pi 4" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi4"
        DEVICE_NAME="Raspberry Pi 4"
        CPU_CORES=4
        HAS_WIFI=true
        HAS_BT=true
        MEMORY_GB=2
    elif grep -q "Raspberry Pi Zero 2" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi02w"
        DEVICE_NAME="Raspberry Pi Zero 2 W"
        CPU_CORES=4
        HAS_WIFI=true
        HAS_BT=true
        MEMORY_GB=0.5
    elif grep -q "Raspberry Pi Zero W" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi0w"
        DEVICE_NAME="Raspberry Pi Zero W"
        CPU_CORES=1
        HAS_WIFI=true
        HAS_BT=true
        MEMORY_GB=0.5
    elif grep -q "Raspberry Pi Zero" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi0"
        DEVICE_NAME="Raspberry Pi Zero"
        CPU_CORES=1
        HAS_WIFI=false
        HAS_BT=false
        MEMORY_GB=0.5
    elif grep -q "Raspberry Pi 3" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi3"
        DEVICE_NAME="Raspberry Pi 3"
        CPU_CORES=4
        HAS_WIFI=true
        HAS_BT=true
        MEMORY_GB=1
    elif grep -q "Raspberry Pi 2" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi2"
        DEVICE_NAME="Raspberry Pi 2"
        CPU_CORES=4
        HAS_WIFI=false
        HAS_BT=false
        MEMORY_GB=1
    elif grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        DEVICE_TYPE="pi1"
        DEVICE_NAME="Raspberry Pi 1"
        CPU_CORES=1
        HAS_WIFI=false
        HAS_BT=false
        MEMORY_GB=0.5
    else
        echo -e "${YELLOW}⚠️  Not a Raspberry Pi device - some features may not work${NC}"
        DEVICE_TYPE="unknown"
        DEVICE_NAME="Unknown Device"
        CPU_CORES=1
        HAS_WIFI=false
        HAS_BT=false
        MEMORY_GB=0.5
    fi

    echo -e "${CHECK} Detected: ${WHITE}${DEVICE_NAME}${NC}"
    echo -e "${CHECK} CPU Cores: ${WHITE}${CPU_CORES}${NC}"
    echo -e "${CHECK} WiFi: ${WHITE}$(if [ "$HAS_WIFI" = true ]; then echo "Yes"; else echo "No"; fi)${NC}"
    echo -e "${CHECK} Bluetooth: ${WHITE}$(if [ "$HAS_BT" = true ]; then echo "Yes"; else echo "No"; fi)${NC}"
    echo ""
}

# System update
update_system() {
    echo -e "${BLUE}${GEAR} Updating system packages...${NC}"

    # Update package lists
    apt update
    echo -e "${CHECK} Package lists updated"

    # Upgrade system (optional - ask user)
    read -p "Upgrade system packages? (recommended) [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        apt upgrade -y
        echo -e "${CHECK} System packages upgraded"
    fi

    # Install required packages
    echo -e "${BLUE}${TOOLS} Installing required packages...${NC}"
    apt install -y \
        python3 \
        python3-pip \
        python3-pygame \
        python3-requests \
        python3-pil \
        python3-curses \
        git \
        vim \
        htop \
        screen \
        openssh-server \
        avahi-daemon \
        avahi-utils \
        fbi \
        imagemagick \
        curl \
        wget \
        jq \
        sqlite3 \
        ufw \
        ntfs-3g \
        exfat-fuse \
        usbutils

    echo -e "${CHECK} Required packages installed"
    echo ""
}

# Install Python dependencies
install_python_deps() {
    echo -e "${BLUE}${GEAR} Installing Python dependencies...${NC}"

    pip3 install --user \
        pygame \
        requests \
        pillow \
        numpy \
        psutil

    echo -e "${CHECK} Python dependencies installed"
    echo ""
}

# Clone repository
clone_repository() {
    echo -e "${BLUE}${BOOK} Cloning 314Sign repository...${NC}"

    if [ -d "314Sign" ]; then
        echo -e "${YELLOW}Repository already exists, updating...${NC}"
        cd 314Sign
        git fetch origin
        git checkout $BRANCH
        git pull origin $BRANCH
    else
        git clone $REPO_URL
        cd 314Sign
        git checkout $BRANCH
    fi

    echo -e "${CHECK} Repository ready"
    echo ""
}

# Create directories
create_directories() {
    echo -e "${BLUE}${GEAR} Creating application directories...${NC}"

    # System directories
    mkdir -p $INSTALL_DIR
    mkdir -p /var/lib/314sign/images
    mkdir -p /var/lib/314sign/backgrounds
    mkdir -p /var/lib/314sign/templates
    mkdir -p $LMS_DIR
    mkdir -p /home/pi/fonts
    mkdir -p /home/pi/logs

    # Set permissions
    chown -R pi:pi $INSTALL_DIR
    chown -R pi:pi /var/lib/314sign
    chown -R pi:pi $LMS_DIR
    chown -R pi:pi /home/pi/fonts
    chown -R pi:pi /home/pi/logs

    echo -e "${CHECK} Directories created and permissions set"
    echo ""
}

# Install application files
install_application() {
    echo -e "${BLUE}${BOOK} Installing 314Sign hybrid system...${NC}"

    # Copy hybrid system files
    if [ -d "hybrid" ]; then
        cp -r hybrid/* $INSTALL_DIR/
        chmod +x $INSTALL_DIR/*.py
        chmod +x $INSTALL_DIR/*.sh
        echo -e "${CHECK} Hybrid system files installed"
    else
        echo -e "${RED}${CROSS} Hybrid directory not found!${NC}"
        exit 1
    fi

    # Copy logo
    if [ -f "hybrid/314sign2.png" ]; then
        cp hybrid/314sign2.png $INSTALL_DIR/
        chmod 644 $INSTALL_DIR/314sign2.png
        echo -e "${CHECK} Logo file installed"
    fi

    echo ""
}

# Configure device
configure_device() {
    echo -e "${BLUE}${GEAR} Configuring device...${NC}"

    # Generate unique device ID
    CPU_SERIAL=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2 2>/dev/null || echo "unknown")
    DEVICE_ID=$(echo -n "$CPU_SERIAL-$DEVICE_TYPE" | sha256sum | cut -c1-8)

    # Set hostname
    NEW_HOSTNAME="kiosk-${DEVICE_ID}"
    hostnamectl set-hostname "$NEW_HOSTNAME"
    sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/" /etc/hosts

    echo -e "${CHECK} Device ID: ${WHITE}${DEVICE_ID}${NC}"
    echo -e "${CHECK} Hostname: ${WHITE}${NEW_HOSTNAME}${NC}"

    # Create configuration
    cat > ${CONFIG_DIR}/kiosk_config.json << EOF
{
  "version": "${SCRIPT_VERSION}",
  "mode": "${DEFAULT_MODE}",
  "device_id": "${DEVICE_ID}",
  "hostname": "${NEW_HOSTNAME}",
  "device_type": "${DEVICE_TYPE}",
  "display_size": [1920, 1080],
  "orientation": "${DEFAULT_ORIENTATION}",
  "kiosk_url": "http://localhost:${KIOSK_PORT}",
  "lms_directory": "${LMS_DIR}",
  "update_interval": 300,
  "web_server_enabled": ${ENABLE_WEB_EDITOR},
  "web_server_port": ${WEB_PORT},
  "kiosk_port": ${KIOSK_PORT},
  "fullscreen": true,
  "direct_framebuffer": true,
  "debug": false,
  "installed_at": "$(date -Iseconds)",
  "hardware": {
    "model": "${DEVICE_NAME}",
    "cpu_cores": ${CPU_CORES},
    "memory_gb": ${MEMORY_GB},
    "has_wifi": ${HAS_WIFI},
    "has_bluetooth": ${HAS_BT}
  }
}
EOF

    echo -e "${CHECK} Configuration created"
    echo ""
}

# Configure boot
configure_boot() {
    echo -e "${BLUE}${PAINT} Configuring boot for direct framebuffer...${NC}"

    # Backup existing config
    if [ ! -f "/boot/config.txt.backup" ]; then
        cp /boot/config.txt /boot/config.txt.backup.$(date +%Y%m%d_%H%M%S)
        echo -e "${CHECK} Boot config backed up"
    fi

    # Add framebuffer configuration
    if ! grep -q "framebuffer_width" /boot/config.txt; then
        echo "" >> /boot/config.txt
        echo "# 314Sign Direct Framebuffer Configuration" >> /boot/config.txt
        echo "framebuffer_width=1920" >> /boot/config.txt
        echo "framebuffer_height=1080" >> /boot/config.txt
        echo "framebuffer_depth=32" >> /boot/config.txt
    fi

    # Configure HDMI for kiosk mode
    if ! grep -q "hdmi_force_hotplug" /boot/config.txt; then
        echo "hdmi_force_hotplug=1" >> /boot/config.txt
        echo "hdmi_drive=2" >> /boot/config.txt
        echo "hdmi_group=2" >> /boot/config.txt
        echo "hdmi_mode=82" >> /boot/config.txt
    fi

    echo -e "${CHECK} Boot configuration updated"
    echo ""
}

# Configure services
configure_services() {
    echo -e "${BLUE}${GEAR} Configuring system services...${NC}"

    # Create kiosk service
    cat > /etc/systemd/system/314sign-kiosk.service << EOF
[Unit]
Description=314Sign Hybrid Kiosk Application
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
ExecStart=${INSTALL_DIR}/kiosk_main.py --config ${CONFIG_DIR}/kiosk_config.json
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=314sign-kiosk

[Install]
WantedBy=multi-user.target
EOF

    # Create web editor service (if enabled)
    if [ "$ENABLE_WEB_EDITOR" = true ]; then
        cat > /etc/systemd/system/314sign-web-editor.service << EOF
[Unit]
Description=314Sign Web LMS Content Editor
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/web_editor.py --host 0.0.0.0 --port ${WEB_PORT}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=314sign-web-editor

[Install]
WantedBy=multi-user.target
EOF
    fi

    # Create splash screen service (if enabled)
    if [ "$ENABLE_SPLASH" = true ]; then
        cat > /etc/systemd/system/314sign-splash.service << EOF
[Unit]
Description=314Sign Boot Splash Screen
After=local-fs.target
Before=314sign-kiosk.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
ExecStart=${INSTALL_DIR}/splash_screen.py --config ${INSTALL_DIR}/splash_config.json
Restart=no
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF
    fi

    # Reload systemd
    systemctl daemon-reload

    # Enable services
    systemctl enable 314sign-kiosk.service
    echo -e "${CHECK} Kiosk service enabled"

    if [ "$ENABLE_WEB_EDITOR" = true ]; then
        systemctl enable 314sign-web-editor.service
        echo -e "${CHECK} Web editor service enabled"
    fi

    if [ "$ENABLE_SPLASH" = true ]; then
        systemctl enable 314sign-splash.service
        echo -e "${CHECK} Splash screen service enabled"
    fi

    echo ""
}

# Configure network
configure_network() {
    echo -e "${BLUE}${WIFI} Configuring network services...${NC}"

    # Enable and start Avahi
    systemctl enable avahi-daemon
    systemctl start avahi-daemon
    echo -e "${CHECK} mDNS service configured"

    # Configure firewall (basic)
    ufw --force enable
    ufw allow ssh
    ufw allow $KIOSK_PORT
    if [ "$ENABLE_WEB_EDITOR" = true ]; then
        ufw allow $WEB_PORT
    fi
    echo -e "${CHECK} Firewall configured"

    echo ""
}

# Create sample content
create_sample_content() {
    echo -e "${BLUE}${BOOK} Creating sample content...${NC}"

    # Copy example LMS files
    if [ -d "hybrid/examples" ]; then
        cp hybrid/examples/* $LMS_DIR/
        echo -e "${CHECK} Sample LMS files installed"
    fi

    # Copy templates
    if [ -d "hybrid/templates" ]; then
        cp hybrid/templates/* /var/lib/314sign/templates/
        echo -e "${CHECK} Content templates installed"
    fi

    echo ""
}

# Create utility scripts
create_utilities() {
    echo -e "${BLUE}${TOOLS} Creating utility scripts...${NC}"

    # Status check script
    cat > /home/pi/check_status.sh << 'EOF'
#!/bin/bash
echo "=== 314Sign Hybrid System Status ==="
echo "Device: $(hostname)"
echo "Uptime: $(uptime)"
echo "CPU Temp: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo ""

echo "Services:"
sudo systemctl status 314sign-kiosk.service --no-pager -l | grep -E "(Active|Loaded)"
sudo systemctl status 314sign-web-editor.service --no-pager -l 2>/dev/null | grep -E "(Active|Loaded)" || echo "Web Editor: Not enabled"
sudo systemctl status 314sign-splash.service --no-pager -l 2>/dev/null | grep -E "(Active|Loaded)" || echo "Splash: Not enabled"
echo ""

echo "Disk Usage:"
df -h / | tail -1
echo ""

echo "Network:"
ip addr show | grep "inet " | grep -v "127.0.0.1"
echo ""

echo "LMS Files:"
ls -la /home/pi/lms/ | wc -l | awk '{print $1-1 " files"}'
echo ""

echo "Configuration:"
cat /home/pi/kiosk_config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['mode'])" 2>/dev/null || echo "Config error"
EOF

    # Content management script
    cat > /home/pi/manage_content.sh << 'EOF'
#!/bin/bash
echo "=== 314Sign Content Management ==="
echo "LMS Directory: /home/pi/lms"
echo "Templates: /var/lib/314sign/templates"
echo "Backgrounds Cache: /var/lib/314sign/backgrounds"
echo ""

echo "Current LMS Files:"
ls -la /home/pi/lms/ 2>/dev/null || echo "No LMS directory"
echo ""

echo "Available Templates:"
ls -la /var/lib/314sign/templates/ 2>/dev/null || echo "No templates directory"
echo ""

echo "Usage:"
echo "  Place .lms files in /home/pi/lms/ for automatic display"
echo "  Templates are used by the web editor"
echo "  Background images are downloaded automatically"
echo "  Web Editor: http://$(hostname).local:8080"
echo "  Admin Console: python3 /opt/314sign/admin/314_admin.py"
EOF

    chmod +x /home/pi/check_status.sh
    chmod +x /home/pi/manage_content.sh

    echo -e "${CHECK} Utility scripts created"
    echo ""
}

# Final setup
final_setup() {
    echo -e "${BLUE}${SHIELD} Performing final setup...${NC}"

    # Set proper permissions
    chown -R pi:pi $INSTALL_DIR
    chown -R pi:pi /var/lib/314sign
    chown -R pi:pi $LMS_DIR

    # Clean up
    cd /
    rm -rf /tmp/314sign-install

    echo -e "${CHECK} Permissions set"
    echo -e "${CHECK} Cleanup completed"
    echo ""
}

# Print completion message
completion_message() {
    echo -e "${GREEN}${ROCKET} 314Sign Hybrid System Installation Complete!${NC}"
    echo ""
    echo -e "${WHITE}Installation Summary:${NC}"
    echo -e "  Version: ${SCRIPT_VERSION}"
    echo -e "  Device: ${DEVICE_NAME}"
    echo -e "  Hostname: ${NEW_HOSTNAME}"
    echo -e "  Mode: ${DEFAULT_MODE}"
    echo ""
    echo -e "${WHITE}Services Installed:${NC}"
    echo -e "  ${CHECK} Kiosk Display Service (314sign-kiosk)"
    if [ "$ENABLE_WEB_EDITOR" = true ]; then
        echo -e "  ${CHECK} Web Content Editor (314sign-web-editor)"
    fi
    if [ "$ENABLE_SPLASH" = true ]; then
        echo -e "  ${CHECK} Boot Splash Screen (314sign-splash)"
    fi
    echo ""
    echo -e "${WHITE}Access Points:${NC}"
    echo -e "  Web Editor: http://${NEW_HOSTNAME}.local:${WEB_PORT}"
    echo -e "  Admin Console: ssh pi@${NEW_HOSTNAME} then run 314_admin.py"
    echo -e "  Status Check: ~/check_status.sh"
    echo ""
    echo -e "${WHITE}Directories:${NC}"
    echo -e "  LMS Content: ${LMS_DIR}"
    echo -e "  Application: ${INSTALL_DIR}"
    echo -e "  Cache: /var/lib/314sign"
    echo ""
    echo -e "${WHITE}Next Steps:${NC}"
    echo -e "  1. Reboot: ${WHITE}sudo reboot${NC}"
    echo -e "  2. Add LMS content to ${LMS_DIR}"
    echo -e "  3. Access web editor for content creation"
    echo -e "  4. Use admin console for system management"
    echo ""
    echo -e "${CYAN}${GLOBE} Welcome to the future of digital signage!${NC}"
}

# Main installation function
main() {
    echo -e "${CYAN}${ROCKET} 314Sign Hybrid System Installer v${SCRIPT_VERSION}${NC}"
    echo -e "${WHITE}Complete digital signage platform with LMS rendering${NC}"
    echo ""

    # Pre-flight checks
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}${CROSS} Please run as root (sudo)${NC}"
        exit 1
    fi

    # Detect hardware
    detect_hardware

    # Confirm installation
    echo -e "${YELLOW}This will install 314Sign Hybrid System on your device.${NC}"
    echo -e "${YELLOW}Any existing 314Sign installation will be updated.${NC}"
    read -p "Continue with installation? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installation cancelled.${NC}"
        exit 0
    fi

    # Configuration options
    echo ""
    echo -e "${WHITE}Configuration Options:${NC}"
    read -p "Device mode (main/remote) [$DEFAULT_MODE]: " mode_input
    DEFAULT_MODE=${mode_input:-$DEFAULT_MODE}

    read -p "Display orientation (portrait/landscape) [$DEFAULT_ORIENTATION]: " orientation_input
    DEFAULT_ORIENTATION=${orientation_input:-$DEFAULT_ORIENTATION}

    read -p "Enable web editor? (y/n) [y]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        ENABLE_WEB_EDITOR=false
    fi

    read -p "Enable boot splash? (y/n) [y]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        ENABLE_SPLASH=false
    fi

    # Run installation steps
    update_system
    install_python_deps
    clone_repository
    create_directories
    install_application
    configure_device
    configure_boot
    configure_services
    configure_network
    create_sample_content
    create_utilities
    final_setup

    # Completion
    completion_message
}

# Run main function
main "$@"