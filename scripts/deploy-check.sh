 #!/usr/bin/env bash
# scripts/deploy-check.sh
# Lightweight deploy verification script.
# Usage: ./scripts/deploy-check.sh [BASE_URL] [WEB_ROOT]
# If BASE_URL is provided (e.g. http://localhost:8000) the script will attempt HTTP checks (ETag).
# WEB_ROOT defaults to current directory's parent (repo root) and is used to check file ownership/permissions.

set -euo pipefail

BASE_URL=${1:-}
WEB_ROOT=${2:-$(pwd)}

OK=0
ERR=0

function ok() { echo "[OK] $1"; OK=$((OK+1)); }
function warn() { echo "[WARN] $1"; }
function fail() { echo "[FAIL] $1"; ERR=$((ERR+1)); }

echo "Deploy check - WEB_ROOT=$WEB_ROOT BASE_URL=${BASE_URL:-(none)}"

echo "\n1) Check version.txt readability"
if [ -r "$WEB_ROOT/version.txt" ]; then
  ok "version.txt readable"
else
  fail "version.txt missing or not readable at $WEB_ROOT/version.txt"
fi

# Directories to check
declare -a DIRS=("$WEB_ROOT/bg" "$WEB_ROOT/media" "$WEB_ROOT/menus" "$WEB_ROOT/slideshows/media")

echo "\n2) Check writable dirs and ownership (prefer www-data)"
for d in "${DIRS[@]}"; do
  if [ -e "$d" ]; then
    if [ -w "$d" ]; then
      owner=$(stat -c '%U' "$d" 2>/dev/null || echo unknown)
      ok "$d writable (owner: $owner)"
    else
      owner=$(stat -c '%U' "$d" 2>/dev/null || echo unknown)
      fail "$d not writable (owner: $owner). Run permissions.sh to fix ownership and permissions."
    fi
  else
    warn "$d does not exist (skipping)"
  fi
done

# Check ETag via HTTP if BASE_URL provided
if [ -n "$BASE_URL" ]; then
  echo "\n3) Check HTTP ETag for index.html"
  set +e
  hdrs=$(curl -sI "$BASE_URL/" -m 5)
  set -e
  if echo "$hdrs" | grep -i '^ETag:' >/dev/null; then
    etag=$(echo "$hdrs" | grep -i '^ETag:' | head -n1 | sed -E 's/ETag:\s*//I' | tr -d '\r')
    ok "ETag present: $etag"
  else
    warn "No ETag header detected for $BASE_URL/. Server may not be configured to send ETags."
  fi

  echo "\n4) Check sample resource (config.json) via HTTP"
  set +e
  cfg_hdr=$(curl -sI "$BASE_URL/config.json" -m 5)
  set -e
  if echo "$cfg_hdr" | grep -i '^HTTP/' >/dev/null; then
    status=$(echo "$cfg_hdr" | head -n1)
    ok "config.json reachable: $status"
  else
    fail "config.json not reachable at $BASE_URL/config.json"
  fi
fi

echo "\nSummary: OK=$OK ERR=$ERR"
if [ "$ERR" -gt 0 ]; then
  echo "Some checks failed. See messages above for remediation hints (e.g., run permissions.sh)."
  exit 2
fi

exit 0
