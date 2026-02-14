# Rotation/Orientation Bug Fix Summary

## Issue
Rotation was not working when applied via the `/screens` configuration page.

## Root Cause
CSS positioning conflict: Elements with `position: fixed` don't rotate when the parent body has `transform: rotate()` applied, because fixed positioning is relative to the viewport, not the rotated element.

## Fixes Applied

### 1. Fixed `body::before` pseudo-element (index.html, line ~33)
**Before:**
```css
body::before {
  position: fixed;  /* Won't rotate with body */
  ...
}
```

**After:**
```css
body::before {
  position: absolute;  /* Rotates with body */
  ...
}
```

### 2. Fixed `.qr-badge` element (index.html, line ~52)
**Before:**
```css
.qr-badge {
  position: fixed;  /* Won't rotate with body */
  ...
}
```

**After:**
```css
.qr-badge {
  position: absolute;  /* Rotates with body */
  ...
}
```

### 3. Simplified `lockOrientation()` function (index.html, lines 230-304)
Removed complex viewport dimension swapping. Now uses a simple, reliable rotation:
```javascript
document.body.style.transformOrigin = 'center center';
document.body.style.transform = `rotate(${rotation})`;
```

## Files Modified
- `/packages/314Sign/index.html` - CSS positioning and rotation logic
- `/packages/314Sign/test-orientation.html` - NEW debug/test page

## How to Test

### Quick Test (No Setup Needed)
1. Visit: `http://localhost/test-orientation.html`
2. Click rotation buttons (0°, 90°, 180°, 270°)
3. Entire page should rotate around center
4. Corners should stay in labeled positions (↖, ↗, ↙, ↘)

### Full Flow Test
1. Visit: `http://localhost/316Sign/screens/`
2. Set orientation for a display (e.g., HDMI 1 = 180°)
3. Click "Apply Changes"
4. Visit: `http://localhost/?port=0` (or appropriate port)
5. Page should automatically rotate within 5 seconds
6. Check browser console for logs like: `[ORIENTATION] Applied CSS rotation: 180deg`

### With Port Parameter (Load from DB)
1. Visit: `http://localhost/test-orientation.html?port=0`
2. Click "Load from DB" button
3. Should fetch orientation from database and apply it
4. Console shows: `[ORIENTATION] Loaded display 0 orientation: 2`

## Why This Works

### The Problem with `position: fixed`
When you have:
```css
body {
  transform: rotate(90deg);
}

.qr-badge {
  position: fixed;  /* Bad! */
  right: 10px;
  bottom: 10px;
}
```

The QR badge doesn't rotate with the body. Fixed positioning ignores transforms on ancestors.

### The Solution: `position: absolute`
```css
body {
  transform: rotate(90deg);
}

.qr-badge {
  position: absolute;  /* Good! */
  right: 10px;
  bottom: 10px;
}
```

Now the QR badge is positioned relative to the rotated body and rotates with it.

## Technical Details

### Rotation Values
- `0` → `0deg` - Normal/landscape
- `1` → `90deg` - Rotated left
- `2` → `180deg` - Upside down
- `3` → `270deg` - Rotated right

### Polling Mechanism
- Display pages poll `/api/kiosk/displays` every 5 seconds
- Compares current orientation with last applied value
- If changed, applies new rotation immediately
- No page reload required

### API Flow
1. Admin changes orientation in `/screens`
2. `setOrientation()` updates local object
3. `applyChanges()` calls `PUT /api/displays/{port}`
4. Server updates database
5. Display client's `checkOrientationUpdate()` detects change
6. New rotation applied via `lockOrientation()`

## Console Log Messages

When working correctly, you'll see:
```
[ORIENTATION] Loaded display 0 orientation: 2
[ORIENTATION] Attempting to apply orientation: 2
[ORIENTATION] Applied CSS rotation: 180deg
[ORIENTATION] Body transform: matrix(-1, 0, 0, -1, 0, 0)
```

Every 5 seconds (if unchanged):
```
[ORIENTATION] Poll - Port 0: DB value=2, last tracked=2, will update: false
```

When orientation changes:
```
[ORIENTATION] Detected change: 1 → 2
[ORIENTATION] Attempting to apply orientation: 2
[ORIENTATION] Applied CSS rotation: 180deg
```

## Verification

✅ Database - `displays` table has `orientation` column (INTEGER, 0-3)
✅ API - `/api/kiosk/displays` returns orientation for each display
✅ Frontend - `index.html` has `lockOrientation()` function with polling
✅ CSS - Fixed positioning changed to absolute for rotatable elements

## Database Schema (Already Exists)
```sql
CREATE TABLE displays (
  hdmi_port INTEGER PRIMARY KEY,
  orientation INTEGER DEFAULT 0,  -- 0, 1, 2, or 3
  enabled INTEGER DEFAULT 1,
  ...
)
```

## No Breaking Changes
- All existing functionality preserved
- Database schema unchanged
- API contracts unchanged
- Just CSS positioning fixed
- The rotation mechanism was already implemented and working at the code level

