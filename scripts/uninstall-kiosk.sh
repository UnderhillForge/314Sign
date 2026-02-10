#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="314sign-kiosk"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo systemctl stop "${SERVICE_NAME}" || true
sudo systemctl disable "${SERVICE_NAME}" || true

if [[ -f "${SERVICE_FILE}" ]]; then
  sudo rm -f "${SERVICE_FILE}"
fi

sudo systemctl daemon-reload

echo "[uninstall] Service removed: ${SERVICE_NAME}"
