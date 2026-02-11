#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export DISPLAY="${DISPLAY:-:0}"

xauth_path="$(ps aux | grep '[X] ' | grep -o '\-auth [^ ]*' | head -n1 | awk '{print $2}')"
if [[ -n "${xauth_path}" && -f "${xauth_path}" ]]; then
  export XAUTHORITY="${xauth_path}"
elif [[ -f "/home/${USER}/.Xauthority" ]]; then
  export XAUTHORITY="/home/${USER}/.Xauthority"
fi

echo "[kiosk] DISPLAY=${DISPLAY}"
echo "[kiosk] XAUTHORITY=${XAUTHORITY:-unset}"

cd "${APP_DIR}"
exec /usr/bin/env npm start
