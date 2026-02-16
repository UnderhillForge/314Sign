#!/bin/bash
# Download curated Google Fonts as WOFF2 files
# Usage: ./download-fonts.sh

FONTS_DIR="$(dirname "$0")"
cd "$FONTS_DIR" || exit 1

echo "Downloading curated Google Fonts as WOFF2..."

# Function to download font from Google Fonts API
download_font() {
  local family="$1"
  local filename="$2"
  
  echo "Downloading $family..."
  
  # Get the CSS from Google Fonts with User-Agent to request WOFF2
  local css_url="https://fonts.googleapis.com/css2?family=${family}&display=swap"
  local css_content
  css_content=$(curl -s -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" "$css_url")
  
  # Extract WOFF2 URL from CSS (get the last/most compatible one)
  local woff2_url
  woff2_url=$(echo "$css_content" | grep -o "https://[^)]*\.woff2" | tail -n 1 | tr -d '\n')
  
  if [ -n "$woff2_url" ]; then
    curl -s -o "$filename" "$woff2_url"
    echo "  ✓ Saved to $filename"
  else
    echo "  ✗ Failed to find WOFF2 URL for $family"
  fi
}

# Download each font
download_font "Roboto" "Roboto-Regular.woff2"
download_font "Open+Sans" "OpenSans-Regular.woff2"
download_font "Lato" "Lato-Regular.woff2"
download_font "Source+Sans+Pro" "SourceSansPro-Regular.woff2"
download_font "Nunito" "Nunito-Regular.woff2"
download_font "Raleway" "Raleway-Regular.woff2"
download_font "Indie+Flower" "IndieFlower-Regular.woff2"
download_font "Permanent+Marker" "PermanentMarker-Regular.woff2"
download_font "Caveat" "Caveat-Regular.woff2"
download_font "Amatic+SC" "AmaticSC-Regular.woff2"
download_font "Bebas+Neue" "BebasNeue-Regular.woff2"
download_font "Oswald" "Oswald-Regular.woff2"

echo ""
echo "Font download complete!"
echo "Files saved to: $FONTS_DIR"

# Set proper permissions
chmod 644 *.woff2 2>/dev/null

echo "Done!"
