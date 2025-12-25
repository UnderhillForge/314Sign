# 314Sign Troubleshooting Guide

## 501 Error (Not Implemented) on Save

The 501 error means lighttpd doesn't recognize the PUT request. This is usually a WebDAV configuration issue.

### Quick Fix

Run these commands on your Raspberry Pi:

```bash
# 1. Enable WebDAV module
sudo lighty-enable-mod webdav

# 2. Check if WebDAV config exists
sudo cat /etc/lighttpd/conf-enabled/10-webdav.conf

# 3. If missing or incorrect, recreate it:
sudo tee /etc/lighttpd/conf-enabled/10-webdav.conf > /dev/null << 'EOF'
server.modules += ( "mod_webdav" )

# Enable WebDAV for specific editable files
$HTTP["url"] =~ "^/(index\.html|page\.json|rules\.json)$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}

# Enable WebDAV for menu files
$HTTP["url"] =~ "^/menus/(breakfast|lunch|dinner|closed)\.txt$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}

# Enable WebDAV for editor pages
$HTTP["url"] =~ "^/(edit|design|rules)/index\.html$" {
    webdav.activate = "enable"
    webdav.is-readonly = "disable"
}
EOF

# 4. Verify file permissions
sudo chmod 664 /var/www/html/config.json
sudo chmod 664 /var/www/html/rules.json
sudo chmod 664 /var/www/html/index.html
sudo chmod 664 /var/www/html/menus/*.txt
sudo chmod 664 /var/www/html/edit/index.html
sudo chmod 664 /var/www/html/design/index.html
sudo chmod 664 /var/www/html/rules/index.html
sudo chown www-data:www-data /var/www/html/config.json
sudo chown www-data:www-data /var/www/html/rules.json
sudo chown -R www-data:www-data /var/www/html/menus/

# 5. Restart lighttpd
sudo systemctl restart lighttpd

# 6. Check for errors
sudo systemctl status lighttpd
sudo tail -f /var/log/lighttpd/error.log
```

### Verify WebDAV is Working

Test from your phone or computer:

```bash
# Test saving to config.json
curl -X PUT http://raspberrypi.local/config.json \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Should return 200 OK (or 201 Created)
# If you get 501, WebDAV isn't configured correctly
```

### Check Lighttpd Modules

```bash
# List enabled modules
ls -la /etc/lighttpd/conf-enabled/

# Should see:
# - 10-fastcgi.conf
# - 15-fastcgi-php.conf
# - 10-webdav.conf

# If webdav is missing:
sudo lighty-enable-mod webdav
sudo systemctl restart lighttpd
```

### Common Issues

1. **WebDAV module not enabled**
   - Solution: `sudo lighty-enable-mod webdav && sudo systemctl restart lighttpd`

2. **Wrong file permissions**
   - Files must be writable by www-data (644 or 664)
   - Solution: See step 4 above

3. **Regex not matching paths**
   - Check `/var/log/lighttpd/error.log` for clues
   - Verify URL paths match the regex patterns

4. **lighttpd-mod-webdav not installed**
   - Solution: `sudo apt install lighttpd-mod-webdav`

## Other Common Issues

### Edit/Design Pages Don't Load

Check that files exist in subdirectories:
```bash
ls -la /var/www/html/edit/index.html
ls -la /var/www/html/design/index.html
ls -la /var/www/html/rules/index.html
```

### Menu Files Not Found

Verify menus directory:
```bash
ls -la /var/www/html/menus/
```

Should contain:
- breakfast.txt
- lunch.txt
- dinner.txt
- closed.txt

### Schedule Not Working

1. Check rules.json exists and is valid:
   ```bash
   cat /var/www/html/rules.json
   ```

2. Verify rules are enabled (`"enabled": true`)

3. Check browser console for JavaScript errors

### Background Images Not Uploading

Check PHP upload settings:
```bash
# View current limits
php -i | grep upload_max_filesize
php -i | grep post_max_size

# If too small, edit PHP config:
sudo nano /etc/php/7.4/cgi/php.ini
# Change:
# upload_max_filesize = 10M
# post_max_size = 10M

# Then restart:
sudo systemctl restart lighttpd
```

Check upload directory permissions:
```bash
sudo chmod 775 /var/www/html/bg/
sudo chown www-data:www-data /var/www/html/bg/
```

### Kiosk Display Blank

1. Check lighttpd is running:
   ```bash
   sudo systemctl status lighttpd
   ```

2. View error logs:
   ```bash
   sudo tail -n 50 /var/log/lighttpd/error.log
   ```

3. Test from browser on another device:
   ```
   http://raspberrypi.local
   ```

### Getting Help

1. Check lighttpd error log: `/var/log/lighttpd/error.log`
2. Check PHP errors in browser developer console
3. Verify all file permissions: `ls -laR /var/www/html/`
4. Test WebDAV manually with curl (see above)

## Network Connectivity Issues

### Can't Access http://hostname.local URLs

The setup script installs and configures avahi-daemon for .local hostname resolution. If you can't reach `http://yourpi.local`, try these steps:

```bash
# 1. Check if avahi-daemon is installed and running
sudo systemctl status avahi-daemon

# If not running:
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# 2. Check if avahi-daemon is listening on port 5353
sudo netstat -uln | grep 5353

# 3. Test mDNS resolution
ping yourpi.local

# 4. Check hostname
hostname
hostname -f

# 5. Restart avahi if needed
sudo systemctl restart avahi-daemon
```

### Alternative: Use IP Address

If .local resolution isn't working, use the Pi's IP address instead:

```bash
# Find the Pi's IP address
hostname -I

# Or check network interfaces
ip addr show

# Then access via IP:
# http://192.168.1.100/ (replace with actual IP)
```

### Firewall Issues

If you have ufw or another firewall enabled:

```bash
# Check firewall status
sudo ufw status

# Allow mDNS traffic (port 5353 UDP)
sudo ufw allow 5353/udp

# Allow HTTP (port 80)
sudo ufw allow 80/tcp
```

### Network Troubleshooting Commands

```bash
# Test basic connectivity
ping 8.8.8.8

# Check local network
ping 192.168.1.1  # Replace with your router IP

# Check DNS resolution
nslookup google.com

# Check avahi browsing
avahi-browse -a
```

## Kiosk Display Not Showing

### Pi Boots to Console Instead of Kiosk

If the Pi boots to command line instead of fullscreen kiosk display:

#### Option 1: Set Up Kiosk Mode (If Not Done During Installation)
```bash
# Run the kiosk setup script
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash

# Follow prompts for screen rotation
sudo reboot
```

#### Option 2: Check If Kiosk Mode is Configured
```bash
# Check if kiosk files exist
ls -la ~/.config/openbox/autostart
ls -la ~/.xinitrc
ls -la ~/.bash_profile

# Check boot behavior
sudo raspi-config nonint get_boot_cli  # Should return 1 (auto-login)

# Check installed packages
dpkg -l | grep -E "(chromium|xserver-xorg|openbox)"
```

#### Option 3: Manual Kiosk Start
If kiosk mode is configured but not auto-starting:
```bash
# Start X11 manually
startx -- -nocursor

# Or check the auto-start configuration
cat ~/.bash_profile
```

### Browser Not Launching in Kiosk Mode

If X11 starts but browser doesn't show:

```bash
# Check browser installation
which chromium || which chromium-browser || which firefox-esr

# Test browser manually
chromium --kiosk http://localhost/index.html

# Check kiosk startup script
cat ~/.config/openbox/autostart
```

### Screen Rotation Issues

If display is rotated incorrectly:

```bash
# Re-run kiosk setup to change rotation
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/scripts/os-lite-kiosk.sh | sudo bash

# Or manually adjust
xrandr --output HDMI-1 --rotate normal  # or right, left, inverted
```

## Undervoltage Warnings

### Raspberry Pi Shows Lightning Bolt Icon

The lightning bolt icon indicates undervoltage detection. This can happen even with adequate power supplies.

### Option 1: Check Power Supply (Recommended First)
```bash
# Test with high-power tasks
stress -c 4 -t 60  # Install stress with: sudo apt install stress

# Monitor voltage during stress test
vcgencmd get_throttled
watch -n 1 vcgencmd measure_volts core
```

### Option 2: Disable Warnings (If Power Supply is Adequate)
If you're confident your power supply is good quality:

```bash
# Check current config
grep -i avoid_warnings /boot/config.txt || echo "Not configured"

# Add to /boot/config.txt
echo "" | sudo tee -a /boot/config.txt
echo "# Disable undervoltage warnings" | sudo tee -a /boot/config.txt
echo "avoid_warnings=1" | sudo tee -a /boot/config.txt

# Reboot to apply
sudo reboot
```

### Option 3: Re-enable Warnings (For Troubleshooting)
```bash
# Remove the line from /boot/config.txt
sudo sed -i '/avoid_warnings=1/d' /boot/config.txt
sudo sed -i '/Disable undervoltage warnings/d' /boot/config.txt

# Reboot to apply
sudo reboot
```

**Note**: The 314Sign installer offers to disable these warnings during setup if you choose "y" when prompted.

## Advanced Security (Optional)

### Separate WebDAV User

For enhanced security (typically only needed if exposing to internet - NOT recommended):

```bash
# Run the optional security enhancement script
./create-webdav-user.sh
```

**When to use:**
- You're exposing the kiosk to the internet (not recommended for other reasons)
- You need additional security isolation
- You want separate audit trails for web serving vs. file edits

**When to skip (most cases):**
- Local network only ✓ **Recommended for typical installations**
- Small trusted staff group
- Simplicity is preferred

The default `www-data` user is perfectly fine for local network deployments.

