# 314Sign Framebuffer Display

A Python-based framebuffer display program for Raspberry Pi Zero 2W that renders 314Sign content directly to the display without requiring a web browser.

## Overview

The framebuffer display program provides an alternative to browser-based display by rendering LMS (Lightweight Markup Script) content and slideshows directly to the Raspberry Pi's framebuffer using pygame. This approach offers:

- **Lower resource usage** - No web browser overhead
- **Direct hardware access** - Faster rendering with `/dev/fb0`
- **Pi Zero 2W optimized** - Hardware-specific optimizations for limited resources
- **Network-aware** - Automatic content updates from main kiosk
- **Offline capable** - Cached content for network outages

## Architecture

```
┌─────────────────┐    HTTP Polling    ┌─────────────────┐
│   Main Kiosk    │◄──────────────────►│   Pi Zero 2W    │
│                 │                    │ Framebuffer     │
│ • LMS Content   │                    │ Display         │
│ • Slideshows    │                    │                 │
│ • Remote Mgmt   │                    │ • LMS Renderer  │
│ • API Server    │                    │ • Slideshow     │
└─────────────────┘                    │ • Network Poll  │
                                        │ • Content Cache │
                                        └─────────────────┘
                                               │
                                               ▼
                                        ┌─────────────────┐
                                        │   HDMI Display  │
                                        │   /dev/fb0      │
                                        └─────────────────┘
```

## Features

### Content Types
- **LMS Content**: Menus, announcements with text, shapes, dynamic content
- **Slideshows**: Image/video slides with transitions and timing
- **Standby Mode**: Fallback display when no content available
- **Mirror Mode**: Display main kiosk content (planned)

### Hardware Optimizations
- **Pi Zero 2W Detection**: Automatic hardware-specific settings
- **Memory Management**: Reduced cache sizes for 512MB RAM
- **CPU Optimization**: Adjusted polling intervals for single-core CPU
- **Direct Framebuffer**: SDL_FBDEV for fastest rendering

### Network Features
- **HTTP Polling**: Config and content updates from main kiosk
- **Content Caching**: Local storage for offline operation
- **Auto-registration**: Device registration with unique IDs
- **Heartbeat Monitoring**: Connectivity status reporting

## Installation

### Automated Setup (Recommended)

Run the automated setup script on a fresh Raspberry Pi Zero 2W:

```bash
# Download and run setup script
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/hybrid/setup_framebuffer.sh | sudo bash
```

The script will:
- Install Python dependencies and SDL libraries
- Configure system for direct framebuffer access
- Create systemd service for auto-start
- Setup device identification and logging
- Reboot system to apply changes

### Manual Installation

If you prefer manual setup:

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# Install Python packages
sudo pip3 install pygame requests

# Copy program files
sudo mkdir -p /opt/314sign
sudo cp -r hybrid/render /opt/314sign/
sudo cp -r hybrid/lms /opt/314sign/
sudo cp hybrid/framebuffer_display.py /opt/314sign/

# Create configuration
sudo mkdir -p /etc/314sign
# Edit /etc/314sign/config.json with your settings
```

## Configuration

The display is configured via `/etc/314sign/config.json`:

```json
{
  "device_code": "PIZERO001",
  "main_kiosk_url": "http://192.168.1.100:80",
  "display_size": [1920, 1080],
  "orientation": "landscape",
  "cache_dir": "/var/cache/314sign",
  "config_poll_interval": 60,
  "content_poll_interval": 300,
  "debug": false,
  "offline_mode": false
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `device_code` | Unique device identifier | Auto-generated |
| `main_kiosk_url` | Main kiosk server URL | `http://localhost:80` |
| `display_size` | Display resolution [width, height] | `[1920, 1080]` |
| `orientation` | Display orientation | `landscape` |
| `cache_dir` | Content cache directory | `/var/cache/314sign` |
| `config_poll_interval` | Config poll interval (seconds) | `60` |
| `content_poll_interval` | Content poll interval (seconds) | `300` |
| `debug` | Enable debug logging | `false` |
| `offline_mode` | Disable network polling | `false` |

## Usage

### Starting the Display

The display runs as a systemd service:

```bash
# Start service
sudo systemctl start 314sign-display.service

# Stop service
sudo systemctl stop 314sign-display.service

# Restart service
sudo systemctl restart 314sign-display.service

# Check status
sudo systemctl status 314sign-display.service

# View logs
sudo journalctl -u 314sign-display.service -f
```

### Helper Scripts

The setup script installs helper commands:

```bash
# Quick status check
314sign-status

# Control the service
314sign-control start
314sign-control stop
314sign-control restart
314sign-control logs
314sign-control configure  # Edit config file
```

### Command Line Options

Run manually for testing:

```bash
# Basic startup
python3 framebuffer_display.py

# With custom config
python3 framebuffer_display.py --config /path/to/config.json

# Override settings
python3 framebuffer_display.py --device-code MYDEVICE --main-kiosk-url http://192.168.1.100:80

# Offline mode
python3 framebuffer_display.py --offline

# Debug mode
python3 framebuffer_display.py --debug
```

## Remote Management

### Device Registration

1. **Generate Device ID**: Setup script creates unique device ID based on CPU serial
2. **Register Device**: Use main kiosk web interface (`/remotes`) to register the device code
3. **Configure Content**: Assign LMS content or slideshows to the device
4. **Monitor Status**: View device status and logs in remote management interface

### Content Assignment

Devices can be configured to display:

- **LMS Mode**: Specific LMS content (e.g., `restaurant-menu`)
- **Slideshow Mode**: Specific slideshow sets (e.g., `daily-specials`)
- **Standby Mode**: Default when no content assigned

### Network Requirements

- **Initial Setup**: Internet connection for registration
- **Operation**: Can work offline with cached content
- **Updates**: HTTP polling for content and configuration changes

## Content Formats

### LMS Content

LMS files define display content with overlays:

```json
{
  "version": "1.0",
  "background": {
    "image": "restaurant-bg.jpg",
    "brightness": 0.9
  },
  "overlays": [
    {
      "type": "text",
      "content": "Daily Specials",
      "font": "BebasNeue",
      "size": 48,
      "position": {"x": 100, "y": 50}
    }
  ]
}
```

### Slideshow Content

Slideshows are JSON arrays of slides:

```json
{
  "name": "Daily Specials",
  "slides": [
    {
      "type": "image",
      "media": "pasta.jpg",
      "duration": 5000,
      "caption": "Pasta Special - $12.95"
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### Display Not Starting
```bash
# Check service status
sudo systemctl status 314sign-display.service

# View detailed logs
sudo journalctl -u 314sign-display.service -n 50

# Check configuration
cat /etc/314sign/config.json
```

#### Black Screen / No Display
- Verify HDMI connection and resolution settings
- Check `/boot/config.txt` for correct HDMI configuration
- Test with fallback display mode: `export SDL_VIDEODRIVER=x11`

#### Network Issues
```bash
# Test connectivity to main kiosk
curl http://YOUR-KIOSK-IP/api/remotes/config/YOUR-DEVICE-CODE

# Check device registration
curl http://YOUR-KIOSK-IP/api/remotes
```

#### Content Not Loading
- Verify LMS/slideshow files exist on main kiosk
- Check device is registered and assigned content
- Review logs for download errors

### Log Files

- **Systemd Logs**: `sudo journalctl -u 314sign-display.service`
- **Application Logs**: Included in systemd output
- **Cache Location**: `/var/cache/314sign/`

### Performance Tuning

For Pi Zero 2W optimization:

```json
{
  "config_poll_interval": 120,
  "content_poll_interval": 600,
  "max_cache_size": 52428800
}
```

## Development

### Testing on Development Machine

```bash
# Install dependencies
pip install pygame requests

# Run in offline mode with test content
python3 framebuffer_display.py --offline --debug

# Test with X11 fallback (for desktop testing)
export SDL_VIDEODRIVER=x11
python3 framebuffer_display.py
```

### Adding New Content Types

1. Extend `_render_current_content()` method
2. Add content-specific rendering methods
3. Update content polling and caching logic
4. Add configuration options if needed

### Hardware-Specific Optimizations

The program auto-detects Pi Zero 2W and applies optimizations:

- Reduced polling intervals for single-core CPU
- Smaller cache sizes for limited RAM
- Optimized rendering settings

## API Endpoints

The framebuffer display communicates with the main kiosk via HTTP APIs:

- `GET /api/remotes/config/{device_code}` - Get device configuration
- `GET /api/lms/{name}` - Get LMS content
- `GET /api/slideshows/{name}` - Get slideshow content
- `GET /api/slideshows/{name}/sets/{set}` - Get slideshow set

## License

314Sign Framebuffer Display is part of the 314Sign project and follows the same CC BY-NC 4.0 license.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review logs with `314sign-status` or `sudo journalctl -u 314sign-display.service`
3. Verify device registration in main kiosk interface
4. Test connectivity between devices

The framebuffer display is designed to be maintenance-free after initial setup, automatically handling content updates and providing fallback displays when needed.