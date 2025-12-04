#!/bin/bash
# Install additional fonts for 314Sign kiosk
# These are casual/fun fonts that work well for restaurant menus

set -e

echo "Installing additional fonts for 314Sign..."

# Update package lists
sudo apt-get update

# Install fonts-liberation2 (includes Liberation Sans which is similar to Arial)
sudo apt-get install -y fonts-liberation2

# Install fonts-dejavu (high quality, widely used)
sudo apt-get install -y fonts-dejavu fonts-dejavu-extra

# Install fonts-freefont-ttf (includes casual fonts)
sudo apt-get install -y fonts-freefont-ttf

# Install fonts-noto (Google's Noto fonts - excellent coverage)
sudo apt-get install -y fonts-noto

# Install fonts-lato (modern, friendly sans-serif)
sudo apt-get install -y fonts-lato

# Install fonts-opensymbol (symbols and decorative)
sudo apt-get install -y fonts-opensymbol

# Refresh font cache
fc-cache -f -v

echo ""
echo "Fonts installed successfully!"
echo ""
echo "Available casual/fun fonts:"
fc-list | grep -iE "DejaVu|FreeSans|Liberation|Lato" | cut -d: -f2 | sort -u | head -20

echo ""
echo "To use these fonts, select them in the design editor."
echo "Recommended for restaurant menus:"
echo "  - DejaVu Sans (clean, readable)"
echo "  - FreeSans (casual, friendly)"
echo "  - Liberation Sans (Arial alternative)"
echo "  - Lato (modern, geometric)"
