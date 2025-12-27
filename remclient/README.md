# 314Sign Remote Client

This directory contains files that belong on remote kiosk devices, not the main 314Sign server.

## Files

### `remote-setup.sh`
Installation script for setting up remote kiosk devices. Downloads and configures:
- Raspberry Pi OS Lite with kiosk mode
- lighttpd web server for minimal hosting
- Chromium browser in fullscreen kiosk mode
- Automatic device registration with main kiosk

**Usage:**
```bash
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/remote-setup.sh | sudo bash
```

### `remote.html`
Main remote display interface that:
- Shows device registration code when unregistered
- Displays assigned content (menu/slideshow/mirror) when registered
- Polls main kiosk for configuration updates
- Falls back to cached content when offline

### `update-remote-config.php`
PHP endpoint for receiving configuration updates from the main kiosk:
- Accepts POST requests with new configuration
- Merges updates with existing settings
- Stores configuration in `remote-config.json`

## Architecture

Remote devices are **hybrid thin clients** that:
- Get most content from the main kiosk server
- Maintain minimal local storage for offline/cached content
- Receive configuration updates via HTTP
- Display registration codes before connection

## Installation Flow

1. Run `remote-setup.sh` on fresh Raspberry Pi
2. Device generates unique ID and displays registration code
3. Admin registers device code in main kiosk interface
4. Remote receives configuration and begins displaying content
5. Remote polls for updates and maintains offline fallback

## Requirements

- Raspberry Pi Zero 2 W or similar
- Raspberry Pi OS Lite 32-bit
- Internet connection for initial setup
- HDMI display for kiosk output

## Maintenance

- Remote devices are largely self-maintaining
- Configuration updates happen automatically
- Content updates pull from main kiosk
- No manual intervention required after initial setup
