# Custom Fonts Directory

Place `.ttf` font files in this directory to make them available in the design editor.

## How to Add Fonts

1. **Upload TTF files** to this directory via SFTP/SCP:
   ```bash
   scp YourFont.ttf pi@314sign:/var/www/html/fonts/
   ```

2. **Set permissions**:
   ```bash
   sudo chown www-data:www-data /var/www/html/fonts/YourFont.ttf
   sudo chmod 644 /var/www/html/fonts/YourFont.ttf
   ```

3. **Refresh the design page** - fonts are auto-detected and added to the dropdown

## Font Guidelines

- **Format**: Only `.ttf` files (TrueType fonts)
- **Avoid**: Variable fonts (`[wght]` in filename) - they may not work in Chromium on Pi
- **Naming**: Use clear, descriptive filenames (e.g., `BebasNeue-Regular.ttf`)
- **Testing**: Always test on the HDMI display before committing to a design

## Recommended Sources

- [Google Fonts](https://fonts.google.com/) - Free, open-source fonts
- [Font Squirrel](https://www.fontsquirrel.com/) - Free commercial fonts
- [DaFont](https://www.dafont.com/) - Check licenses carefully

## Current System Fonts

These are always available (installed via `scripts/install-fonts.sh`):
- Lato
- Bebas Neue
- Permanent Marker
- Caveat
- Shadows Into Light

## Notes

- Fonts in this directory are served via CSS `@font-face` rules
- Large font files (>1MB) may slow page loading
- Font licensing: Ensure you have the right to use fonts for commercial signage
