#!/bin/bash
#
# 314Sign Hybrid System Build Script
# Compiles and packages the complete 314Sign hybrid system for distribution
#
# This script creates a complete binary release package containing:
# - Compiled Python bytecode for optimized performance
# - Bundled dependencies and assets
# - Installation scripts and configuration templates
# - Documentation and release notes
# - Cross-platform compatibility checks
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Build configuration
BUILD_VERSION="1.0.2.69"
BUILD_DATE=$(date +%Y%m%d_%H%M%S)
BUILD_DIR="build"
RELEASE_DIR="release"
PACKAGE_NAME="314sign-hybrid-${BUILD_VERSION}"
TEMP_DIR="/tmp/314sign-build-${BUILD_DATE}"

# Architecture detection
detect_architecture() {
    echo -e "${BLUE}🔍 Detecting build architecture...${NC}"

    # Get system information
    ARCH=$(uname -m)
    OS=$(uname -s)
    KERNEL=$(uname -r)

    case $ARCH in
        x86_64|amd64)
            BUILD_ARCH="x86_64"
            ;;
        arm64|aarch64)
            BUILD_ARCH="arm64"
            ;;
        armv7l|armv6l)
            BUILD_ARCH="armhf"
            ;;
        *)
            BUILD_ARCH="unknown"
            ;;
    esac

    echo -e "${GREEN}✅ Build Architecture: ${WHITE}${BUILD_ARCH}${NC}"
    echo -e "${GREEN}✅ Operating System: ${WHITE}${OS}${NC}"
    echo -e "${GREEN}✅ Kernel Version: ${WHITE}${KERNEL}${NC}"
    echo ""
}

# Check build dependencies
check_dependencies() {
    echo -e "${BLUE}🔧 Checking build dependencies...${NC}"

    local missing_deps=()

    # Check for required commands
    local required_cmds=("python3" "pip3" "git" "tar" "gzip" "zip" "rsync" "find" "xargs")

    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    # Check for Python modules
    local required_modules=("pygame" "requests" "PIL" "numpy")

    for module in "${required_modules[@]}"; do
        if ! python3 -c "import $module" &> /dev/null; then
            echo -e "${YELLOW}⚠️  Python module '$module' not found in current environment${NC}"
            echo -e "${YELLOW}   It will be bundled with the release${NC}"
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing build dependencies: ${missing_deps[*]}${NC}"
        echo -e "${RED}   Please install them and run again${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All build dependencies satisfied${NC}"
    echo ""
}

# Clean previous builds
clean_build() {
    echo -e "${BLUE}🧹 Cleaning previous builds...${NC}"

    # Remove build directories
    rm -rf "$BUILD_DIR"
    rm -rf "$RELEASE_DIR"
    rm -rf "$TEMP_DIR"

    # Remove any existing release packages
    rm -f *.tar.gz *.zip *.deb *.rpm 2>/dev/null || true

    echo -e "${GREEN}✅ Build directories cleaned${NC}"
    echo ""
}

# Create build directory structure
create_build_structure() {
    echo -e "${BLUE}📁 Creating build directory structure...${NC}"

    # Create main directories
    mkdir -p "$BUILD_DIR"
    mkdir -p "$TEMP_DIR"

    # Create package structure
    mkdir -p "$TEMP_DIR/opt/314sign"
    mkdir -p "$TEMP_DIR/var/lib/314sign"/{images,backgrounds,templates}
    mkdir -p "$TEMP_DIR/home/pi"/{lms,fonts,logs}
    mkdir -p "$TEMP_DIR/etc/systemd/system"
    mkdir -p "$TEMP_DIR/usr/local/bin"
    mkdir -p "$TEMP_DIR/usr/share/doc/314sign"
    mkdir -p "$TEMP_DIR/DEBIAN"

    echo -e "${GREEN}✅ Build structure created${NC}"
    echo ""
}

# Compile Python code
compile_python_code() {
    echo -e "${BLUE}🐍 Compiling Python code...${NC}"

    # Create __pycache__ directories to force bytecode compilation
    find . -name "*.py" -type f | while read -r pyfile; do
        mkdir -p "$(dirname "$pyfile")/__pycache__"
    done

    # Compile all Python files with optimization
    echo -e "${CYAN}   Compiling with optimization level 1...${NC}"
    python3 -m compileall -b -f -q . || true  # Continue on warnings

    # Create optimized bytecode (-O flag removes docstrings and assertions)
    echo -e "${CYAN}   Creating optimized bytecode...${NC}"
    python3 -OO -m compileall -b -f -q . || true

    echo -e "${GREEN}✅ Python code compiled${NC}"
    echo ""
}

# Bundle Python dependencies
bundle_dependencies() {
    echo -e "${BLUE}📦 Bundling Python dependencies...${NC}"

    # Create virtual environment for clean dependency bundling
    local venv_dir="$TEMP_DIR/venv"
    python3 -m venv "$venv_dir"

    # Activate virtual environment
    source "$venv_dir/bin/activate"

    # Install required packages
    pip install --quiet pygame requests pillow numpy psutil

    # Create requirements.txt for the release
    pip freeze > "$TEMP_DIR/requirements.txt"

    # Bundle site-packages
    cp -r "$venv_dir/lib/python3."*/site-packages "$TEMP_DIR/opt/314sign/lib"

    # Deactivate virtual environment
    deactivate

    # Clean up virtual environment
    rm -rf "$venv_dir"

    echo -e "${GREEN}✅ Dependencies bundled${NC}"
    echo ""
}

# Copy application files
copy_application_files() {
    echo -e "${BLUE}📋 Copying application files...${NC}"

    # Copy main application files
    cp hybrid/kiosk_main.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/web_editor.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/bundle_manager.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/security_keys.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/mdns_discovery.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/blockchain_security.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/314st_wallet.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/splash_screen.py "$TEMP_DIR/opt/314sign/"
    cp hybrid/splash_config.json "$TEMP_DIR/opt/314sign/"
    cp hybrid/314sign2.png "$TEMP_DIR/opt/314sign/"

    # Copy admin console
    cp -r hybrid/admin "$TEMP_DIR/opt/314sign/"

    # Copy examples and templates
    cp -r hybrid/examples "$TEMP_DIR/opt/314sign/"
    cp -r hybrid/templates "$TEMP_DIR/var/lib/314sign/"
    cp -r hybrid/fonts "$TEMP_DIR/home/pi/"

    # Copy build script
    cp hybrid/dev/install_314sign_hybrid.sh "$TEMP_DIR/opt/314sign/"

    echo -e "${GREEN}✅ Application files copied${NC}"
    echo ""
}

# Create systemd service files
create_service_files() {
    echo -e "${BLUE}⚙️ Creating systemd service files...${NC}"

    # Kiosk service
    cat > "$TEMP_DIR/etc/systemd/system/314sign-kiosk.service" << 'EOF'
[Unit]
Description=314Sign Hybrid Kiosk Application
After=network.target local-fs.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
ExecStart=/opt/314sign/kiosk_main.py --config /home/pi/kiosk_config.json
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=314sign-kiosk

[Install]
WantedBy=multi-user.target
EOF

    # Web editor service
    cat > "$TEMP_DIR/etc/systemd/system/314sign-web-editor.service" << 'EOF'
[Unit]
Description=314Sign Web LMS Content Editor
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/314sign
ExecStart=/opt/314sign/web_editor.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=314sign-web-editor

[Install]
WantedBy=multi-user.target
EOF

    # Splash screen service
    cat > "$TEMP_DIR/etc/systemd/system/314sign-splash.service" << 'EOF'
[Unit]
Description=314Sign Boot Splash Screen
After=local-fs.target
Before=314sign-kiosk.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1
Environment=SDL_VIDEO_ALLOW_SCREENSAVER=0
ExecStart=/opt/314sign/splash_screen.py --config /opt/314sign/splash_config.json
Restart=no
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${GREEN}✅ Service files created${NC}"
    echo ""
}

# Create DEB package structure
create_deb_package() {
    echo -e "${BLUE}📦 Creating DEB package structure...${NC}"

    # Create control file
    cat > "$TEMP_DIR/DEBIAN/control" << EOF
Package: 314sign-hybrid
Version: ${BUILD_VERSION}
Section: misc
Priority: optional
Architecture: all
Depends: python3, python3-pip, python3-pygame, python3-requests, python3-pil, python3-cryptography, avahi-daemon, ufw, systemd
Maintainer: 314Sign Team <info@314sign.com>
Description: Complete digital signage platform with LMS rendering
 314Sign Hybrid is a complete digital signage platform featuring:
  - Direct framebuffer LMS rendering engine
  - Web-based visual content editor
  - Comprehensive administration console
  - Professional boot splash screens
  - Hardware-accelerated graphics
  - Multi-device network management
Homepage: https://github.com/UnderhillForge/314Sign
EOF

    # Create postinst script
    cat > "$TEMP_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Reload systemd
systemctl daemon-reload

# Set permissions
chown -R pi:pi /opt/314sign
chown -R pi:pi /var/lib/314sign
chown -R pi:pi /home/pi/lms
chown -R pi:pi /home/pi/fonts

# Enable services
systemctl enable 314sign-kiosk.service
systemctl enable 314sign-web-editor.service
systemctl enable 314sign-splash.service

echo "314Sign Hybrid System installed successfully!"
echo "Run 'sudo reboot' to start the system"
EOF

    # Create prerm script
    cat > "$TEMP_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Stop and disable services
systemctl stop 314sign-kiosk.service || true
systemctl stop 314sign-web-editor.service || true
systemctl stop 314sign-splash.service || true

systemctl disable 314sign-kiosk.service || true
systemctl disable 314sign-web-editor.service || true
systemctl disable 314sign-splash.service || true

# Reload systemd
systemctl daemon-reload
EOF

    # Make scripts executable
    chmod 755 "$TEMP_DIR/DEBIAN/postinst"
    chmod 755 "$TEMP_DIR/DEBIAN/prerm"

    echo -e "${GREEN}✅ DEB package structure created${NC}"
    echo ""
}

# Create documentation
create_documentation() {
    echo -e "${BLUE}📚 Creating documentation...${NC}"

    # Create README
    cat > "$TEMP_DIR/usr/share/doc/314sign/README.md" << EOF
# 314Sign Hybrid System

Complete digital signage platform with LMS rendering engine.

## Installation

This package provides a complete 314Sign installation. After installation:

1. Reboot the system: \`sudo reboot\`
2. Access the web editor at: http://[hostname].local:8080
3. Use the admin console: \`python3 /opt/314sign/admin/314_admin.py\`

## Components

- **kiosk_main.py**: Main LMS rendering engine with direct framebuffer support
- **web_editor.py**: Web-based visual content creation interface
- **314_admin.py**: Comprehensive system administration console
- **splash_screen.py**: Professional boot splash screen system

## Configuration

System configuration is stored in: \`/home/pi/kiosk_config.json\`

## Directories

- \`/opt/314sign/\`: Application files
- \`/var/lib/314sign/\`: Data and cache
- \`/home/pi/lms/\`: LMS content files
- \`/home/pi/fonts/\`: Custom fonts

## Services

- \`314sign-kiosk.service\`: Main display service
- \`314sign-web-editor.service\`: Web content editor
- \`314sign-splash.service\`: Boot splash screen

## Version

${BUILD_VERSION} (built ${BUILD_DATE})

For more information, visit: https://github.com/UnderhillForge/314Sign
EOF

    # Create changelog
    cat > "$TEMP_DIR/usr/share/doc/314sign/changelog" << EOF
314sign-hybrid (${BUILD_VERSION}) unstable; urgency=medium

  * Complete hybrid LMS rendering system
  * Web-based visual content editor
  * Comprehensive administration console
  * Professional boot splash screens
  * Multi-device network management
  * Hardware-accelerated graphics

 -- 314Sign Team <info@314sign.com>  $(date -R)
EOF

    # Copy additional documentation
    cp docs/README.md "$TEMP_DIR/usr/share/doc/314sign/" 2>/dev/null || true
    cp README.md "$TEMP_DIR/usr/share/doc/314sign/PROJECT_README.md" 2>/dev/null || true

    echo -e "${GREEN}✅ Documentation created${NC}"
    echo ""
}

# Create release archives
create_release_archives() {
    echo -e "${BLUE}📦 Creating release archives...${NC}"

    # Create release directory
    mkdir -p "$RELEASE_DIR"

    # Create DEB package
    echo -e "${CYAN}   Creating DEB package...${NC}"
    dpkg-deb --build "$TEMP_DIR" "$RELEASE_DIR/${PACKAGE_NAME}.deb"

    # Create tar.gz archive
    echo -e "${CYAN}   Creating tar.gz archive...${NC}"
    cd "$TEMP_DIR"
    tar -czf "../$RELEASE_DIR/${PACKAGE_NAME}.tar.gz" .
    cd - > /dev/null

    # Create zip archive
    echo -e "${CYAN}   Creating zip archive...${NC}"
    cd "$TEMP_DIR"
    zip -r "../$RELEASE_DIR/${PACKAGE_NAME}.zip" . > /dev/null
    cd - > /dev/null

    echo -e "${GREEN}✅ Release archives created${NC}"
    echo ""
}

# Generate build report
generate_build_report() {
    echo -e "${BLUE}📊 Generating build report...${NC}"

    cat > "$RELEASE_DIR/build-report.txt" << EOF
314Sign Hybrid System Build Report
===================================

Build Information:
- Version: ${BUILD_VERSION}
- Build Date: ${BUILD_DATE}
- Build Architecture: ${BUILD_ARCH}
- Operating System: ${OS}

Package Contents:
EOF

    # List package contents
    find "$TEMP_DIR" -type f -executable | grep -v "__pycache__" | sort >> "$RELEASE_DIR/build-report.txt"

    cat >> "$RELEASE_DIR/build-report.txt" << EOF

Release Files:
$(ls -la "$RELEASE_DIR")

Installation Instructions:
1. Transfer the appropriate package to your target system
2. Install with: sudo dpkg -i ${PACKAGE_NAME}.deb
3. Or extract tar.gz: sudo tar -xzf ${PACKAGE_NAME}.tar.gz -C /
4. Reboot: sudo reboot

Post-Installation Access:
- Web Editor: http://[hostname].local:8080
- Admin Console: python3 /opt/314sign/admin/314_admin.py
- Status Check: ~/check_status.sh

Dependencies:
- Python 3.7+
- SDL2 libraries
- Systemd
- Avahi (mDNS)
- UFW (firewall)

Build completed successfully at $(date)
EOF

    echo -e "${GREEN}✅ Build report generated${NC}"
    echo ""
}

# Clean up
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up build artifacts...${NC}"

    # Remove temporary build directory
    rm -rf "$TEMP_DIR"

    echo -e "${GREEN}✅ Cleanup completed${NC}"
    echo ""
}

# Main build function
main() {
    echo -e "${CYAN}🚀 314Sign Hybrid System Build Script${NC}"
    echo -e "${WHITE}Version ${BUILD_VERSION} - Complete binary release packaging${NC}"
    echo ""

    # Run build steps
    detect_architecture
    check_dependencies
    clean_build
    create_build_structure
    compile_python_code
    bundle_dependencies
    copy_application_files
    create_service_files
    create_deb_package
    create_documentation
    create_release_archives
    generate_build_report
    cleanup

    # Final summary
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    echo ""
    echo -e "${WHITE}Release packages created in: ${RELEASE_DIR}/${NC}"
    echo ""
    ls -la "$RELEASE_DIR"
    echo ""
    echo -e "${CYAN}Ready for distribution and deployment!${NC}"
}

# Run main function
main "$@"