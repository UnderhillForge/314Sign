# 314Sign Electron Kiosk

Welcome to 314Sign, the dual-screen menu kiosk that runs in the real world and behaves like it. This app powers restaurant menu displays, rotating screens on demand, playing slideshows, and keeping everything crisp at full-screen scale.

It is an Electron-based kiosk app with dual HDMI support, native display orientation control via xrandr, and browser-level orientation handling for display pages.

## Highlights

- ✅ **Dual-screen ready**: Configure HDMI-1 and HDMI-2 independently
- ✅ **Rotation that sticks**: System-level xrandr plus browser-level orientation handling
- ✅ **Menus and slideshows**: Built for daily menus and timed slide decks
- ✅ **Kiosk-first UX**: Fullscreen, minimal chrome, fast startup
- ✅ **TypeScript everywhere**: Safer changes, clearer intent
- ✅ **Secure IPC**: Clean bridge between Electron main and renderer

## What 314Sign Does

- Shows restaurant menus at full screen resolution
- Runs slideshows for promotions, specials, and events
- Supports test patterns and identify screens for setup
- Keeps display orientation consistent across reboots

## Architecture

```
┌─────────────────────────────────────┐
│   Electron Main Process             │
│  (Node.js + Display Control)        │
├─────────────────────────────────────┤
│  - DisplayController (xrandr)       │
│  - IPC Handler Functions            │
│  - Window Management                │
└────────────┬────────────────────────┘
             │ IPC
┌────────────▼────────────────────────┐
│   Electron Renderer (React)         │
│  (Browser - Display UI)             │
├─────────────────────────────────────┤
│  - Menu Display Component           │
│  - Orientation Control UI           │
│  - Screen Orientation API Calls     │
└─────────────────────────────────────┘
```

## Development

### Prerequisites

- Node.js 18+ with npm
- Raspberry Pi with dual HDMI support (Raspberry Pi 5)
- xrandr installed and functional
- Chromium/Electron compatible display

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Starts Vite dev server on http://localhost:3000 with Electron app running in full screen.

### Building

```bash
npm run build
```

Compiles TypeScript and Vite renderer into `dist/` directory.

### Production Start

```bash
npm start
```

Runs the built Electron app in production mode.

### One-Command Install (systemd service)

```bash
bash scripts/install-kiosk.sh
```

This installs dependencies, builds the app, and registers a `314sign-kiosk` systemd service that starts on boot.
By default, the admin UI is at `http://314sign.local/start` (port 80).

Optional flags:

```bash
bash scripts/install-kiosk.sh --port 80 --user pi
```

Uninstall:

```bash
bash scripts/uninstall-kiosk.sh
```

### Packaging

```bash
npm run dist
```

Creates distributable packages (AppImage, deb, etc.) for Linux.

## Configuration

### Display Orientation Values

- `0` = Portrait Primary (0°)
- `1` = Landscape Secondary (90° left)
- `2` = Portrait Secondary (180°)
- `3` = Landscape Primary (270° right)

### IPC API (available in renderer via `window.electronAPI`)

#### Display Control

```typescript
// Set orientation for HDMI port
await window.electronAPI.setOrientation(port: number, orientation: number)

// Get current display configuration
await window.electronAPI.getDisplayConfig()

// Get xrandr status
await window.electronAPI.getXrandrStatus()

// Lock orientation via Screen Orientation API
await window.electronAPI.lockOrientation(orientationType: string)

// Unlock orientation
window.electronAPI.unlockOrientation()
```

#### Menu API

```typescript
// Fetch menu from server
await window.electronAPI.fetchMenu(menuName: string)

// Fetch config from server
await window.electronAPI.fetchConfig()
```

## Connecting to 314Sign Server

The app expects a 314Sign Node.js server running on the same machine (or accessible via network):

- **Menu Endpoint**: `GET /api/menu/{menuName}`
- **Config Endpoint**: `GET /api/config`

Configure the server address in `src/main/main.ts` and `src/preload/preload.ts` if needed.

## xrandr Integration

The DisplayController module handles xrandr commands with proper environment setup:

- Automatically detects X server display (`:0`)
- Dynamically finds XAUTHORITY file from running X process
- Applies rotation commands via `xrandr --output {HDMI-X} --rotate {rotation}`
- Provides error handling and logging

## Screen Orientation API

For browsers with Screen Orientation API support:

- Automatically requests fullscreen before locking orientation
- Maps 314Sign orientation values to standard orientation types
- Falls back to xrandr if API unavailable

## Troubleshooting

### Display blanks after orientation change

- Check xrandr compatibility with your display hardware
- Verify HDMI cable connection and display input settings
- Try different orientation values (0° and 180° are most compatible)
- Check X server logs: `journalctl -u x11`

### XAUTHORITY not found

- Verify X server is running: `ps aux | grep -i X`
- Check display: `echo $DISPLAY` (should be `:0`)
- Try setting manually: `export XAUTHORITY=/path/to/.Xauthority`

### Menu not loading

- Verify 314Sign server is running on port 3000
- Check network connectivity: `curl http://localhost:3000/api/menu/dinner`
- Check browser console for fetch errors

## Project Structure

```
.
├── package.json
├── tsconfig.json
├── tsconfig.main.json
├── vite.config.ts
├── src/
│   ├── main/
│   │   ├── main.ts           # Electron main process
│   │   └── display-controller.ts  # xrandr integration
│   ├── preload/
│   │   └── preload.ts        # IPC API bridge
│   └── renderer/
│       ├── App.tsx           # React app component
│       ├── App.css           # Styling
│       ├── main.tsx          # React entry point
│       ├── index.html        # HTML template
│       └── index.css         # Global styles
└── dist/                      # Build output
```

## License

314Sign © 2026 - All Rights Reserved
