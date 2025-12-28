#!/bin/bash
###############################################################################
# 314Sign Remote Setup for FullPageOS
###############################################################################

echo "=== 314Sign Remote Setup ==="

# Detect FullPageOS
if [ ! -f "/boot/firmware/fullpageos.txt" ]; then
  echo "ERROR: FullPageOS not detected!"
  exit 1
fi

echo "✓ FullPageOS detected"

# Generate device ID
CPU_SERIAL=$(grep "Serial" /proc/cpuinfo | awk '{print $3}' | tr '[:lower:]' '[:upper:]')
DEVICE_CODE=$(echo "$CPU_SERIAL" | md5sum | cut -c1-6 | tr '[:lower:]' '[:upper:]')
echo "Device Code: $DEVICE_CODE"

# Set hostname
sudo hostnamectl set-hostname "remote-$DEVICE_CODE" 2>/dev/null || sudo hostname "remote-$DEVICE_CODE"

# Install git only (skip web server for now)
echo "Installing git..."
sudo apt update && sudo apt install -y git

# Clone and copy files
TEMP_DIR=$(mktemp -d)
git clone --depth 1 --filter=tree:0 --sparse https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign" 2>/dev/null || git clone --depth 1 https://github.com/UnderhillForge/314Sign.git "$TEMP_DIR/314Sign"
cd "$TEMP_DIR/314Sign" && git sparse-checkout add remclient/ && cd - >/dev/null
sudo cp -r "$TEMP_DIR/314Sign/remclient/"* /var/www/html/

# Create device config
cat > /var/www/html/device.json <<EOF
{
  "serial": "$CPU_SERIAL",
  "code": "$DEVICE_CODE",
  "type": "remote",
  "setupDate": "$(date -Iseconds)",
  "version": "remote-1.0.0"
}
EOF

# Create remote config
cat > /var/www/html/remote-config.json <<EOF
{
  "registered": false,
  "mode": "unregistered",
  "lastUpdate": "$(date -Iseconds)",
  "displayName": "Remote $DEVICE_CODE"
}
EOF

# Set permissions
sudo chown -R www-data:www-data /var/www/html

# Copy remote.html to boot partition and configure browser URL
echo "Configuring FullPageOS browser..."
sudo cp /var/www/html/remote.html /boot/firmware/ 2>/dev/null || echo "Could not copy remote.html to boot partition"
echo "file:///boot/firmware/remote.html" | sudo tee /boot/firmware/fullpageos.txt > /dev/null

# Skip web server start for now

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Setup complete!"
echo "🆔 Device Code: $DEVICE_CODE"
echo "🌐 Access: http://remote-$DEVICE_CODE.local/remote/"
echo "📋 Register this code with your main kiosk"
echo ""

# task_progress List (Optional - Plan Mode)

#While in PLAN MODE, if you've outlined concrete steps or requirements for the user, you may include a preliminary todo list using the task_progress parameter.

#Reminder on how to use the task_progress parameter:


#1. To create or update a todo list, include the task_progress parameter in the next tool call
#2. Review each item and update its status:
#   - Mark completed items with: - [x]
#   - Keep incomplete items as: - [ ]
#   - Add new items if you discover additional steps
#3. Modify the list as needed:
#		- Add any new steps you've discovered
#	 - Reorder if the sequence has changed
#4. Ensure the list accurately reflects the current state

#**Remember:** Keeping the task_progress list updated helps track progress and ensures nothing is missed.