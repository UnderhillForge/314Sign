# Quick Start: Display Rotation Diagnostics

## What Changed

Added comprehensive diagnostic logging to Electron main process (`src/main/main.ts`):

1. **Automatically checks:**
   - ✅ How many displays Electron detects
   - ✅ Current rotation value each display reports
   - ✅ Whether xrandr command is available on system
   - ✅ Display properties (resolution, scale, bounds, etc.)

2. **When it runs:**
   - Logs appear in **Electron console output** at app startup
   - Look for messages starting with `[ROTATE]` and `[KIOSK]`

## How to Test (3 steps)

### Step 1: Build and restart the app

```bash
cd /home/pi/314Sign-e

# Rebuild Electron with new code
npm run build

# Start the app in development mode (shows console)
npm run dev
```

### Step 2: Look for diagnostic output

**In your terminal, you should see startup messages like:**

```
[ROTATE] ===== DISPLAY INFO (2 total) =====
[ROTATE] Display ID: 1234567890
[ROTATE]   - Bounds: 0,0 (1920x1080)
[ROTATE]   - Resolution: 1920x1080
[ROTATE]   - Rotation: 0° (value: 0)
[ROTATE]   - Scale: 1
[ROTATE]   - Virtual: No
[ROTATE] Display ID: 9876543210
[ROTATE]   - Bounds: 1920,0 (1920x1080)
[ROTATE]   - Resolution: 1920x1080
[ROTATE]   - Rotation: 0° (value: 0)
[ROTATE]   - Scale: 1
[ROTATE]   - Virtual: No
[ROTATE] ===== END DISPLAY INFO =====

[KIOSK] xrandr is available for display rotation
```

**OR (if xrandr not installed):**

```
[KIOSK] xrandr not found - display rotation will not work
[KIOSK] To enable rotation, install: sudo apt-get install x11-xserver-utils
```

### Step 3: Test rotation trigger

1. Keep app running and console visible
2. Open browser to `http://localhost/screens`
3. Click on a display
4. Change orientation from **0°** to **90°**
5. Click **Apply Changes**
6. **Watch console for [ROTATE] messages**

You should see:
```
[ROTATE] Applying rotation to HDMI-1: left (value: 1)
[ROTATE] Successfully rotated HDMI-1 to left
```

## Key Outcomes

| Outcome | Meaning | Next Step |
|---|---|---|
| `[ROTATE] Display ID: ...` appears with 2+ displays | ✅ Displays detected correctly | Proceed to xrandr check |
| `[ROTATE] Rotation: 0°` for all displays | ✅ Baseline correct (no rotation yet) | Ready to test |
| `[KIOSK] xrandr is available` | ✅ xrandr installed | Proceed to rotation test |
| `[KIOSK] xrandr not found` | ❌ xrandr missing | Run: `sudo apt-get install x11-xserver-utils` |
| `[ROTATE] Applying rotation to ...` appears | ✅ Command being executed | Check if display rotates physically |
| No `[ROTATE]` messages appear | ❌ Orientation still 0 or config not applied | Verify orientation changed to non-zero |

## If xrandr Not Installed

```bash
# SSH to Raspberry Pi
ssh pi@your-pi-ip

# Install xrandr
sudo apt-get update
sudo apt-get install x11-xserver-utils

# Restart Electron app
# (Either restart from UI or kill app and `npm run dev` again)
```

## Manual Verification

While Electron app is **running**, SSH into Raspberry Pi and test:

```bash
# List displays
xrandr

# Manually rotate display (test if it works)
xrandr --output HDMI-1 -or left

# Rotate back
xrandr --output HDMI-1 -o normal
```

If manual rotation works but app rotation doesn't → The issue is the xrandr output name doesn't match database.

## Expected Rotation Values

| Config Value | xrandr Command | Physical Result |
|---|---|---|
| **0** | `normal` | Not rotated (0°) |
| **1** | `left` | Rotated 90° clockwise |
| **2** | `inverted` | Rotated 180° (upside down) |
| **3** | `right` | Rotated 270° clockwise |

## Troubleshooting Checklist

Before reporting issues, verify:

- [ ] Run `npm run build` after pulling latest code
- [ ] Electron app started with `npm run dev` (shows console)
- [ ] Look for `[ROTATE]` messages in console
- [ ] Check if xrandr is available: `[KIOSK] xrandr is available`
- [ ] Set orientation to 1 (90°) not 0 - need non-zero to trigger
- [ ] Click "Apply Changes" button after changing orientation
- [ ] Wait 5 seconds for polling cycle to detect change
- [ ] Check console for `[ROTATE] Applying rotation to ...` messages

## Still Not Working?

After verifying above, share:

```bash
# 1. Show xrandr list
xrandr

# 2. Show database config
sqlite3 ~/.config/314sign/database.db "SELECT hdmi_port, xrandr_output, orientation FROM displays;"

# 3. Full Electron console output from app startup
```

This will help match display names and understand the disconnect.

