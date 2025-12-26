# Requirements & System Setup

Hardware and software requirements for running 314Sign.

## Hardware Requirements

### Minimum Requirements
- **Raspberry Pi 3B+** or newer (Pi Zero 2 W recommended)
- **2GB RAM** minimum (4GB recommended)
- **16GB microSD card** minimum (32GB recommended)
- **Network connection** (Ethernet or Wi-Fi)

### Recommended Hardware
- **Raspberry Pi 4** or **Raspberry Pi 5**
- **4GB RAM** or more
- **32GB microSD card** or larger
- **Ethernet connection** for reliability
- **HDMI display** or touchscreen

### Display Options
- **Portrait or landscape** orientation supported
- **HDMI monitors** (recommended)
- **Touchscreens** supported
- **TV displays** (1080p or higher recommended)

## Software Requirements

### Operating System
- **Raspberry Pi OS Lite** (64-bit) - **Required**
- **Debian 11/12** or **Ubuntu 20.04+** (alternative)
- **macOS 12+** or **Windows 10+** (development only)

### Node.js & Tools
- **Node.js 18+** (LTS recommended)
- **npm 8+**
- **PM2** (process manager)
- **SQLite3** (database)
- **Git** (for updates)

## Network Requirements

### Connectivity
- **Local network access** (LAN/Wi-Fi)
- **DHCP** (automatic IP assignment)
- **DNS resolution** working
- **Port 80** available (default HTTP port)

### Remote Access (Optional)
- **SSH access** for administration
- **VPN** for remote management
- **Firewall** configuration if needed

## Installation Steps

### 1. Prepare Raspberry Pi
```bash
# Download Raspberry Pi OS Lite (64-bit)
# Flash to microSD card using Raspberry Pi Imager
# Enable SSH and Wi-Fi during imaging
# Boot Pi and connect via SSH
ssh pi@raspberrypi.local
```

### 2. Update System
```bash
# Update package lists
sudo apt update

# Upgrade system packages
sudo apt upgrade -y

# Install required tools
sudo apt install -y curl git htop
```

### 3. Install 314Sign
```bash
# One-command installation
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
```

### 4. Configure Kiosk Display (Optional)
```bash
# Auto-setup kiosk mode for Pi OS Lite
sudo ./scripts/os-lite-kiosk.sh

# Follow prompts for:
# - Screen rotation (0=normal, 90, 180, 270)
# - Browser selection (Chromium/Firefox)
```

### 5. Access Kiosk
```
Main kiosk: http://your-pi-hostname.local
Edit menus: http://your-pi-hostname.local/edit/
Design page: http://your-pi-hostname.local/design/
```

## Development Setup

### Local Development
```bash
# Clone repository
git clone https://github.com/UnderhillForge/314Sign.git
cd 314Sign

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

### Required Development Tools
- **Node.js 18+** with npm
- **Git** for version control
- **VS Code** (recommended editor)
- **Chrome/Firefox** for testing

## Performance Optimization

### Raspberry Pi Tuning
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Optimize memory usage
echo "gpu_mem=256" | sudo tee -a /boot/config.txt

# Use zram for swap compression
echo "zram" | sudo tee -a /etc/modules
```

### Network Optimization
- Use Ethernet over Wi-Fi when possible
- Configure static IP for reliability
- Disable power management on Wi-Fi

### Storage Optimization
- Use fast microSD cards (Class 10 or UHS-I)
- Regular log rotation
- Clean temp files periodically

## Security Considerations

### Basic Security
```bash
# Change default password
passwd

# Configure firewall (optional)
sudo apt install ufw
sudo ufw enable
sudo ufw allow 80
sudo ufw allow 22
```

### Access Control
- Change default admin password immediately
- Use strong passwords
- Limit SSH access to trusted networks
- Regularly update system packages

## Troubleshooting Installation

### Common Issues
- **"Permission denied"**: Run setup with `sudo`
- **"Command not found"**: Ensure curl is installed
- **Network timeout**: Check internet connection
- **Disk space**: Ensure 2GB+ free space

### Verification Steps
```bash
# Check Node.js installation
node --version
npm --version

# Check PM2 status
pm2 list

# Check web server
curl http://localhost/api/status

# Check database
ls -la 314sign.db
```

## Supported Browsers

### Display Browsers (Kiosk Mode)
- **Chromium** (recommended for Pi OS Lite)
- **Firefox ESR** (alternative)
- **Epiphany** (fallback)

### Editing Browsers
- **Chrome 90+**
- **Firefox 88+**
- **Safari 14+**
- **Edge 90+**
- **Mobile browsers** supported

## Backup & Recovery

### Automatic Backups
- Menu content saved to database
- Configuration preserved across updates
- Uploads stored in dedicated directories

### Manual Backup
```bash
# Backup critical files
tar -czf backup-$(date +%Y%m%d).tar.gz \
  314sign.db \
  config.json \
  bg/uploaded_* \
  fonts/*.ttf \
  logs/
```

## Support & Resources

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides available
- **Community**: Raspberry Pi forums for hardware help
- **Updates**: Automatic update system included
