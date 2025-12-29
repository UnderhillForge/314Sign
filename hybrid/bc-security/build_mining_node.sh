#!/bin/bash
# 314Sign Mining Node Build Script
# Compiles the standalone mining node executable for systemd deployment

set -e

echo "🔨 Building 314Sign Mining Node executable..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing via apt..."
    sudo apt update && sudo apt install -y python3-pyinstaller
fi

# Check if we're in the right directory
if [ ! -f "314st-mining-node.py" ]; then
    echo "❌ 314st-mining-node.py not found. Run this script from bc-security/ directory."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec~

# Build the executable
echo "⚙️  Building executable with PyInstaller..."
pyinstaller --clean mining_node.spec

# Check if build succeeded
if [ ! -f "dist/314st-mining-node" ]; then
    echo "❌ Build failed - executable not found"
    exit 1
fi

echo "✅ Build successful!"

# Show executable info
echo "📊 Executable details:"
ls -la dist/314st-mining-node
file dist/314st-mining-node

# Test the executable (basic)
echo "🧪 Testing executable..."
if timeout 5s ./dist/314st-mining-node --help > /dev/null 2>&1; then
    echo "✅ Executable test passed"
else
    echo "⚠️  Executable test failed - may not work on this system"
fi

echo ""
echo "🎉 Mining node executable ready at: dist/314st-mining-node"
echo ""
echo "To install as systemd service:"
echo "  sudo cp dist/314st-mining-node /usr/local/bin/"
echo "  sudo cp 314sign-mining.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable 314sign-mining"
echo "  sudo systemctl start 314sign-mining"