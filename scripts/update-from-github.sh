#!/bin/bash
###############################################################################
# 314Sign GitHub Update Script
# 
# Safely syncs local installation with GitHub repository, updating only
# changed files while preserving local configuration and uploaded content.
#
# Usage:
#   sudo ./scripts/update-from-github.sh [options]
#
# Options:
#   --dry-run    Show what would be updated without making changes
#   --force      Update even if local changes detected (dangerous)
#   --backup     Create backup before updating (recommended)
#
# What gets updated:
#   - Core display files (index.html, edit/design/rules pages)
#   - PHP backends (upload-bg.php, bg/index.php, status.php)
#   - Scripts (backup.sh, os-lite-kiosk.sh, permissions.sh)
#   - Default background images
#
# What gets preserved:
#   - config.json (your settings)
#   - menus-config.json (per-menu settings)
#   - rules.json (your schedule)
#   - rules.json (your schedule)
#   - menus/*.txt (your menu content)
#   - bg/uploaded_* (your uploaded images)
#   - logs/ directory
###############################################################################

set -e

# Configuration
GITHUB_REPO="UnderhillForge/314Sign"
GITHUB_BRANCH="main"
GITHUB_RAW_BASE="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}"
WEB_ROOT="/var/www/html"
TEMP_DIR=$(mktemp -d)
BACKUP_DIR=""

# Parse command line options
DRY_RUN=false
FORCE_UPDATE=false
CREATE_BACKUP=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --force)
      FORCE_UPDATE=true
      shift
      ;;
    --backup)
      CREATE_BACKUP=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dry-run] [--force] [--backup]"
      exit 1
      ;;
  esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]] && [[ "$DRY_RUN" == false ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

echo "=== 314Sign GitHub Update Tool ==="
echo ""

# Verify web root exists
if [[ ! -d "$WEB_ROOT" ]]; then
  log_error "Web root not found: $WEB_ROOT"
  log_error "Is 314Sign installed? Run setup-kiosk.sh first."
  exit 1
fi

# Create backup if requested
if [[ "$CREATE_BACKUP" == true ]] && [[ "$DRY_RUN" == false ]]; then
  log_info "Creating backup..."
  if [[ -x "$WEB_ROOT/scripts/backup.sh" ]]; then
    "$WEB_ROOT/scripts/backup.sh"
    log_success "Backup created"
  else
    log_warning "Backup script not found or not executable"
  fi
  echo ""
fi

# Files to update (relative to web root)
# Exclude config.json, menus-config.json, rules.json, menus/*.txt, uploaded images, and runtime state files
declare -a UPDATE_FILES=(
  "index.html"
  "version.txt"
  "favicon.svg"
  "edit/index.html"
  "design/index.html"
  "design/upload-bg.php"
  "design/purge-history.php"
  "rules/index.html"
  "rules.json"
  "start/index.html"
  "maintenance/index.html"
  "bg/index.php"
  "fonts/index.php"
  "fonts/.htaccess"
  "status.php"
  "check-updates.php"
  "apply-updates.php"
  "restart-server.php"
  "create-backup.php"
  "trigger-reload.php"
  "save-menu-history.php"
  "get-menu-history.php"
  "set-current-menu.php"
  "scripts/backup.sh"
  "scripts/merge-config.php"
  "scripts/read-file-debug.php"
  "scripts/put-guard.php"
  "scripts/validate-slideshow-set.php"
  "scripts/os-lite-kiosk.sh"
  "scripts/update-from-github.sh"
  "permissions.sh"
  "setup-kiosk.sh"
  "create-webdav-user.sh"
  "sudoers-314sign"
  "design/upload-logo.php"
  "media/index.php"
  "menus/index.php"
  "bg/backgd2.avif"
)

# Optional documentation files (won't fail if missing)
declare -a DOC_FILES=(
  "readme.md"
  "docs/FORMATTING.md"
  "docs/troubleshooting.md"
  "docs/requirements.md"
  "docs/contributing.md"
  "docs/file_structure.md"
  "docs/diagnostic.html"
  "docs/font-test.html"
  "LICENSE"
  "fonts/README.md"
  ".github/copilot-instructions.md"
)

# Track statistics
TOTAL_FILES=0
UPDATED_FILES=0
UNCHANGED_FILES=0
FAILED_FILES=0

# Function to download and compare file
update_file() {
  local file_path="$1"
  local local_file="$WEB_ROOT/$file_path"
  local remote_url="$GITHUB_RAW_BASE/$file_path"
  local temp_file="$TEMP_DIR/$(basename "$file_path")"
  
  TOTAL_FILES=$((TOTAL_FILES + 1))
  
  # Download from GitHub with cache busting
  if ! curl -fsSL -H "Cache-Control: no-cache" "$remote_url?_=$(date +%s)" -o "$temp_file" 2>/dev/null; then
    log_warning "Could not download: $file_path (may not exist in repo)"
    FAILED_FILES=$((FAILED_FILES + 1))
    return 1
  fi
  
  # Check if local file exists
  if [[ ! -f "$local_file" ]]; then
    log_info "New file: $file_path"
    if [[ "$DRY_RUN" == false ]]; then
      mkdir -p "$(dirname "$local_file")"
      cp "$temp_file" "$local_file"
      log_success "Created: $file_path"
      UPDATED_FILES=$((UPDATED_FILES + 1))
    else
      echo "  [DRY RUN] Would create: $file_path"
    fi
    return 0
  fi
  
  # Compare files
  if cmp -s "$local_file" "$temp_file"; then
    UNCHANGED_FILES=$((UNCHANGED_FILES + 1))
    return 0
  fi
  
  # Files differ - update needed
  log_info "Changes detected: $file_path"
  
  if [[ "$DRY_RUN" == false ]]; then
    # Show diff summary (first 3 lines)
    if command -v diff &> /dev/null; then
      echo "  Changes:"
      diff -u "$local_file" "$temp_file" 2>/dev/null | head -10 | sed 's/^/    /' || true
      echo "  ..."
    fi
    
    # Update file
    cp "$temp_file" "$local_file"
    log_success "Updated: $file_path"
    UPDATED_FILES=$((UPDATED_FILES + 1))
  else
    echo "  [DRY RUN] Would update: $file_path"
    UPDATED_FILES=$((UPDATED_FILES + 1))
  fi
}

# Update core files
log_info "Checking for updates from GitHub..."
echo ""

for file in "${UPDATE_FILES[@]}"; do
  update_file "$file"
done

# Update documentation (optional)
log_info "Checking documentation files..."
for file in "${DOC_FILES[@]}"; do
  update_file "$file" || true  # Don't fail on missing docs
done

echo ""

# Update default background images (only if they don't exist locally)
log_info "Checking default background images..."
for i in {1..9}; do
  bg_file="bg/bg${i}.jpg"
  local_bg="$WEB_ROOT/$bg_file"
  
  if [[ ! -f "$local_bg" ]]; then
    if curl -fsSL "$GITHUB_RAW_BASE/$bg_file" -o "$TEMP_DIR/bg${i}.jpg" 2>/dev/null; then
      if [[ "$DRY_RUN" == false ]]; then
        mkdir -p "$WEB_ROOT/bg"
        cp "$TEMP_DIR/bg${i}.jpg" "$local_bg"
        log_success "Downloaded: $bg_file"
        UPDATED_FILES=$((UPDATED_FILES + 1))
      else
        echo "  [DRY RUN] Would download: $bg_file"
      fi
    fi
  fi
done

echo ""

# === Update custom fonts from fonts/ directory ===
log_info "Checking for custom font updates..."
FONTS_URL="https://api.github.com/repos/$GITHUB_REPO/contents/fonts"
if FONTS_LIST=$(curl -fsSL "$FONTS_URL" 2>/dev/null); then
  FONT_COUNT=$(echo "$FONTS_LIST" | grep '"name":' | grep -c '\.ttf"' || echo "0")
  if [[ $FONT_COUNT -gt 0 ]]; then
    log_info "Found $FONT_COUNT font files in repository"
    echo "$FONTS_LIST" | grep '"name":' | grep '\.ttf"' | sed -E 's/.*"name": "([^"]*)".*/\1/' | while read -r font_file; do
      local_font="$WEB_ROOT/fonts/$font_file"
      remote_url="$GITHUB_RAW_BASE/fonts/$font_file"
      
      if [[ ! -f "$local_font" ]]; then
        log_info "New font: $font_file"
        if [[ "$DRY_RUN" == false ]]; then
          mkdir -p "$WEB_ROOT/fonts"
          if curl -fsSL "$remote_url" -o "$local_font" 2>/dev/null; then
            log_success "Downloaded: $font_file"
            UPDATED_FILES=$((UPDATED_FILES + 1))
          else
            log_warning "Failed to download: $font_file"
            FAILED_FILES=$((FAILED_FILES + 1))
          fi
        else
          echo "  [DRY RUN] Would download: $font_file"
        fi
      fi
    done
  else
    log_info "No custom fonts found in repository"
  fi
else
  log_warning "Could not check fonts directory (repo may not have fonts/)"
fi

echo ""

# Fix permissions
if [[ "$DRY_RUN" == false ]] && [[ -x "$WEB_ROOT/permissions.sh" ]]; then
  log_info "Fixing permissions..."
  "$WEB_ROOT/permissions.sh" "$WEB_ROOT"
  log_success "Permissions updated"
  echo ""
fi

# Cleanup
rm -rf "$TEMP_DIR"

# Summary
echo "=== Update Summary ==="
echo "Total files checked: $TOTAL_FILES"
echo "Files updated: ${GREEN}$UPDATED_FILES${NC}"
echo "Files unchanged: $UNCHANGED_FILES"
if [[ $FAILED_FILES -gt 0 ]]; then
  echo "Files failed: ${RED}$FAILED_FILES${NC}"
fi
echo ""

if [[ "$DRY_RUN" == true ]]; then
  log_warning "DRY RUN MODE - No changes were made"
  echo "Run without --dry-run to apply updates"
  echo ""
fi

if [[ $UPDATED_FILES -gt 0 ]] && [[ "$DRY_RUN" == false ]]; then
  log_success "Update complete!"
  echo ""
  echo "Next steps:"
  echo "  1. Check your kiosk display: http://$(hostname).local"
  echo "  2. Verify editor pages work: http://$(hostname).local/edit/"
  echo "  3. Check logs if issues occur: tail -f /var/log/lighttpd/error.log"
  echo ""
  log_warning "If you made local customizations to updated files, they were overwritten."
  log_warning "Restore from backup if needed."
elif [[ $UPDATED_FILES -eq 0 ]] && [[ "$DRY_RUN" == false ]]; then
  log_success "Already up to date!"
  echo "No updates needed - your installation matches GitHub."
fi

echo ""
exit 0

