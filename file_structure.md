# 314Sign File Structure

```
/var/www/html/
├── index.html                  # Kiosk display (auto-updates every 3s)
├── config.json                 # Settings: background, font, sizes, brightness
├── rules.json                  # Auto-schedule rules for menu switching
├── reload.txt                  # Remote reload trigger for kiosk
├── favicon.svg                 # Site icon
├── status.php                  # System health check endpoint
├── save-menu-history.php       # Backend for 7-day history
├── get-menu-history.php        # Backend for history retrieval
├── setup-kiosk.sh              # One-click installer
├── permissions.sh              # File permission setup
├── create-webdav-user.sh       # Optional WebDAV authentication
│
├── start/                      # Quick start landing page
│   └── index.html              # Links to edit/design/rules pages
│
├── edit/                       # Menu editor interface
│   └── index.html              # Edit breakfast/lunch/dinner/closed menus
│
├── design/                     # Style configuration
│   ├── index.html              # Background, font, header, brightness
│   └── upload-bg.php           # Image upload handler
│
├── rules/                      # Schedule configuration
│   └── index.html              # Time-based menu switching rules
│
├── menus/                      # Menu content files
│   ├── breakfast.txt           # Breakfast menu
│   ├── lunch.txt               # Lunch menu
│   ├── dinner.txt              # Dinner menu
│   └── closed.txt              # Closed message
│
├── history/                    # Menu version history (7 days)
│   └── [menu]_YYYY-MM-DD_Day_HHMMSS.txt
│
├── bg/                         # Background images
│   ├── index.php               # Image list API
│   ├── backgd.jpg              # Default background
│   ├── uploaded_*.jpg          # User-uploaded images
│   └── [other defaults]        # Additional default images
│
├── logs/                       # System logs
│   ├── uploads.log             # Image upload events
│   └── history.log             # Menu save events
│
└── scripts/                    # Maintenance utilities
    ├── backup.sh               # Backup menus/config/images
    ├── os-lite-kiosk.sh        # Convert Pi OS Lite to kiosk
    └── update-from-github.sh   # Sync with GitHub releases
```

## Key Configuration Files

### config.json
```json
{
  "bg": "backgd.jpg",
  "font": "'Comic Sans MS', cursive",
  "pollIntervalSeconds": 3,
  "fontScalePercent": 5,
  "headerSizePercent": 5,
  "bgBrightness": 1.0,
  "headerText": "Specials",
  "showClock": false,
  "clock24Hour": true,
  "availableFonts": { ... }
}
```

### rules.json
```json
{
  "enabled": true,
  "rules": [
    {
      "name": "Breakfast Hours",
      "days": ["monday", "tuesday", ...],
      "startTime": "07:00",
      "endTime": "11:00",
      "menu": "menus/breakfast.txt"
    }
  ]
}
```

## WebDAV Editable Files

Configured in `/etc/lighttpd/conf-enabled/10-webdav.conf`:
- index.html
- config.json
- rules.json
- reload.txt
- menus/*.txt
- edit/index.html
- design/index.html
- rules/index.html

## Generated QR Codes
- qr-start.png → http://hostname.local/start/
- qr-edit.png → http://hostname.local/edit/
- qr-design.png → http://hostname.local/design/
- qr-rules.png → http://hostname.local/rules/
```
