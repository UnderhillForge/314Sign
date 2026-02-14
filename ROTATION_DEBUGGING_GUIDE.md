# Rotation/Orientation Debugging Guide

## Problem Statement
Rotation does not seem to be working when applied via the `/screens` configuration page.

## Complete Flow Diagram

```
1. Admin Interface (/screens)
   └─> User clicks orientation button (0°, 90°, 180°, 270°)
       └─> JavaScript calls setOrientation(port, value)
           └─> Updates local display object with new orientation
               └─> Marks display as changed in `changes` object
                   └─> User clicks "Apply Changes"
                       └─> API call: PUT /api/displays/{port}
                           └─> Server updates database
                               └─> Database now has new orientation value

2. Display Client (index.html or slideshow)
   └─> Page loads with ?port=X parameter
       └─> loadConfig() is called
           └─> loadDisplayOrientation(port) is called
               └─> Fetch /api/kiosk/displays (public endpoint)
                   └─> Find display with matching hdmi_port
                       └─> lockOrientation(orientation_value)
                           └─> Apply CSS transform: rotate(Xdeg);
                               └─> Content should rotate on screen

3. Real-time Updates
   └─> checkOrientationUpdate() runs every 5 seconds
       └─> Fetch /api/kiosk/displays again
           └─> Compare current value with lastOrientationValue
               └─> If different, call lockOrientation(new_value)
                   └─> CSS rotation applied
```

## Testing Checklist

### Step 1: Verify Database is Updating
```bash
# Open SQL client or check via API
curl http://localhost/api/displays -H "Authorization: Bearer YOUR_TOKEN"

# Look for the display you configured and verify:
# - "hdmi_port": matches the port you set
# - "orientation": shows the value you selected (0, 1, 2, or 3)
```

### Step 2: Verify Public API Returns Correct Value
```bash
# No authentication needed
curl http://localhost/api/kiosk/displays

# Should show:
# {
#   "data": [
#     {
#       "hdmi_port": 0,
#       "orientation": 2,   # <-- Check this matches what you set
#       "mode": "main"
#     }
#   ]
# }
```

### Step 3: Check Display Client is Loading Config
Visit the display URL in the Electron window or browser:
```
http://localhost/?port=0
```

Open browser console (F12) and look for these logs:
```
[ORIENTATION] Loaded display 0 orientation: 2
[ORIENTATION] Applied CSS rotation: 180deg
[ORIENTATION] Body transform: matrix(...)
```

### Step 4: Verify CSS Rotation is Actually Applied
In browser console, run:
```javascript
// Check if transform is applied
window.getComputedStyle(document.body).transform

// Should return something like:
// "matrix(-1, 0, 0, -1, 0, 0)"  for 180°
// or similar matrix notation

// Also check the actual style property:
document.body.style.transform
// Should show: "rotate(180deg)"
```

### Step 5: Visual Inspection
If CSS transform is applied but content doesn't appear rotated:
- Check if body width/height are fixed pixels instead of 100%
- Check if there's overflow: hidden preventing rotated content from displaying
- Check z-index and positioning constraints
- Try opening F12 dev tools and inspecting the body element's computed styles

## Common Issues & Solutions

### Issue: Database updates but display doesn't update within 5 seconds

**Debugging steps:**
1. Check console logs - is checkOrientationUpdate() running?
   ```javascript
   // Add to console:
   console.log('[DEBUG] checkOrientationUpdate called');
   ```

2. Check network tab - is /api/kiosk/displays being called every 5 seconds?
   - Open Dev Tools → Network tab
   - Filter by "displays"
   - Should see requests every ~5 seconds
   - Verify new orientation value appears in response

3. Check if port parameter is being read:
   ```javascript
   // In console:
   const params = new URLSearchParams(window.location.search);
   console.log('Port from URL:', params.get('port'));
   // Should print: "Port from URL: 0" (or your port number)
   ```

### Issue: Orientation is 0° (not rotating) even though value is set

**Possible causes:**
1. `orientation` value in database is NULL or undefined
   ```bash
   # Check database directly for NULL values
   ```

2. Port parameter not in URL
   - Check your browser address bar has `?port=X`
   - If missing, it loads global config instead

3. API endpoint returning old data (caching issue)
   ```bash
   # Force fresh data by adding timestamp
   curl "http://localhost/api/kiosk/displays?$(date +%s)"
   ```

### Issue: Content is rotated but appears cut off or misaligned

**This is the CSS rotation issue!**

The problem: `transform: rotate()` rotates the element but doesn't change the viewport. Content extends beyond original bounds and gets clipped.

**Solutions to try:**
1. Reduce content size
2. Add extra padding/margin to accommodate rotation
3. Check that `overflow: hidden` on body allows for rotated content
4. Verify transform-origin is centered

**Verify current CSS:**
```javascript
// Check body styles
const bodyComputedStyle = window.getComputedStyle(document.body);
console.log('TransformOrigin:', bodyComputedStyle.transformOrigin);
console.log('Overflow:', bodyComputedStyle.overflow);
console.log('Width:', bodyComputedStyle.width);
console.log('Height:', bodyComputedStyle.height);
```

## Key Files to Check

1. **[packages/314Sign/index.html](packages/314Sign/index.html)**
   - Lines 230-304: `lockOrientation()` function
   - Lines 307-323: `unlockOrientation()` function
   - Lines 360-387: `loadConfig()` and `loadDisplayOrientation()`
   - Lines 420-450: `checkOrientationUpdate()` polling
   - Line 658: Polling interval setup

2. **[packages/314Sign/screens/index.html](screens/index.html)**
   - Lines 689-700: `setOrientation()` function
   - Lines 776-800: `applyChanges()` API call
   - Lines 631-640: Orientation button rendering

3. **Database** (Check server-side)
   - Table: `displays`
   - Column: `orientation` (INTEGER, values 0-3)
   - Verify the PUT endpoint updates this column

4. **API Endpoints** (Check server logs)
   - `GET /api/kiosk/displays` - must return current orientation
   - `PUT /api/displays/{port}` - must save orientation to database

## Console Log Reference

When working correctly, you should see this sequence in browser console:

```
[ORIENTATION] Loaded display 0 orientation: 2
[ORIENTATION] Attempting to apply orientation: 2
[ORIENTATION] Applied CSS rotation: 180deg
[ORIENTATION] Body transform: matrix(-1, 0, 0, -1, 0, 0)
```

Then every 5 seconds:
```
[ORIENTATION] Poll - Port 0: DB value=2, last tracked=2, will update: false
```

When orientation changes via /screens:
```
[ORIENTATION] Poll - Port 0: DB value=2, last tracked=1, will update: true
[ORIENTATION] Detected change: 1 → 2
[ORIENTATION] Attempting to apply orientation: 2
[ORIENTATION] Applied CSS rotation: 180deg
```

## Next Steps

1. Run through the testing checklist above
2. Check console logs for error messages
3. Verify database has correct orientation value
4. Verify API endpoint returns correct value
5. If CSS is applied but not visible, focus on CSS styling/overflow issues
6. File issue with specific console output and steps to reproduce

