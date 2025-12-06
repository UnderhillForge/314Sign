#!/bin/bash
# Increment the build number in version.txt
# Usage: ./increment-version.sh [major.minor.patch]
# Examples:
#   ./increment-version.sh           # Increments build: 0.9.2.5 -> 0.9.2.6
#   ./increment-version.sh 0.9.3     # New version: 0.9.3.1
#   ./increment-version.sh 1.0.0     # Major bump: 1.0.0.1

set -e

# Path to version.txt (relative to repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$REPO_ROOT/version.txt"

if [[ ! -f "$VERSION_FILE" ]]; then
    echo "Error: version.txt not found at $VERSION_FILE"
    exit 1
fi

# Read current version
CURRENT=$(cat "$VERSION_FILE")

if [[ $# -eq 1 ]]; then
    # New version specified (e.g., 0.9.3 or 1.0.0)
    NEW_VERSION="$1"
    
    # Validate format (x.x.x)
    if [[ ! "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Version must be in format x.x.x (e.g., 0.9.3)"
        exit 1
    fi
    
    # Reset build number to 1
    NEW_FULL="$NEW_VERSION.1"
    echo "Version bump: $CURRENT -> $NEW_FULL"
    
else
    # Increment build number
    if [[ ! "$CURRENT" =~ ^([0-9]+\.[0-9]+\.[0-9]+)\.([0-9]+)$ ]]; then
        echo "Error: Invalid version format in version.txt: $CURRENT"
        echo "Expected format: x.x.x.xx (e.g., 0.9.2.1)"
        exit 1
    fi
    
    VERSION_BASE="${BASH_REMATCH[1]}"
    BUILD_NUM="${BASH_REMATCH[2]}"
    NEW_BUILD=$((BUILD_NUM + 1))
    NEW_FULL="$VERSION_BASE.$NEW_BUILD"
    
    echo "Build increment: $CURRENT -> $NEW_FULL"
fi

# Write new version
echo "$NEW_FULL" > "$VERSION_FILE"
echo "Updated version.txt to $NEW_FULL"

# Optional: Auto-commit
if [[ "$AUTO_COMMIT" == "true" ]]; then
    cd "$REPO_ROOT"
    git add version.txt
    git commit -m "Bump version to $NEW_FULL" --no-verify
    echo "Committed version bump"
fi
