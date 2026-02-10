#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="314sign-kiosk"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
RUN_USER="${SUDO_USER:-$USER}"
PORT="${KIOSK_PORT:-80}"

usage() {
  cat <<EOF
Usage: $0 [--port PORT] [--user USER]

Installs dependencies, builds the app, and installs a systemd service.

Options:
  --port PORT   HTTP port for 314Sign server (default: 80)
  --user USER   Run the service as this user (default: current user)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift 2
      ;;
    --user)
      RUN_USER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${RUN_USER}" ]]; then
  echo "Could not determine run user" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found in PATH" >&2
  exit 1
fi

if [[ ! -f "${APP_DIR}/package.json" ]]; then
  echo "package.json not found at ${APP_DIR}" >&2
  exit 1
fi

if [[ ! -f "${APP_DIR}/packages/314Sign/package.json" ]]; then
  echo "packages/314Sign/package.json not found" >&2
  exit 1
fi

echo "[install] Using app dir: ${APP_DIR}"

echo "[install] Installing root dependencies..."
cd "${APP_DIR}"
npm install

echo "[install] Installing 314Sign dependencies..."
cd "${APP_DIR}/packages/314Sign"
npm install

cd "${APP_DIR}"

echo "[install] Building kiosk app and 314Sign server..."
npm run build

if [[ "${PORT}" == "80" ]]; then
  NODE_BIN="$(command -v node)"
  if [[ -z "${NODE_BIN}" ]]; then
    echo "node not found in PATH" >&2
    exit 1
  fi

  echo "[install] Granting node permission to bind privileged ports (cap_net_bind_service)..."
  sudo setcap 'cap_net_bind_service=+ep' "${NODE_BIN}"
fi

if [[ $EUID -ne 0 ]]; then
  echo "[install] Elevating to write systemd service..."
fi

sudo tee "${SERVICE_FILE}" >/dev/null <<EOF
[Unit]
Description=314Sign Electron Kiosk
After=network.target
Wants=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
Environment=NODE_ENV=production
Environment=KIOSK_PORT=${PORT}
Environment=KIOSK_HOST=127.0.0.1
ExecStart=/usr/bin/env npm start
Restart=always
RestartSec=3
TimeoutStopSec=20
KillSignal=SIGTERM
StandardOutput=journal
StandardError=journal
SyslogIdentifier=314sign-kiosk

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "[install] Service installed and started: ${SERVICE_NAME}"
if [[ "${PORT}" == "80" ]]; then
  echo "[install] Admin UI: http://314sign.local/start"
else
  echo "[install] Admin UI: http://314sign.local:${PORT}/start"
fi
