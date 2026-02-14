# Orientation & Rotation Feature Implementation

## Overview
Complete implementation of per-display orientation support with CSS-based visual rotation for the 314Sign Kiosk system.

## Changes Made

### 1. Electron Main Process ([src/main/main.ts](src/main/main.ts))
**Function: `buildDisplayUrl()`** (Lines 113-135)

**What changed:**
- Now passes `?port=X` parameter to all display URLs
- Enables renderer to identify which HDMI port it's running on
- Applies to all display modes: main, slideshow, identify, test-pattern

**URLs Generated:**
```
Main display:      http://localhost/?port=0
Slideshow:         http://localhost/?slideshow=lunch&port=1
Identify mode:     http://localhost/identify.html?display=1
Test pattern:      http://localhost/test-pattern.html?display=2
```

### 2. Display Renderer ([packages/314Sign/index.html](packages/314Sign/index.html))

#### Enhanced `lockOrientation()` Function (Lines 230-295)
**Primary Method: CSS Rotation** (Always works)
```javascript
document.body.style.transform = `rotate(${rotation}deg)`;
```

**Orientation Mapping:**
- Value 0 → 0° (portrait-primary)
- Value 1 → 90° (landscape-secondary / portrait on RPi)
- Value 2 → 180° (portrait-secondary)
- Value 3 → 270° (landscape-primary)

**Fallback Method:** Screen Orientation API
- Requests fullscreen first
- Calls `screen.orientation.lock()` if available
- Gracefully handles API unavailability

#### New `loadDisplayOrientation()` Function (Lines 352-378)
**Behavior:**
- Reads port parameter from URL: `?port=0`
- Fetches public `/api/kiosk/displays` endpoint (no auth required)
- Finds matching display by `hdmi_port`
- Applies orientation via `lockOrientation()`
- Falls back to 90° (landscape-secondary) if no data

**Why public endpoint:**
- Guest-facing displays can't use admin-only `/api/displays/:port`
- `/api/kiosk/displays` returns all displays with full config
- No authentication needed for Electron renderer

#### New `checkOrientationUpdate()` Function (Lines 380-410)
**Behavior:**
- Polls every 5 seconds for orientation changes
- Only updates CSS if value actually changed (prevents jank)
- Silently fails on network errors
- Uses same public API endpoint

#### Updated `unlockOrientation()` Function (Lines 297-310)
**Behavior:**
- Clears CSS transforms when unlocking
- Resets viewport width/height
- Attempts to unlock Screen Orientation API if available

#### Polling Setup (Line 605)
```javascript
setInterval(checkOrientationUpdate, 5000); // Every 5 seconds
```

### 3. Database Design ([packages/314Sign/src/database.ts](packages/314Sign/src/database.ts))
**Displays Table Schema:**
```sql
orientation INTEGER DEFAULT 0,  -- 0 (normal), 1 (90°), 2 (180°), 3 (270°)
```

**Default Values:**
- Port 0 (HDMI-1): orientation = 1 (90° portrait)
- Port 1 (HDMI-2): orientation = 0 (landscape)

## Feature Capabilities

### Per-Display Configuration
Each HDMI port can have independent orientation settings:
```json
{
  "hdmi_port": 0,
  "orientation": 1,  // 90° left
  "mode": "main"
}
{
  "hdmi_port": 1,
  "orientation": 0,  // Normal/landscape
  "mode": "main"
}
```

### Real-Time Updates
1. Admin changes orientation in `/screens` UI
2. System updates database via API
3. Electron polls `/api/kiosk/displays` every 5 seconds
4. Renderer's `checkOrientationUpdate()` detects change within 5 seconds
5. CSS rotation applied immediately

### Fallback Chain
1. ✅ CSS `transform: rotate()` - Always works on all browsers/devices
2. ✅ Screen Orientation API - Works on modern browsers with fullscreen
3. ✅ Default fallback - Uses 90° if both methods fail

## Resolution Handling (Plug & Play Support)

### Current System
- `getAvailableResolutions()` auto-detects hardware capabilities at runtime
- No hardcoded display modes - xrandr queries actual device
- Position_x/position_y fixed in database based on physical layout

### What Happens When You Plug In New Display
1. Physical connection to HDMI port
2. Electron polls `/api/kiosk/displays` (every 5 seconds)
3. Triggers `applyXrandrConfig()` 
4. Auto-detection finds new display's capabilities
5. xrandr applies appropriate resolution automatically

### Supported Scenarios
- ✅ Swap displays between HDMI ports (auto-detected)
- ✅ Replace display with different resolution model (auto-detected)
- ✅ Configure different orientations per port
- ✅ Raspberry Pi limitation: Max 2 HDMI ports (inherent hardware)

## Testing

### Verify Orientation Implementation
```bash
# Check display config with orientation values
curl -s http://localhost/api/kiosk/displays | jq '.data | map({port: .hdmi_port, orientation, mode})'

# Update orientation via admin API
curl -X PUT http://localhost/api/displays/0 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"orientation": 2}'

# Mark complete change detection within 5 seconds
# Observe CSS rotation applied to display content
```

### Browser Console Logs
When port parameter is passed, console shows:
```
[ORIENTATION] Applied CSS rotation: 90deg
[ORIENTATION] Loaded display 0 orientation: 1
[ORIENTATION] Display 0 orientation changed to: 2
```

## API Endpoints

### Public (No Auth)
- `GET /api/kiosk/displays` - Returns all displays with full config including orientation
  - Used by: Electron main, display renderers

### Admin-Only
- `GET /api/displays` - Full display list with xrandr_outputs
- `GET /api/displays/:port` - Single display details
- `PUT /api/displays/:port` - Update display config (resolution, orientation, mode, position)
- `POST /api/displays/identify` - Show display numbers on all enabled displays for 5 seconds

## Files Modified

1. **[src/main/main.ts](src/main/main.ts)** (Lines 113-135)
   - Updated `buildDisplayUrl()` to pass port parameter

2. **[packages/314Sign/index.html](packages/314Sign/index.html)**
   - Lines 230-295: Enhanced `lockOrientation()` with CSS rotation
   - Lines 297-310: Updated `unlockOrientation()` to clear CSS
   - Lines 327-351: Updated `loadConfig()` to use port-specific loading
   - Lines 352-378: New `loadDisplayOrientation()` function
   - Lines 380-410: New `checkOrientationUpdate()` polling function
   - Line 605: Added 5-second polling interval

## Future Enhancements

1. **Orientation Animation**
   - Add CSS transition for smooth rotation (if desired)
   - Example: `transition: transform 0.3s ease-in-out;`

2. **Per-Orientation Layout Adjustment**
   - Adjust font sizes, padding based on rotation value
   - Example: Double padding when rotated 90° to account for narrower column

3. **Orientation Persistence**
   - Save lastOrientationValue to sessionStorage to survive page reloads
   - Prevents flashing white screen during orientation change

4. **Hardware Detection**
   - Detect actual display resolution at startup
   - Auto-populate database with hardware capabilities
   - Migrate legacy config values if hardware changed

## Notes

- CSS rotation is the primary method for maximum compatibility
- Screen Orientation API is a fallback for systems that support it
- The public `/api/kiosk/displays` endpoint enables guest displays to read config
- Polling every 5 seconds allows dynamic updates without page reload
- Resolution auto-detection means system is ready for any HDMI display
