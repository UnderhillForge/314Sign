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

# Download and install Permanent Marker (Google Font - bold marker style)
echo "Installing Permanent Marker (bold marker font)..."
FONT_DIR="/usr/share/fonts/truetype/permanentmarker"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/apache/permanentmarker/PermanentMarker-Regular.ttf
sudo mv PermanentMarker-Regular.ttf "$FONT_DIR/"

# Download and install Bebas Neue (Google Font - tall, bold, impactful)
echo "Installing Bebas Neue (tall bold font)..."
FONT_DIR="/usr/share/fonts/truetype/bebasneue"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf
sudo mv BebasNeue-Regular.ttf "$FONT_DIR/"

# Download and install Shadows Into Light (Google Font - handwritten casual)
echo "Installing Shadows Into Light (casual handwriting)..."
FONT_DIR="/usr/share/fonts/truetype/shadowsintolight"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/apache/shadowsintolight/ShadowsIntoLight-Regular.ttf
sudo mv ShadowsIntoLight-Regular.ttf "$FONT_DIR/"

# Download and install Pacifico (Google Font - bold script, retro)
echo "Installing Pacifico (bold retro script)..."
FONT_DIR="/usr/share/fonts/truetype/pacifico"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf
sudo mv Pacifico-Regular.ttf "$FONT_DIR/"

# Download and install Bangers (Google Font - comic book style)
echo "Installing Bangers (comic book style)..."
FONT_DIR="/usr/share/fonts/truetype/bangers"
sudo mkdir -p "$FONT_DIR"
wget -q https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf
sudo mv Bangers-Regular.ttf "$FONT_DIR/"

# Refresh font cache
fc-cache -f -v

echo ""
echo "Fonts installed successfully!"
echo ""
echo "Available distinctive fonts:"
fc-list | grep -iE "Permanent|Bebas|Shadows|Pacifico|Bangers|Caveat|Kalam|Indie|Comfortaa|Lato" | cut -d: -f2 | sort -u

echo ""
echo "All installed fonts:"
fc-list | grep -iE "DejaVu|FreeSans|Liberation|Lato|Caveat|Kalam|Indie|Comfortaa|Quicksand|Permanent|Bebas|Shadows|Pacifico|Bangers" | cut -d: -f2 | sort -u

echo ""
echo "To use these fonts, select them in the design editor."
echo "Recommended for restaurant menus:"
echo "  - Bebas Neue (tall, bold, modern)"
echo "  - Permanent Marker (bold marker style)"
echo "  - Pacifico (retro script, fun)"
echo "  - Bangers (comic book, energetic)"
echo "  - Caveat (handwritten, casual)"
echo "  - Shadows Into Light (casual handwriting)"
echo "  - Lato (clean, modern)"
echo "  - DejaVu Sans (professional)"
