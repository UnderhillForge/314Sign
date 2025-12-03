# 314Sign — The Dead-Simple Digital Menu Board

**Version 0.8.0** | [License: CC BY-NC 4.0](LICENSE)

> **No apps. No logins. No tech skills.**  
> Just point a mobile browser at edit.html, make changes, and **watch it update instantly** on screen.

314Sign turns any **Raspberry Pi 5 + fullpageOS** into a **beautiful, live-updating digital sign** — perfect for **restaurants, private clubs, cafés, or kitchens**.

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
# 1. Flash fullpageOS on your Pi 5
# 2. Boot, enable SSH, connect to Wi-Fi
# 3. Run the one-click setup:
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash

# 4. Open in browser:
http://raspberrypi.local
http://raspberrypi.local/edit/
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
# Check system status
curl http://raspberrypi.local/status.php

# Returns JSON with version, uptime, menu status, disk space
```

### Auto-Schedule Menus
Visit `http://raspberrypi.local/rules/` to configure time-based menu switching (e.g., breakfast 7-11am, lunch 11am-3pm, dinner 5-10pm).

---

## License & Credits

**314Sign v0.8.0**  
Licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)

- ✅ Free for personal, educational, and non-profit use
- ✅ Modify and share with attribution
- ❌ Commercial use requires permission

For commercial licensing, contact the project maintainer.

Built with ❤️ for small businesses and community spaces.
