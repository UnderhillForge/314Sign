# 314Sign — The Dead-Simple Digital Menu Board

**Version 0.8.0** | [License: CC BY-NC 4.0](LICENSE)

> **No apps. No logins. No tech skills.**  
> Just point a mobile browser at edit.html, make changes, and **watch it update instantly** on screen.

314Sign turns any **Raspberry Pi** (with fullpageOS or Raspberry Pi OS Lite 64-bit) into a **beautiful, live-updating digital sign** — perfect for **restaurants, private clubs, cafés, or kitchens**.

---

## Features

| Feature | Why It Matters |
|-------|----------------|
| **Edit from any phone** | Staff use their own device — no training needed |
| **Live preview & instant update** | Changes appear in **< 3 seconds** |
| **Custom backgrounds & fonts** | Match your brand with Comic Sans, handwriting, or elegance |
| **Upload photos from phone** | Snap a special → upload → done |
| **Zero apps or accounts** | Works on **Wi-Fi only**, no internet required |
| **Auto-reload kiosk** | No manual refresh — just works |

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

---

## License & Credits

**314Sign v0.8.0**  
Licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)

- ✅ Free for personal, educational, and non-profit use
- ✅ Modify and share with attribution
- ❌ Commercial use requires permission

For commercial licensing, contact the project maintainer.

Built with ❤️ for small businesses and community spaces.
