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

# Install handwriting/chalkboard-style fonts
echo "Installing handwriting and casual fonts..."
sudo apt-get install -y fonts-hanazono          # Decorative
sudo apt-get install -y fonts-comfortaa         # Rounded, friendly
sudo apt-get install -y fonts-quicksand         # Geometric, casual

# Download and install Caveat (Google Font - handwritten style, similar to Chalkduster)
echo "Installing Caveat (handwritten font)..."
FONT_DIR="/usr/share/fonts/truetype/caveat"
sudo mkdir -p "$FONT_DIR"
cd /tmp
wget -q https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf -O Caveat.ttf
sudo mv Caveat.ttf "$FONT_DIR/"

# Download and install Kalam (Google Font - handwritten, similar to Chalkboard)
echo "Installing Kalam (handwritten font)..."
FONT_DIR="/usr/share/fonts/truetype/kalam"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf
wget -q https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Bold.ttf
sudo mv Kalam-*.ttf "$FONT_DIR/"

# Download and install Indie Flower (Google Font - casual handwriting)
echo "Installing Indie Flower (casual handwritten font)..."
FONT_DIR="/usr/share/fonts/truetype/indieflower"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower-Regular.ttf
sudo mv IndieFlower-Regular.ttf "$FONT_DIR/"

# Refresh font cache
fc-cache -f -v

echo ""
echo "Fonts installed successfully!"
echo ""
echo "Available handwriting/chalkboard-style fonts:"
fc-list | grep -iE "Caveat|Kalam|Indie|Comfortaa|Quicksand" | cut -d: -f2 | sort -u

echo ""
echo "All installed fonts:"
fc-list | grep -iE "DejaVu|FreeSans|Liberation|Lato|Caveat|Kalam|Indie|Comfortaa|Quicksand" | cut -d: -f2 | sort -u

echo ""
echo "To use these fonts, select them in the design editor."
echo "Recommended for restaurant menus:"
echo "  - Lato (modern, geometric)"
echo "  - Caveat (handwritten, casual)"
echo "  - Kalam (handwritten, bold)"
echo "  - Indie Flower (playful, casual)"
echo "  - Comfortaa (rounded, friendly)"
echo "  - DejaVu Sans (clean, readable)"
