# 314Sign Remote Client

This directory contains files that belong on remote kiosk devices, not the main 314Sign server.

## Files

### `remote-setup.sh`
Simplified setup script for FullPageOS systems. Configures the existing browser to display the remote interface:
- Detects FullPageOS installation
- Installs lighttpd web server for local content hosting
- Copies remote interface files to web root
- Generates unique device identifier
- Configures FullPageOS browser to load remote registration interface

**Usage:**
```bash
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/remote-setup.sh | sudo bash
```

### `reset-remote.sh`
Reset script to restore FullPageOS to clean state after 314Sign remote installation:
- Removes 314Sign-specific files and configurations
- Resets hostname and browser configuration
- Optionally removes web server packages
- Preserves FullPageOS installation intact

**Usage:**
```bash
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/remclient/reset-remote.sh | sudo bash
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

Remote devices are **lightweight web clients** that:
- Use FullPageOS as the display platform
- Get most content from the main kiosk server
- Maintain minimal local storage for offline/cached content
- Receive configuration updates via HTTP
- Display registration codes before connection

## Installation Flow

1. Install FullPageOS on Raspberry Pi (3B+ or newer recommended)
2. Run `remote-setup.sh` on the FullPageOS system
3. Device generates unique ID and displays registration code on screen
4. Admin registers device code in main kiosk web interface
5. Remote receives configuration and begins displaying assigned content
6. Remote polls for updates and maintains offline fallback

## Requirements

- **FullPageOS** (recommended) - provides browser and display management
- Raspberry Pi 3B+ or newer (Pi 5 recommended for best performance)
- Internet connection for initial setup and content updates
- HDMI display connected to Raspberry Pi

## Compatibility

-  **FullPageOS** (primary support)
-   **Raspberry Pi OS Lite** (fallback, requires manual kiosk setup)

The script automatically detects FullPageOS and uses the appropriate configuration method.

## Maintenance

- Remote devices are largely self-maintaining
- Configuration updates happen automatically via HTTP polling
- Content updates pull from main kiosk server
- FullPageOS handles browser and display management
- No manual intervention required after initial setup

## Troubleshooting

If setup fails or you need to start over:
1. Run `reset-remote.sh` to clean up 314Sign configurations
2. Reboot the system
3. Run `remote-setup.sh` again

The reset script preserves FullPageOS while removing only 314Sign additions.