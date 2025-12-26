# Troubleshooting Guide

Common issues and solutions for 314Sign.

## Installation Issues

### "Permission denied" during setup
```bash
# Run setup with sudo
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash
```

### Raspberry Pi OS Lite kiosk setup fails
- Ensure you're using Raspberry Pi OS Lite (64-bit)
- Check that the Pi has internet access
- Try running the kiosk setup manually:
```bash
sudo ./scripts/os-lite-kiosk.sh
```

## Network Issues

### Can't access kiosk from other devices
- Ensure the Pi and your device are on the same network
- Check firewall settings: `sudo ufw status`
- Verify hostname resolution: `ping raspberrypi.local`

### Kiosk shows "Connection lost"
- Check PM2 status: `pm2 list`
- Restart server: `pm2 restart 314sign`
- Check logs: `pm2 logs 314sign`

## Display Issues

### Text appears too small/large
- Adjust font size in the design page
- Check screen resolution settings
- Use size override tags: `[s16]Text[/s]`

### Colors don't show correctly
- Check background brightness setting (20-150%)
- Ensure sufficient contrast between text and background
- Test on the actual display device

### Kiosk display doesn't update
- Force reload from maintenance page
- Check PM2 status and restart if needed
- Verify database connectivity

## Performance Issues

### Kiosk runs slowly
- Check system resources: `top` or `htop`
- Reduce slideshow transition effects
- Optimize background image size
- Clear browser cache

### High CPU usage
- Check for runaway processes: `ps aux | head -20`
- Restart PM2 processes: `pm2 restart all`
- Monitor with: `pm2 monit`

## File Upload Issues

### Background images don't upload
- Check file permissions: `./permissions.sh /var/www/html`
- Verify disk space: `df -h`
- Check file size limits (max 10MB)
- Ensure image format is supported (JPG, PNG, AVIF)

### Custom fonts don't load
- Upload TTF files to fonts/ directory
- Check file permissions
- Restart server after font uploads

## Database Issues

### Menus don't save
- Check database file: `ls -la 314sign.db`
- Verify permissions: `chmod 664 314sign.db`
- Check disk space
- Restart server

### Old menus still show
- Force browser refresh (Ctrl+F5)
- Clear browser cache
- Check PM2 logs for errors

## Remote Viewer Issues

### Remote doesn't connect
- Verify main kiosk is online
- Check remote device ID in main kiosk
- Ensure both devices on same network segment
- Check firewall settings

### Remote shows wrong content
- Verify remote configuration in main kiosk
- Check network connectivity
- Restart remote device

## Recovery Procedures

### Emergency restart
```bash
# Stop all processes
sudo pm2 kill

# Restart server
cd /var/www/html
npm start
```

### Reset to defaults
```bash
# Backup current settings
cp config.json config.backup.json

# Reset configuration
cp config.json.example config.json
```

### Factory reset (CAUTION)
```bash
# This removes all data - backup first!
rm -rf /var/www/html/bg/uploaded_*
rm -rf /var/www/html/fonts/*.ttf
rm 314sign.db
npm run migrate
```

## Getting Help

### Check system status
```bash
# Full diagnostic
curl http://localhost/api/status

# Check logs
pm2 logs 314sign --lines 50
```

### Contact support
- Check GitHub issues for similar problems
- Include PM2 logs and system information
- Describe steps to reproduce the issue

## Prevention

### Regular maintenance
- Check PM2 status weekly: `pm2 list`
- Monitor disk space: `df -h`
- Keep system updated: `sudo apt update && sudo apt upgrade`
- Backup configuration monthly

### Best practices
- Test changes on a development setup first
- Keep multiple browser tabs open for testing
- Use the maintenance page for diagnostics
- Monitor logs regularly
