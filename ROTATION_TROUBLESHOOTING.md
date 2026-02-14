# Display Rotation - Diagnostic Guide

## Current Issue
Displays are not rotating even though orientation is set. Identification is working correctly, which means:
- ✅ Display detection is working
- ✅ Display windows are being created 
- ✅ Config is being read
- ❌ Rotation is not being applied

## Step 1: Check Electron Logs

**Look for these messages at startup:**

```
[ROTATE] ===== DISPLAY INFO (2 total) =====
[ROTATE] Display ID: 12345
[ROTATE]   - Bounds: 0,0 (1920x1080)
[ROTATE]   - Resolution: 1920x1080
[ROTATE]   - Rotation: 0° (value: 0)
[ROTATE]   - Scale: 1
[ROTATE]   - Virtual: No
[ROTATE] ===== END DISPLAY INFO =====
```

**Check for xrandr availability:**

```
[KIOSK] xrandr is available for display rotation
```

OR (if missing):

```
[KIOSK] xrandr not found - display rotation will not work
[KIOSK] To enable rotation, install: sudo apt-get install x11-xserver-utils
```

## Step 2: Install xrandr (if needed)

```bash
# SSH into Raspberry Pi and run:
sudo apt-get update
sudo apt-get install x11-xserver-utils

# Verify installation:
which xrandr
# Should output: /usr/bin/xrandr
```

## Step 3: Test xrandr Manually

```bash
# List connected displays
xrandr

# Example output:
# HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis)
# HDMI-2 connected 1920x1080+1920+0 (normal left inverted right x axis y axis)

# Try rotating HDMI-1 to 90° (left)
xrandr --output HDMI-1 -o left

# Rotate back to normal
xrandr --output HDMI-1 -o normal

# Rotate to 180° (inverted)
xrandr --output HDMI-1 -o inverted
```

## Step 4: Verify Display Names Match Database

After successful manual xrandr rotation:

1. Run on Raspberry Pi:
```bash
xrandr | grep " connected"
```

2. Get output names (e.g., `HDMI-1`, `HDMI-2`, `HDMI1`, `HDMI2`)

3. Check database:
```bash
# SSH to Raspberry Pi, then:
sqlite3 ~/.config/314sign/database.db
SELECT hdmi_port, xrandr_output, orientation FROM displays;
```

4. Update database if needed:
```sql
UPDATE displays SET xrandr_output = 'HDMI-1' WHERE hdmi_port = 0;
UPDATE displays SET xrandr_output = 'HDMI-2' WHERE hdmi_port = 1;
```

## Step 5: Check Current Config Values

In `/screens` UI, verify:

1. **Display Port Numbers** - Should see HDMI-1, HDMI-2 or similar
2. **Current Orientation** - All should be at 0° (baseline)
3. **xrandr_output** - Should be populated (or will default to HDMI-1, HDMI-2)

## Step 6: Monitor Logs During Config Change

1. Open Electron console (usually shows in terminal/logs)
2. In `/screens` UI: Change HDMI display orientation from 0° to 90°
3. Click "Apply Changes"
4. Watch console for:

```
[ROTATE] Applying rotation to HDMI-1: left (value: 1)
[ROTATE] Successfully rotated HDMI-1 to left
```

**If you see these:** ✅ Rotation is working!
**If not:** ❌ Something is blocking the xrandr command

## Step 7: Understand the Rotation Values

| Config Value | xrandr Value | Display Rotation |
|---|---|---|
| **0** | normal | 0° (normal) |
| **1** | left | 90° clockwise |
| **2** | inverted | 180° (upside down) |
| **3** | right | 270° clockwise |

## Troubleshooting Errors

### "xrandr not found"

```
[KIOSK] xrandr not found - display rotation will not work
```

**Solution:**
```bash
sudo apt-get install x11-xserver-utils
# Then restart Electron app
```

### "xrandr: can't find display 'HDMI-1'"

This means the display name in database doesn't match actual hardware.

**Fix:**
```bash
# Check actual names:
xrandr | grep " connected"

# Update database with correct names
sqlite3 ~/.config/314sign/database.db
UPDATE displays SET xrandr_output = 'HDMI-2' WHERE hdmi_port = 0;
```

### "xrandr failed with status 1"

Could mean:
- Wrong display name
- Display doesn't support rotation
- X11 server issue

**Debug:**
```bash
xrandr --output HDMI-1 -o left
# If it fails, the same command from Electron will also fail
```

### No [ROTATE] logs appear at all

Could mean:
- Orientation is still 0 (no logs for 0)
- Config change not detected
- Electron not restarting

**Check:**
1. Verify orientation is NOT 0 in `/screens` UI
2. Check that "Apply Changes" was clicked
3. Restart entire Electron app

## Browser-Side Debugging

The CSS rotation might also be active. Check in browser console (`F12`):

```javascript
// Check current body rotation
window.getComputedStyle(document.body).transform

// Should show something like:
// "matrix(0, 1, -1, 0, 0, 0)" for 90°
// "matrix(-1, 0, 0, -1, 0, 0)" for 180°
// etc.
```

## Display API Debugging

Check what Electron's Display API sees:

In Electron main process console (advanced):
```javascript
const { screen } = require('electron');
const displays = screen.getAllDisplays();
displays.forEach(d => {
  console.log(`ID: ${d.id}, Rotation: ${d.rotation}, Bounds: ${JSON.stringify(d.bounds)}`);
});
```

## Quick Diagnostic Checklist

- [ ] xrandr is installed: `which xrandr`
- [ ] Display names match: `xrandr | grep connected` vs database
- [ ] Orientation value is not 0 in `/screens`
- [ ] "Apply Changes" button clicked
- [ ] Electron console shows `[ROTATE]` messages
- [ ] Manual xrandr command works: `xrandr --output HDMI-1 -o left`
- [ ] Orientation logged correctly in browser console

## If Everything Checks Out

If all diagnostics pass but displays still aren't rotating:

1. Check if there's a display server issue:
```bash
echo $DISPLAY
# Should show something like :0 or :1
```

2. Try rotating manually while app is running:
```bash
xrandr --output HDMI-1 -o left
```

3. Check if Wayland vs X11:
```bash
echo $XDG_SESSION_TYPE
# Should be 'x11' (not 'wayland')
```

## Next: Try CSS Rotation

If OS-level rotation isn't working, verify CSS rotation fallback:

1. Open `/test-orientation.html?port=0` 
2. Click "90°" button
3. Does page rotate visually?
4. If yes: CSS is working (but display isn't physically rotating)

This tells us if the issue is OS-level or browser-level.

