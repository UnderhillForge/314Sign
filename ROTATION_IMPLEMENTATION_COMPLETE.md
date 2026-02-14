# Display Rotation - Complete Implementation Guide

## Overview

The 314Sign kiosk system now supports **true OS-level display rotation** on Linux/Raspberry Pi, with intelligent fallbacks for maximum compatibility.

## Architecture: Multi-Layer Rotation

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: OS-Level Display Rotation (PRIMARY)            │
│ ├─ Method: xrandr commands on Linux/Raspberry Pi        │
│ ├─ Executed by: Electron main process (main.ts)         │
│ ├─ Coverage: Physical monitor rotation (best quality)   │
│ ├─ Performance: Excellent (GPU-handled)                 │
│ └─ When: On app start and whenever config changes       │
├─────────────────────────────────────────────────────────┤
│ Layer 2: CSS Content Rotation (FALLBACK)               │
│ ├─ Method: CSS transform: rotate() on <body>           │
│ ├─ Executed by: Browser renderer (index.html)          │
│ ├─ Coverage: Web content rotation if OS rotation fails  │
│ ├─ Performance: May impact GPU on embedded devices      │
│ └─ When: If OS-level rotation unavailable              │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Screen Orientation API (FALLBACK)             │
│ ├─ Method: screen.orientation.lock() if available      │
│ ├─ Executed by: Browser renderer                       │
│ ├─ Coverage: Modern browsers with fullscreen support    │
│ └─ When: If other methods unavailable                  │
└─────────────────────────────────────────────────────────┘
```

## Layer 1: OS-Level Display Rotation (PRIMARY)

### How It Works

**File:** `src/main/main.ts`
**Function:** `applyDisplayRotation(xrandrOutput, orientation)`

1. Electron main process fetches display config every 5 seconds
2. For each display, checks if `orientation` is set
3. Gets xrandr output name (e.g., "HDMI-1") from config or derives it
4. Executes xrandr command: `xrandr --output HDMI-1 -o right`
5. Logs success/failure to console

### Orientation Values

- **0** = `normal` - No rotation
- **1** = `left` - 90° clockwise (as rotation parameter)
- **2** = `inverted` - 180° (upside down)
- **3** = `right` - 270° clockwise (or 90° counter-clockwise)

### xrandr Command Format

```bash
# Example rotation commands
xrandr --output HDMI-1 -o normal      # 0° (no rotation)
xrandr --output HDMI-1 -o left        # 90° clockwise
xrandr --output HDMI-1 -o inverted    # 180°
xrandr --output HDMI-1 -o right       # 270° clockwise
```

### When OS-Level Rotation Applies

- ✅ Linux/Raspberry Pi systems (process.platform === 'linux')
- ✅ When orientation value is non-zero
- ✅ On app startup
- ✅ When display config changes (within 5-second polling interval)

### Benefits of OS-Level Rotation

| Aspect | Benefit |
|--------|---------|
| **Display** | True physical monitor rotation |
| **Performance** | GPU-optimized, no software rotation overhead |
| **Responsiveness** | Instant, no continuous re-rendering |
| **Compatibility** | Works on any Linux display server |
| **Power Usage** | Minimal - handled at kernel level |
| **Display Quality** | No pixel artifacts or smoothing issues |

### Limitations

- Linux/Raspberry Pi only (not macOS/Windows in this implementation)
- Requires xrandr utility available on system
- Some older displays may not support rotation

---

## Layer 2: CSS Content Rotation (FALLBACK)

### How It Works

**File:** `packages/314Sign/index.html`
**Function:** `lockOrientation(orientationValue)`

1. Browser loads page with `?port=X` parameter
2. Fetches display config from `/api/kiosk/displays`
3. If OS-level rotation isn't available or as secondary measure
4. Applies CSS: `body.style.transform = 'rotate(Xdeg)'`
5. HTML and CSS polling every 5 seconds for changes

### When CSS Rotation Applies

- ✅ Non-Linux systems (macOS, Windows)
- ✅ If OS-level rotation isn't available
- ✅ As supplementary rotation for content
- ✅ Desktop testing and development

### Advantages

- Works on all platforms/browsers
- No system utilities required
- Useful for testing

### Disadvantages

- Only rotates web content, not display
- GPU performance impact on embedded devices
- Ongoing rendering overhead
- May cause slight jank on low-end hardware

---

## Layer 3: Screen Orientation API (FALLBACK)

### How It Works

**File:** `packages/314Sign/index.html`
**Function:** `lockOrientation()` - Screen Orientation API section

1. Requests fullscreen if needed (required by some browsers)
2. Calls `screen.orientation.lock(orientationType)`
3. Orientation types: `portrait-primary`, `landscape-primary`, etc.

### Availability

- Modern browsers with fullscreen support
- Not all browsers/devices support this API
- Fallback for testing

---

## Rotation Values Mapping

### Electron Main Process (xrandr)
```javascript
const rotationMap = {
  0: 'normal',    // 0°
  1: 'left',      // 90° clockwise
  2: 'inverted',  // 180°
  3: 'right',     // 270° clockwise
}
```

### Browser Renderer (CSS)
```javascript
const rotationMap = {
  0: '0deg',      // 0°
  1: '90deg',     // 90°
  2: '180deg',    // 180°
  3: '270deg',    // 270°
}
```

Note: xrandr "left/right" refer to rotation direction, while CSS degrees refer to visual rotation. They map the same way:
- Going from 0 to 1: xrandr "left" = CSS rotate 90°
- Going from 0 to 3: xrandr "right" = CSS rotate 270°

This is counterintuitive but consistent across both systems.

---

## Implementation Details

### Database Schema
```sql
CREATE TABLE displays (
  hdmi_port INTEGER PRIMARY KEY,
  orientation INTEGER DEFAULT 0,      -- 0, 1, 2, or 3
  xrandr_output STRING,               -- e.g., "HDMI-1"
  ...
)
```

### API Endpoint (GET /api/kiosk/displays)
```json
{
  "data": [
    {
      "hdmi_port": 0,
      "orientation": 2,           -- 180°
      "xrandr_output": "HDMI-1",  -- Used for OS-level rotation
      "enabled": 1,
      "mode": "main"
    }
  ]
}
```

### Electron Main Process Flow
```
1. app.on('ready')
   └─> startKiosk()
       └─> fetchDisplayConfig() [/api/kiosk/displays]
           └─> for each display config
               ├─> ensureWindowForDisplay(config)
               └─> if orientation !== 0:
                   └─> applyDisplayRotation(xrandrOutput, orientation)
                       └─> spawnSync('xrandr', [...])
```

### Browser Renderer Flow
```
1. Page loads with ?port=X
   └─> loadConfig() 
       └─> loadDisplayOrientation(port)
           └─> fetch(/api/kiosk/displays)
               └─> lockOrientation(orientation)
                   ├─> Apply CSS rotation
                   └─> Try Screen Orientation API
```

---

## Console Logging

### Electron Main Process
```
[ROTATE] Applying rotation to HDMI-1: left (value: 1)
[ROTATE] Successfully rotated HDMI-1 to left
```

Error:
```
[ROTATE] xrandr failed with status 1: Cannot find display
[ROTATE] Failed to execute xrandr: command not found
```

### Browser Renderer
```
[ORIENTATION] Loaded display 0 orientation: 2
[ORIENTATION] Applied CSS rotation (fallback): 180deg
[ORIENTATION] Note: Primary rotation is handled by OS-level commands (xrandr on Linux/RPi)
[ORIENTATION] Body transform: matrix(-1, 0, 0, -1, 0, 0)
```

---

## Configuration Flow

### User Sets Orientation in /screens UI

```
1. Admin visits http://localhost/314sign/screens/
2. Clicks orientation button for a display (e.g., HDMI-1)
3. Selects: 180° (inverted)
4. Clicks: "Apply Changes"
   └─> API PUT /api/displays/0
       └─> Server updates database: orientation = 2
```

### Electron Detects and Applies

```
5. Electron polling (every 5 seconds): GET /api/kiosk/displays
   └─> Detects: orientation changed from 0 to 2
       └─> Executes: xrandr --output HDMI-1 -o inverted
           └─> System rotates physical display 180°
           └─> Logs: [ROTATE] Successfully rotated HDMI-1 to inverted
```

### Display Renderer Updates (Secondary)

```
6. Browser page /?port=0 runs 5-second polling
   └─> GET /api/kiosk/displays
       └─> Detects: orientation changed
           └─> Applies CSS rotation (already done by OS)
               └─> Logs: [ORIENTATION] Detected change: 0 → 2
```

---

## Testing & Verification

### Test 1: Verify xrandr is Available
```bash
which xrandr
# Output: /usr/bin/xrandr

# List available displays
xrandr
```

### Test 2: Manual xrandr Rotation
```bash
# Rotate HDMI-1 to 90° left
xrandr --output HDMI-1 -o left

# Rotate back to normal
xrandr --output HDMI-1 -o normal
```

### Test 3: Check Electron Logs
```bash
# Monitor electron console for [ROTATE] messages
# When orientation is changed in /screens UI,
# should see immediate [ROTATE] logs
```

### Test 4: Full Feature Test
1. Open `/314sign/screens/`
2. Set HDMI-1 orientation to 90°
3. Click "Apply Changes"
4. Monitor Electron console → should show `[ROTATE] Successfully rotated...`
5. Physical display should rotate instantly

---

## Performance Considerations

### Raspberry Pi Recommendations

1. **Prefer OS-level rotation** over CSS rotation
   - OS-level: GPU-handled, efficient
   - CSS: Continuous rendering, higher CPU/GPU load

2. **Monitor performance** if using both layers
   - If both active and display rotates twice, may see jank
   - Ideal: One layer only

3. **Test frame rates**
   - Check if slideshow/menus remain smooth after rotation
   - If sluggish, reduce animation complexity

### GPU Performance Impact

```
Layer 1 (OS-level):    Minimal ∆
Layer 2 (CSS):         5-15% ∆ (depends on hardware)
Combined:              May compound if both active
```

---

## Troubleshooting

### Rotation Not Applied

**Check 1: Is xrandr available?**
```bash
which xrandr
# If not found: sudo apt-get install x11-xserver-utils
```

**Check 2: What's the xrandr output name?**
```bash
xrandr | grep " connected"
# Example output: HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis)
```

**Check 3: Can you manually rotate?**
```bash
xrandr --output HDMI-1 -o left
# If this works, system support is fine
```

**Check 4: Is orientation value saved in database?**
```sql
SELECT hdmi_port, orientation, xrandr_output FROM displays;
-- Should show orientation = 1, 2, or 3 (not 0)
```

**Check 5: Is Electron executing xrandr?**
- Open Electron console
- Change orientation in /screens
- Look for `[ROTATE]` logs
- If no logs, orientation may be 0

### xrandr Not Found

```bash
# Install on Raspberry Pi
sudo apt-get install x11-xserver-utils

# Or if using Wayland instead of X11
# May need different approach - check system display server
```

### Display Not Responding to Rotation

1. Check if display actually supports rotation
2. Try manual xrandr command to verify
3. Check display parameter in xrandr output
4. Some displays may have rotation locked in firmware

---

## Future Improvements

1. **Wayland Support** - Add fallback for Wayland systems
2. **Multiple Displays** - Better multi-display rotation handling  
3. **Rotation Animation** - Add smooth transition effects
4. **Fallback Detection** - Auto-select best available method
5. **Performance Monitoring** - Track GPU impact in real-time
6. **Display Capabilities** - Query if display supports rotation before attempting

---

## Summary

| Aspect | Layer 1 (OS) | Layer 2 (CSS) | Layer 3 (API) |
|--------|------|--------|-------|
| **Method** | xrandr | CSS transform | screen.orientation |
| **Platform** | Linux only | All platforms | Modern browsers |
| **Quality** | Excellent | Good | Good |
| **Performance** | Minimal | High | Medium |
| **Reliability** | High | High | Medium |
| **Primary Use** | Raspberry Pi | Desktop/fallback | Testing |

**Recommended:** Use Layer 1 (OS xrandr) for production Raspberry Pi systems, Layer 2 (CSS) for development/testing.

