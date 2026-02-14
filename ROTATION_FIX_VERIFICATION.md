# Rotation Fix - Verification Steps

## What Was Fixed
CSS positioning issue preventing rotated content from displaying correctly. The `body::before` pseudo-element and `.qr-badge` were set to `position: fixed`, which doesn't rotate with the body's CSS transform. Changed both to `position: absolute`.

## Quick Verification (2 minutes)

### Step 1: Test Basic Rotation
Open test page: `http://localhost/test-orientation.html`

Click buttons in this order and observe:
- Click `0°` - Page should be normal
- Click `90°` - Page rotates 90° left
- Click `180°` - Page rotates upside down  
- Click `270°` - Page rotates 90° right

**Expected:** Entire page rotates around the center point, including the cyan box and corner indicators.

**If this works:** ✅ Basic rotation is working

**If not:** Check browser console for errors

---

## Full Feature Test (5 minutes)

### Step 2: Set Orientation via Admin UI
1. Open: `http://localhost/314sign/screens/`
2. Find a display (e.g., "HDMI 1")
3. Click the orientation button for that display
   - Try: `180°` (Upside down)
4. Click "Apply Changes" button
5. Wait for "Display configuration updated successfully" toast

**Expected:** Toast appears, changes saved to database

---

### Step 3: Verify Display Updates
1. Get the display's port number from the screens UI
2. In a new tab, open the display page:
   - `http://localhost/?port=0` (for HDMI 1 / port 0)
   - `http://localhost/?port=1` (for HDMI 2 / port 1)
   - OR use the test page: `http://localhost/test-orientation.html?port=0`

3. Watch what happens (should be automatic, within 5 seconds):
   - Press `F12` to open Developer Console
   - Look for log messages

**Expected Console Log:**
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

**Expected Visual:** 
- Page rotates to match the orientation you set
- All content rotates together (header, menu, QR badge)

---

## Advanced Test (10 minutes)

### Step 4: Test Real-Time Updates
While the display page is open (from Step 3):

1. Go back to screens tab
2. Change the same display's orientation again
   - If it was 180°, change to 90°
3. Click "Apply Changes"

**Back on the display page:**
- Watch console for this sequence:
```
[ORIENTATION] Poll - Port 0: DB value=1, last tracked=2, will update: true
[ORIENTATION] Detected change: 2 → 1
[ORIENTATION] Attempting to apply orientation: 1
[ORIENTATION] Applied CSS rotation: 90deg
```

**Visual:** Page should rotate to new orientation within 5 seconds, NO page reload needed

---

### Step 5: Test with "Load from DB" Button
On test page: `http://localhost/test-orientation.html?port=0`

1. Don't click manual rotation buttons
2. Instead, click "Load from DB" button
3. Watch console

**Expected Log:**
```
[ORIENTATION-TEST] Loading orientation from /api/kiosk/displays for port: 0
[ORIENTATION-TEST] API Response: {data: [...]}
[ORIENTATION-TEST] Loaded display config: {hdmi_port: 0, orientation: X, ...}
[ORIENTATION-TEST] Orientation value from DB: X
[ORIENTATION-TEST] Setting rotation to: Xdeg
```

**Visual:** Page rotates to match the database value

---

## Troubleshooting

### Issue: Page doesn't rotate when I click buttons
**Check:**
1. Browser console for errors (F12)
2. Try a different browser or incognito mode
3. Try `test-orientation.html` without port parameter first

**Most likely:** Browser doesn't support CSS transforms (unlikely on modern browsers)

---

### Issue: Rotation is applied but content is cut off
**Check:**
1. Full-screen the browser window (F11)
2. Make viewport larger
3. Check that corners (↖, ↗, ↙, ↘) are still visible

**Note:** This is expected with CSS rotation - rotated content extends beyond original bounds. If corners are visible, it's working.

---

### Issue: Database updates but display doesn't update within 5 seconds
**Check:**

1. Port parameter is in URL:
   ```javascript
   // In console:
   const params = new URLSearchParams(window.location.search);
   console.log(params.get('port'));
   // Should NOT be null
   ```

2. Polling is running:
   - Open Dev Tools → Network tab
   - Filter by "displays"
   - Should see requests every ~5 seconds
   - Check if response includes new orientation value

3. Database was actually updated:
   ```bash
   curl http://localhost/api/kiosk/displays | grep -i orientation
   ```

---

### Issue: Console shows no [ORIENTATION] logs
**Check:**

1. Page actually loaded:
   - Try refreshing browser
   - Should see "Loading menu..." change to actual menu

2. Port parameter was passed:
   - Address bar should have `?port=0` or similar
   - If missing, page won't try to load display-specific config

3. loadConfig() was called:
   ```javascript
   // In console:
   const params = new URLSearchParams(window.location.search);
   if (!params.get('port')) {
     console.log('No port parameter - loadDisplayOrientation() was not called');
   }
   ```

---

## Files Changed

Only these were modified:
1. `/packages/314Sign/index.html` - CSS and rotation function
2. `/packages/314Sign/test-orientation.html` - NEW test page

Database and API are **unchanged** - they were already working correctly.

---

## Expected Behavior Timeline

1. **Admin does:** Sets orientation → clicks "Apply Changes"
2. **Server does:** Updates database
3. **Display does:** Every 5 seconds, polls `/api/kiosk/displays`
4. **Within 5 seconds:** Detects change and applies new rotation
5. **Result:** Content rotates, NO page reload

---

## Success Checklist

- [ ] Test page rotation works (Step 1)
- [ ] Can set orientation in screens UI (Step 2)
- [ ] Display page rotates automatically (Step 3)
- [ ] Console shows [ORIENTATION] logs (Step 3)
- [ ] Real-time updates work (Step 4)
- [ ] "Load from DB" button works (Step 5)

If all boxes checked ✅ → Rotation feature is fully working!

---

## Questions?

Check:
1. Browser console (F12) for error messages
2. [ROTATION_FIX_SUMMARY.md](ROTATION_FIX_SUMMARY.md) for technical details
3. [ROTATION_DEBUGGING_GUIDE.md](ROTATION_DEBUGGING_GUIDE.md) for deep diagnostics

