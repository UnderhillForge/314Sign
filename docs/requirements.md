# 314Sign Requirements

What you need to run 314Sign — hardware, software, and network setup.

---

## Hardware

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Raspberry Pi** | Pi 4 (4GB+) or Pi 5 | Tested on Pi 5; Pi 4 works great too |
| **MicroSD Card** | 16GB+ (Class 10) | 32GB recommended for room to grow |
| **Display** | Any HDMI monitor/TV | 1080p+ recommended |
| **Network** | Wi-Fi or Ethernet | Local network only — no internet needed after setup |
| **Power** | Official Pi power supply | Stable power prevents corruption |

**Total cost**: ~$100-150 if buying everything new (Pi + SD card + case + power)

---

## Software

### Operating System (Choose One)

**Option 1: Raspberry Pi OS Lite (Recommended)**
- Lightweight, no desktop bloat
- One-command kiosk mode installer included
- Best performance for dedicated signage

**Option 2: FullpageOS**
- Pre-configured kiosk mode out of the box
- Boots straight to fullscreen browser
- Great if you want zero configuration

### What Gets Installed

The `setup-kiosk.sh` script installs:
- **lighttpd** — Fast, lightweight web server
- **PHP** (with CGI) — For image uploads and file listing
- **avahi-daemon** — mDNS service for .local hostname resolution
- **git** — To clone the repository
- **qrencode** — Generate QR codes for mobile access

**Total install size**: ~50MB. No Node.js, no databases, no heavy frameworks.

---

## Network Setup

### What You Need
- **Local Wi-Fi or Ethernet**: Pi must be on same network as staff phones/tablets
- **mDNS (Avahi)**: Lets you use `http://hostname.local` instead of IP addresses (**automatically installed by setup script**)
- **Open ports**: 80 (HTTP), 22 (SSH)

### No Internet Required
After initial setup, 314Sign runs **100% offline**. Perfect for:
- Restaurant private networks
- Church halls without internet
- VFW posts and private clubs
- Locations with unreliable connectivity

---

## Installation

### Prerequisites
1. Flash Raspberry Pi OS Lite 64-bit to microSD (use Raspberry Pi Imager)
2. Boot Pi, enable SSH: `sudo raspi-config` → Interface Options → SSH
3. Connect to Wi-Fi: `sudo raspi-config` → System Options → Wireless LAN
4. Optional but recommended: Set hostname: `sudo raspi-config` → System Options → Hostname

### One-Command Install
```bash
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
```

**That's it.** The script handles everything:
- Installs dependencies (lighttpd, PHP, avahi-daemon, etc.)
- Configures lighttpd + WebDAV
- Sets up file permissions
- Generates QR codes for mobile access
- **Optional**: Disables undervoltage warnings (prompts during installation)

### Post-Installation Options

**Kiosk Display Mode** (Optional)
- During installation, you'll be asked if you want to set up auto-boot kiosk mode
- Installs minimal X11 + Chromium browser for fullscreen display
- Configures screen rotation options
- Pi boots directly to kiosk display instead of console
- Can be set up later if skipped during installation

**Undervoltage Warning Override** (Optional)
- During installation, you'll be asked if you want to disable undervoltage warnings
- Adds `avoid_warnings=1` to `/boot/config.txt`
- Useful if you have a good power supply but still get warnings
- Can be safely skipped - warnings help diagnose power issues

### Optional: Auto-Boot to Kiosk (Pi OS Lite)
If you want the Pi to automatically display the menu on boot:

```bash
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash
sudo reboot
```

This installs minimal X11 + Chromium and configures fullscreen kiosk mode with optional screen rotation.

---

## What You Don't Need

❌ **No keyboard/mouse** — SSH-only after initial setup  
❌ **No desktop environment** — Runs headless or minimal kiosk  
❌ **No database** — Everything is JSON and text files  
❌ **No cloud account** — Fully self-hosted  
❌ **No monthly fees** — Own it forever  
❌ **No internet connection** — Works 100% offline after setup

---

## Browser Compatibility

### For Editing (Staff Devices)
Works on any modern browser:
- ✅ Safari (iOS/iPad/Mac)
- ✅ Chrome (Android/Windows/Mac)
- ✅ Firefox (Windows/Mac/Linux)
- ✅ Edge (Windows)

### For Kiosk Display
- ✅ Chromium (default on Pi)
- ✅ Firefox ESR (fallback option)

---

## Optional Enhancements

### Custom Fonts
Drop TTF font files into `/var/www/html/fonts/` and they'll auto-load in the editor dropdown.

### More Backgrounds
Add images via:
- Upload through design page (from phone camera)
- SCP/SFTP: Copy to `/var/www/html/bg/`
- USB stick: Mount and copy files

### Automated Backups
Add to crontab for daily backups:
```bash
# Edit crontab
sudo crontab -e

# Add this line (runs at 2am daily)
0 2 * * * /var/www/html/scripts/backup.sh /home/pi/backups
```

---

## Need Help?

- 📖 **Troubleshooting**: See [troubleshooting.md](troubleshooting.md)
- 🎨 **Formatting**: See [FORMATTING.md](FORMATTING.md)
- 🤝 **Contributing**: See [contributing.md](contributing.md)
- �� **Issues**: [GitHub Issues](https://github.com/UnderhillForge/314Sign/issues)

---

**314Sign: Simple requirements, powerful results.**
