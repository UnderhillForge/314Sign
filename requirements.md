# 314Sign Requirements

This document outlines the **hardware, software, and setup prerequisites** for running **314Sign** — the dead-simple digital signage kiosk for Raspberry Pi 5 + fullpageOS.

314Sign is designed to be **lightweight and dependency-minimal**, so you can get up and running in **under 5 minutes** with the one-click installer. No complex builds or external services required.

---

## Hardware Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Raspberry Pi Model** | Pi 5 (4GB+) | Pi 5 (8GB) | Tested on Pi 5; older models may work but with slower image uploads |
| **Storage** | 8GB microSD | 32GB+ microSD (Class 10) | FullpageOS image takes ~4GB; room for backgrounds |
| **Display** | HDMI monitor/TV (1024x768+) | 1080p+ touchscreen | Kiosk mode fills screen automatically |
| **Network** | Wi-Fi (2.4GHz/5GHz) | Ethernet | Local network only — no internet needed |
| **Power** | Official 5V/5A USB-C | Same | Stable power prevents glitches |
| **Peripherals** | Keyboard/mouse (for initial setup) | None (headless after install) | SSH access recommended |

> **Total Cost**: ~$100 (Pi 5 + SD + case) if starting fresh.

---

## Software Requirements

### Operating System
- **Primary**: [FullpageOS](https://github.com/guysoft/FullPageOS) (latest stable)
  - Why? Built-in kiosk mode (Chromium fullscreen) — no extra config.
  - Download: Flash via Raspberry Pi Imager.
- **Alternative**: Raspberry Pi OS Lite (64-bit) + minimal X11 kiosk setup
  - Lightweight kiosk mode without full desktop environment
  - One-command setup: `curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash`
  - See `scripts/os-lite-kiosk.sh` for details

### Server & Runtime
- **Web Server**: lighttpd (1.4.50+)
  - Handles static files, PHP, and WebDAV for edits.
- **PHP**: PHP 7.4+ (with CGI/FPM)
  - For image uploads (`upload-bg.php`) and file listing (`bg/index.php`).
- **No Database**: Everything is file-based (JSON + TXT).

### Installed Packages
The `setup-kiosk.sh` script installs these automatically:

| Package | Version | Purpose | Install Command (Manual) |
|---------|---------|---------|--------------------------|
| `lighttpd` | Latest | Web server | `sudo apt install lighttpd` |
| `php-cgi` | Latest | PHP runtime | `sudo apt install php-cgi` |
| `git` | Latest | Clone repo | `sudo apt install git` |
| `qrencode` | Latest | Generate QR codes | `sudo apt install qrencode` |
| `inotify-tools` | Latest | File change detection | `sudo apt install inotify-tools` |
| `xdotool` | Latest | Auto-refresh kiosk (F5 key) | `sudo apt install xdotool` |

> **Total Install Size**: ~50MB. No heavy frameworks (e.g., no Node.js, no Python).

---

## Network & Environment Requirements

- **Local Wi-Fi Network**: Pi must be on the same network as staff phones/tablets.
  - Hostname: `raspberrypi.local` (auto-resolved via mDNS; install Avahi if needed: `sudo apt install avahi-daemon`).
- **Firewall**: None required (closed network assumed).
- **Ports**:
  - 80 (HTTP) — for kiosk and editors.
  - 22 (SSH) — for initial setup.
- **Internet Access**: Only during install (for `apt` and `git clone`). Offline after.
- **Browser**: Any modern (Chrome, Safari, Firefox) on staff devices for editors.

---

## Setup Prerequisites

Before running `setup-kiosk.sh`:

1. **Flash & Boot**:
   - Download FullpageOS image.
   - Flash to microSD with Raspberry Pi Imager.
   - Boot Pi → Connect HDMI/keyboard for first run (enable SSH: `sudo raspi-config` → Interface Options → SSH).

2. **Network Config**:
   - Join Wi-Fi: Edit `/boot/wpa_supplicant.conf` or use `raspi-config`.
   - SSH in: `ssh pi@raspberrypi.local` (default password: `raspberry`).

3. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo reboot
   ```

4. **Run Installer**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
   ```

> **Post-Install**: Point your kiosk browser to `http://raspberrypi.local/index.html`.

---

## Optional Enhancements

| Add-On | Why? | How? |
|--------|------|------|
| **Touchscreen Support** | For interactive kiosks | Use official Pi display; enable in `raspi-config` |
| **Backup Script** | Auto-save configs | Add cron job: `crontab -e` → `0 2 * * * rsync -av /var/www/html/ /backup/` |
| **HTTPS** | If exposing publicly | Install certbot: `sudo apt install certbot` + `sudo certbot --nginx` (switch to Nginx?) |
| **More Backgrounds** | Variety | Drop JPG/PNG into `/var/www/html/bg/` via SCP |

---

## Troubleshooting Common Issues

- **"Permission denied" on upload**: Re-run `setup-kiosk.sh` (fixes ownership).
- **Thumbnails not loading**: Check `sudo tail -f /var/log/lighttpd/error.log`.
- **Kiosk not fullscreen**: In FullpageOS, edit `/etc/xdg/lxsession/LXDE-pi/autostart` → `@chromium --kiosk http://raspberrypi.local/index.html`.
- **No mDNS**: Install Avahi and reboot.

For more, see [CONTRIBUTING.md](CONTRIBUTING.md) or open an [issue](https://github.com/UnderhillForge/314Sign/issues).

---

**314Sign: Minimal deps, maximum simplicity.**  
Questions? Ping us in Discussions.

--- 

*Last Updated: November 12, 2025*
