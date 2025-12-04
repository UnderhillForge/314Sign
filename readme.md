# 314Sign — The Dead-Simple Digital Menu Board

**Version 0.9.1** | [License: CC BY-NC 4.0](LICENSE)

> **No apps. No logins. No tech skills.**  
> Just point a mobile browser at edit.html, make changes, and **watch it update instantly** on screen.

314Sign turns any **Raspberry Pi** (with fullpageOS or Raspberry Pi OS Lite 64-bit) into a **beautiful, live-updating digital sign** — perfect for **restaurants, private clubs, cafés, or kitchens**.

---

## Features

| Feature | Why It Matters |
|-------|----------------|
| **Edit from any phone** | Staff use their own device — no training needed |
| **Quick start page** | Simple landing page with links to all tools |
| **Live preview & instant update** | Changes appear in **< 3 seconds** |
| **Active rule display** | See which menu is currently live on kiosk |
| **7-day menu history** | Restore previous versions with one click |
| **Auto-schedule menus** | Breakfast/lunch/dinner switch by time of day |
| **Custom backgrounds & fonts** | Match your brand with 12+ font options |
| **Background brightness** | Adjust darkness (20-150%) for text readability |
| **Header & text sizing** | Independent control for header (5-20%) and body (5-20%) |
| **Upload photos from phone** | Snap a special → upload → done |
| **Emoji toolbar** | Quick-insert 🍔🍕🍗🥗🍰☕🍺🍷 |
| **Text alignment** | Center or right-align text with tags |
| **Color tags** | {r}red {y}yellow {g}green {b}blue and more |
| **Size override tags** | [s15]bigger text[/s] for emphasis |
| **Zero apps or accounts** | Works on **Wi-Fi only**, no internet required |
| **Remote reload trigger** | Force kiosk refresh from edit page |

---

## Quick Start (5 Minutes)

```bash
# 1. Flash fullpageOS or Raspberry Pi OS Lite 64-bit
# 2. Boot, enable SSH, connect to Wi-Fi
# 3. Set hostname (optional): sudo raspi-config -> System -> Hostname
# 4. Run the one-click setup:
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash

# 5. Open in browser (replace with your hostname):
http://YOUR-HOSTNAME.local
http://YOUR-HOSTNAME.local/start/
http://YOUR-HOSTNAME.local/edit/
http://YOUR-HOSTNAME.local/design/
http://YOUR-HOSTNAME.local/rules/
```

### Pi OS Lite: Optional Kiosk Mode
If using Raspberry Pi OS Lite and want the Pi to auto-boot to fullscreen display:

```bash
# Install minimal X11 + Chromium kiosk (after main setup)
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash
sudo reboot
```

**Features:**
- Prompts for screen rotation (0=normal, 1=90°, 2=180°, 3=270°)
- Auto-detects and installs Chromium or Firefox ESR
- Re-runnable: change rotation anytime without reinstalling
- Configures auto-login and fullscreen kiosk mode

---

## Maintenance & Monitoring

### Backup Your Data
```bash
# Run backup script (saves to /var/backups/314sign/)
sudo /var/www/html/scripts/backup.sh

# Or specify custom backup location
sudo /var/www/html/scripts/backup.sh /home/pi/backups
```

### Health Check
```bash
# Check system status (replace YOUR-HOSTNAME with your actual hostname)
curl http://YOUR-HOSTNAME.local/status.php

# Returns JSON with version, uptime, menu status, disk space
```

### Auto-Schedule Menus
Visit `http://YOUR-HOSTNAME.local/rules/` to configure time-based menu switching (e.g., breakfast 7-11am, lunch 11am-3pm, dinner 5-10pm).

### Update from GitHub
Keep your installation in sync with the latest version:
```bash
# Check what would be updated (safe - makes no changes)
sudo /var/www/html/scripts/update-from-github.sh --dry-run

# Update with automatic backup
sudo /var/www/html/scripts/update-from-github.sh --backup

# Quick update (no backup)
sudo /var/www/html/scripts/update-from-github.sh
```

**What gets updated**: Core HTML/PHP files, scripts, default backgrounds  
**What's preserved**: Your menus, config.json, rules.json, uploaded images

### Change Screen Rotation (Pi OS Lite)
Re-run the kiosk script to update rotation without reinstalling:
```bash
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash
sudo reboot
```

---

## License & Credits

**314Sign v0.9.1**  
Licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)

- ✅ Free for personal, educational, and non-profit use
- ✅ Modify and share with attribution
- ❌ Commercial use requires permission

For commercial licensing, contact the project maintainer.

Built with ❤️ for small businesses and community spaces.
