# 314Sign — The Dead-Simple Digital Menu Board

**Version 1.0.2.2** | [License: CC BY-NC 4.0](LICENSE)

> **No apps. No subscriptions. No learning curve.**  
> Point your phone at http://your-pi.local/start → edit → see changes **instantly** on screen.

A modern, self-hosted digital signage solution built with Node.js/TypeScript and SQLite database. Perfect for restaurants, cafés, churches, and community spaces that need simple, reliable menu boards without complexity.

## ✨ Key Features

### 🚀 Self-Hosted & Modern
- **Node.js/TypeScript backend** with Express server and SQLite database
- **RESTful API** for all operations
- **Zero external dependencies** after setup
- **Full TypeScript type safety** and modern JavaScript features

### 🎨 Professional Customization
- **Per-menu styling**: Each menu gets its own font and size
- **Upload backgrounds from your phone**: Snap a photo → upload → instant background
- **6+ professional fonts included**: Lato, Bebas Neue, Caveat, and more
- **Brightness control**: Adjust background brightness (20-150%)
- **Logo overlay**: Add business logos with adjustable size and transparency

### ⚡ Smart Features
- **Auto-format button**: ✨ One-click styling for menu items and prices
- **Time-based rules**: Automatically switch menus by time of day
- **Slideshow system**: Create multimedia presentations with images and videos
- **Menu history**: 7-day backup with one-click restore
- **Live preview**: See changes before saving
- **Color tags**: `{y}$8.95` yellow prices, `{r}` red text, and more
- **Real-time updates**: Changes appear instantly on kiosk display

### 🛠️ Built for Production
- **PM2 process management** for reliable operation
- **Automatic service startup** on boot
- **Health monitoring** and status endpoints
- **Professional logging** and error handling
- **One-command installation** for Raspberry Pi

---

## Quick Start (5 Minutes)

### Installation
```bash
# 1. Flash Raspberry Pi OS Lite 64-bit to microSD
# 2. Boot Pi, enable SSH (sudo raspi-config → Interface → SSH)
# 3. Connect to Wi-Fi, set hostname (optional: sudo raspi-config → System → Hostname)
# 4. Run one-command setup:
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash

# 5. Open on any device (replace YOUR-HOSTNAME with your Pi's hostname):
http://YOUR-HOSTNAME.local/start/          # Quick access landing page
http://YOUR-HOSTNAME.local/edit/           # Edit daily specials
http://YOUR-HOSTNAME.local/design/         # Customize appearance
http://YOUR-HOSTNAME.local/rules/          # Schedule auto-switching
http://YOUR-HOSTNAME.local/slideshows/     # Create multimedia slideshows
```

### Development Setup
```bash
# Clone repository
git clone https://github.com/UnderhillForge/314Sign.git
cd 314Sign

# Install dependencies
npm install

# Build TypeScript
npm run build

# Start development server
npm run dev

# Or start production server
npm start
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

### Remote Kiosks (Multiple Displays)
For multi-display setups, set up additional Raspberry Pis as remote kiosks that sync with your main kiosk:

```bash
# On each remote Pi (Pi Zero 2 W recommended):
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remote-setup.sh | sudo bash

# Features:
# - Hardware-based unique device identification
# - Automatic network discovery of main kiosk
# - Real-time sync of menus, slideshows, and configurations
# - Emergency admin panel for troubleshooting
# - Screen rotation support (portrait/landscape)
# - Auto-boot kiosk mode
```

After setup, register each remote device with your main kiosk using the displayed 6-character code.

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

## API Endpoints

The RESTful API provides programmatic access to all features:

### Core System
- `GET /api/status` - Server health and configuration status
- `GET /api/system/info` - System information and diagnostics

### Configuration
- `GET /api/config` - Get current kiosk configuration
- `POST /api/config` - Update configuration (merge)
- `PUT /api/config` - Replace entire configuration

### Menu Management
- `GET /api/menu` - List all menus
- `GET /api/menu/:name` - Get specific menu content
- `PUT /api/menu/:name` - Update menu content
- `DELETE /api/menu/:name` - Delete menu
- `GET /api/menu/:name/history` - Get menu version history

### Rules & Scheduling
- `GET /api/rules` - List all scheduling rules
- `POST /api/rules` - Create new rule
- `PUT /api/rules/:id` - Update rule
- `DELETE /api/rules/:id` - Delete rule

### File Management
- `GET /api/backgrounds` - List background images
- `GET /api/fonts` - List available fonts
- `POST /api/upload/bg` - Upload background image
- `POST /api/upload/media` - Upload media file
- `DELETE /api/upload/bg/:filename` - Delete background image

### System Control
- `POST /api/system/reload` - Trigger kiosk reload
- `GET /api/auth/me` - Get current user info (authenticated)

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

## Maintenance & Management

### PM2 Process Management
```bash
# Check server status
pm2 list

# View logs
pm2 logs 314sign

# Restart server
pm2 restart 314sign

# Stop server
pm2 stop 314sign

# Monitor processes
pm2 monit
```

### Health Check
```bash
# Check system status
curl http://YOUR-HOSTNAME.local/api/status

# Returns JSON: version, uptime, menu stats, config status
```

### Manual Backup (SSH)
```bash
# Save menus, configs, and uploaded images
/var/www/html/scripts/backup.sh

# Or specify custom location
/var/www/html/scripts/backup.sh /home/pi/my-backups
```

### Development
```bash
# Run tests
npm test

# Run with auto-reload during development
npm run dev

# Build for production
npm run build
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

**314Sign v1.0.2.2**
Licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)

- ✅ Free for personal, educational, and non-profit use
- ✅ Modify and share with attribution
- ❌ Commercial use requires permission (contact maintainer)

**Perfect for**: Restaurants, cafés, church halls, private clubs, home kitchens, community centers, office break rooms.

Built with ❤️ for small businesses and community spaces that deserve better than overpriced subscription services.
