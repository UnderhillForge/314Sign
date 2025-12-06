# 314Sign — The Dead-Simple Digital Menu Board

**Version 0.9.2** | [License: CC BY-NC 4.0](LICENSE)

> **No apps. No subscriptions. No learning curve.**  
> Point your phone at http://your-pi.local/start → edit → see changes **instantly** on screen.

## Why Choose 314Sign?

**Most digital signage solutions are overkill.** They force you to install apps, create accounts, and learn complex interfaces. 314Sign is different.

### ✨ It Just Works
- **Staff-ready in 30 seconds**: Open a browser, type or tap the URL, start editing. No apps to download, no accounts to create, no training needed.
- **Edit from anything**: iPhone, Android, iPad, laptop — if it has a browser, it works.
- **See changes instantly**: Hit save → kiosk updates in under 3 seconds. No refresh button, no waiting.

### 🚀 Self-Hosted & Private
- **Runs on your network**: Everything local — no cloud dependencies, no internet required after setup.
- **You own the hardware**: Raspberry Pi-based solution with full control.
- **Privacy first**: Your menus stay on your premises. No data sent to third parties.

### 🎨 Customization That Makes Sense
- **Per-menu styling**: Each menu gets its own font and size. Perfect for any use case—food menus, event schedules, promotional content—each can have a distinct look.
- **Upload backgrounds from your phone**: Snap a photo of today's special → upload → done. No desktop computer needed.
- **6+ professional fonts included**: From clean and modern (Lato, Bebas Neue) to handwritten fun (Caveat, Walter Turncoat). Add your own TTF fonts anytime.
- **Brightness control**: Darken backgrounds (20-150%) so text pops without editing images.

### ⚡ Smart Features That Save Time
- **Auto-format button**: ✨ One-click color styling for menu items, prices, and descriptions.
- **Auto-schedule menus**: Define time-based rules (e.g., breakfast 7-11am, lunch 11am-3pm, dinner 5-10pm). Kiosk switches automatically.
- **Slideshow system**: Create multimedia presentations with images, videos, and text. Schedule ads during closed hours or rotate promotional content.
- **7-day menu history**: Made a mistake? Restore yesterday's menu with one tap.
- **Active rule display**: Edit page shows which menu is currently live on the kiosk.
- **Color tags**: `{y}$8.95` for yellow prices, `{r}` for red text, and more.
- **Live preview**: See exactly how your menu looks before saving.

### 🛠️ Built for Real-World Use
- **Works offline**: Wi-Fi-only operation. Perfect for restaurants, private clubs, church halls.
- **One-command setup**: `curl | sudo bash` → grab coffee → it's installed.
- **SSH-only management**: No keyboard/mouse needed on the Pi after initial setup.
- **Raspberry Pi OS compatible**: Works with fullpageOS (auto-kiosk) or Pi OS Lite (minimal X11 setup).

---

## Quick Start (5 Minutes)

```bash
# 1. Flash Raspberry Pi OS Lite 64-bit or fullpageOS to microSD
# 2. Boot Pi, enable SSH (sudo raspi-config → Interface → SSH)
# 3. Connect to Wi-Fi, set hostname (optional: sudo raspi-config → System → Hostname)
# 4. Run one-command setup:
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash

# 5. Open on any device (replace YOUR-HOSTNAME with your Pi's hostname):
http://YOUR-HOSTNAME.local/start/     # Quick access landing page
http://YOUR-HOSTNAME.local/edit/      # Edit daily specials
http://YOUR-HOSTNAME.local/design/    # Customize appearance
http://YOUR-HOSTNAME.local/rules/     # Schedule auto-switching
http://YOUR-HOSTNAME.local/slideshows/ # Create multimedia slideshows
```

### Recommended: Auto-Boot to Kiosk Display (Pi OS Lite)
For Pi OS Lite installations, configure the Pi to automatically show your menu on boot:

```bash
# Install minimal X11 + Chromium kiosk mode
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash
sudo reboot

# Features:
# - Prompts for screen rotation (0=normal, 1=90°, 2=180°, 3=270°)
# - Auto-detects Chromium or Firefox ESR
# - Re-runnable to change rotation without reinstalling
```

**Note**: FullpageOS users skip this step — kiosk mode is built-in.

---

## What You Can Do

| Feature | Description |
|---------|-------------|
| **Edit from any phone** | Staff use their own devices — zero training required |
| **✨ Auto-format** | One-click styling for items, prices, and descriptions with customizable colors |
| **Live preview** | See changes as you type before saving |
| **7-day history** | Restore previous versions with one click |
| **Auto-schedule** | Content switches by time of day based on rules you define |
| **Slideshows** | Create multimedia presentations with images, videos, and text overlays |
| **Per-menu fonts & sizes** | Each menu gets its own style (font + size) |
| **Upload photos** | Snap → upload → instant background |
| **Color tags** | `{r}` red `{y}` yellow `{g}` green `{b}` blue `{o}` orange `{p}` pink `{w}` white `{lg}` light grey |
| **Text alignment** | `[center]...[/center]` and `[right]...[/right]` tags |
| **Size overrides** | `[s15]bigger text[/s]` for emphasis |
| **Background brightness** | Adjust 20-150% for text readability |
| **Custom fonts** | Drop TTF files in fonts/ directory — auto-loads |
| **Remote reload** | Force kiosk refresh from edit page |
| **Transition effects** | 6 slideshow transitions: fade, slide, zoom |

---

## Maintenance & Updates

### Web-Based Maintenance Panel
Access at `http://YOUR-HOSTNAME.local/maintenance/` for:
- **Create Backups**: One-click backup of menus, configs, and uploaded images
- **Apply Updates**: Pull latest features from GitHub with automatic backup
- **Restart Server**: Reload lighttpd after manual changes
- **View System Status**: Check version, uptime, disk space

**Note**: Requires `sudoers-314sign` to be installed (automatically configured by `setup-kiosk.sh`). If backup fails with "Permission denied", run:
```bash
sudo cp /var/www/html/sudoers-314sign /etc/sudoers.d/314sign
sudo chmod 0440 /etc/sudoers.d/314sign
sudo visudo -cf /etc/sudoers.d/314sign  # Validate
```

### Manual Backup (SSH)
```bash
# Save menus, configs, and uploaded images to /var/backups/314sign/
sudo /var/www/html/scripts/backup.sh

# Or specify custom location
sudo /var/www/html/scripts/backup.sh /home/pi/my-backups
```

### Update from GitHub (SSH)
```bash
# Preview what would change (safe, makes no modifications)
sudo /var/www/html/scripts/update-from-github.sh --dry-run

# Update with auto-backup before applying changes
sudo /var/www/html/scripts/update-from-github.sh --backup

# Quick update (no backup)
sudo /var/www/html/scripts/update-from-github.sh

# What updates: Core HTML/PHP, scripts, default backgrounds
# What's preserved: Your menus, configs, uploaded images
```

### Health Check
```bash
# Check system status
curl http://YOUR-HOSTNAME.local/status.php

# Returns JSON: version, uptime, menu stats, disk space
```

---

## Documentation

- **[Formatting Guide](docs/FORMATTING.md)** — Color tags, alignment, size overrides
- **[Slideshow Guide](docs/SLIDESHOWS.md)** — Create multimedia presentations with images, videos, and text
- **[Troubleshooting](docs/troubleshooting.md)** — Common issues and fixes
- **[Requirements](docs/requirements.md)** — Hardware, software, network setup
- **[Contributing](docs/contributing.md)** — How to improve 314Sign

---

## License & Credits

**314Sign v0.9.2**  
Licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)

- ✅ Free for personal, educational, and non-profit use
- ✅ Modify and share with attribution
- ❌ Commercial use requires permission (contact maintainer)

**Perfect for**: Restaurants, cafés, church halls, private clubs, home kitchens, community centers, office break rooms.

Built with ❤️ for small businesses and community spaces that deserve better than overpriced subscription services.
