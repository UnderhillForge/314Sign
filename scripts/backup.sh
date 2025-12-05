#!/bin/bash
###############################################################################
# 314Sign Backup Script
# Creates timestamped backups of critical kiosk data
#
# Usage:
#   ./scripts/backup.sh [backup_directory]
#
# Default backup location: /var/backups/314sign/
# Backs up: menus/, config.json, menus-config.json, rules.json, bg/ (uploaded images only)
###############################################################################

set -e

# Configuration
BACKUP_ROOT="${1:-/var/backups/314sign}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
WEB_ROOT="/var/www/html"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "=== 314Sign Backup - $(date) ==="
echo "Backup location: ${BACKUP_DIR}"

# Backup menus
if [ -d "${WEB_ROOT}/menus" ]; then
  echo "Backing up menus..."
  cp -r "${WEB_ROOT}/menus" "${BACKUP_DIR}/"
fi

# Backup configuration
if [ -f "${WEB_ROOT}/config.json" ]; then
  echo "Backing up config.json..."
  cp "${WEB_ROOT}/config.json" "${BACKUP_DIR}/"
fi

# Backup menu configuration
if [ -f "${WEB_ROOT}/menus-config.json" ]; then
  echo "Backing up menus-config.json..."
  cp "${WEB_ROOT}/menus-config.json" "${BACKUP_DIR}/"
fi

# Backup schedule rules
if [ -f "${WEB_ROOT}/rules.json" ]; then
  echo "Backing up rules.json..."
  cp "${WEB_ROOT}/rules.json" "${BACKUP_DIR}/"
fi

# Backup uploaded images (exclude defaults)
if [ -d "${WEB_ROOT}/bg" ]; then
  echo "Backing up uploaded images..."
  mkdir -p "${BACKUP_DIR}/bg"
  # Only backup uploaded_* files to avoid duplicating default backgrounds
  find "${WEB_ROOT}/bg" -name "uploaded_*" -type f -exec cp {} "${BACKUP_DIR}/bg/" \; 2>/dev/null || true
  # Also backup custom images (anything not starting with bg1-bg9)
  find "${WEB_ROOT}/bg" -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.gif" \) ! -name "bg[0-9].*" ! -name "uploaded_*" -exec cp {} "${BACKUP_DIR}/bg/" \; 2>/dev/null || true
fi

# Create backup metadata
cat > "${BACKUP_DIR}/backup-info.txt" <<EOF
314Sign Backup
Created: $(date)
Hostname: $(hostname)
Web Root: ${WEB_ROOT}
Backup Contents:
- Menu files (menus/*.txt)
- Configuration (config.json)
- Schedule rules (rules.json)
- Uploaded images (bg/uploaded_*.*)
EOF

echo ""
echo "✓ Backup complete: ${BACKUP_DIR}"
echo ""
echo "To restore from this backup:"
echo "  sudo cp -r ${BACKUP_DIR}/menus/* ${WEB_ROOT}/menus/"
echo "  sudo cp ${BACKUP_DIR}/config.json ${WEB_ROOT}/"
echo "  sudo cp ${BACKUP_DIR}/rules.json ${WEB_ROOT}/"
echo "  sudo cp ${BACKUP_DIR}/bg/* ${WEB_ROOT}/bg/"
echo "  sudo chown -R www-data:www-data ${WEB_ROOT}/{menus,config.json,rules.json,bg}"
echo ""

# Optional: Remove backups older than 30 days
if [ -d "${BACKUP_ROOT}" ]; then
  echo "Cleaning up old backups (>30 days)..."
  find "${BACKUP_ROOT}" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
fi

echo "=== Backup Complete ==="
