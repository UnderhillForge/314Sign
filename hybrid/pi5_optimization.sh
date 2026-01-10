#!/bin/bash
# Raspberry Pi 5 Specific Optimizations for 314Sign
# Performance tuning and hardware-specific configurations

set -e

echo "314Sign Pi 5 Optimization Script"
echo "================================="

# Check if running on Pi 5
if ! grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    echo "Error: This script is designed for Raspberry Pi 5 only"
    echo "Current device: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
    exit 1
fi

echo "✓ Detected Raspberry Pi 5"

# Ensure 314sign configuration directory exists
echo "Creating 314sign configuration directory..."
sudo mkdir -p /etc/314sign

# Pi 5 specific kernel parameters for better performance
echo "Configuring Pi 5 kernel parameters..."
sudo tee -a /boot/firmware/cmdline.txt > /dev/null << 'EOF'
usbhid.mousepoll=0 usbhid.kbpoll=0 usbhid.jspoll=0
dwc_otg.speed=1
EOF

# Pi 5 specific boot configuration
echo "Optimizing Pi 5 boot configuration..."
sudo tee -a /boot/firmware/config.txt > /dev/null << 'EOF'

# Pi 5 Specific Optimizations for 314Sign
# ========================================

# GPU Memory - Maximum for high-quality rendering
gpu_mem=1024

# PCIe tuning for better I/O performance
dtparam=pciex1_gen=3

# USB tuning for reduced latency
usb_max_current_enable=1
usb_ssphy_quirk_enable=1

# CPU governor settings
force_turbo=0
arm_boost=1

# Disable unused peripherals for power savings
dtparam=audio=off
dtparam=i2c_arm=off
dtparam=spi=off
camera_auto_detect=0

# Network optimizations
dtparam=eth_led0=4
dtparam=eth_led1=4

# Temperature and power management
temp_limit=75
temp_soft_limit=70
EOF

# CPU performance tuning
echo "Configuring CPU performance tuning..."
cat > /tmp/314sign-cpu-governor.conf << 'EOF'
# CPU governor configuration for 314Sign
GOVERNOR="performance"
MIN_FREQ="1500000"
MAX_FREQ="2400000"
EOF

sudo mv /tmp/314sign-cpu-governor.conf /etc/314sign/cpu-governor.conf

# Create systemd service for CPU tuning
cat > /tmp/314sign-cpu-tune.service << 'EOF'
[Unit]
Description=314Sign CPU Performance Tuning
After=sysinit.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c '\
    echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; \
    echo performance > /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor; \
    echo performance > /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor; \
    echo performance > /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor; \
    echo 2400000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq; \
    echo 2400000 > /sys/devices/system/cpu/cpu1/cpufreq/scaling_max_freq; \
    echo 2400000 > /sys/devices/system/cpu/cpu2/cpufreq/scaling_max_freq; \
    echo 2400000 > /sys/devices/system/cpu/cpu3/cpufreq/scaling_max_freq; \
'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/314sign-cpu-tune.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 314sign-cpu-tune.service

# Memory optimization for Pi 5
echo "Configuring memory management..."
sudo tee -a /etc/sysctl.d/99-314sign-memory.conf > /dev/null << 'EOF'
# Memory optimization for 314Sign on Pi 5
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio=10
vm.dirty_background_ratio=5
vm.dirty_expire_centisecs=3000
vm.dirty_writeback_centisecs=1500

# Network buffer tuning
net.core.rmem_max=262144
net.core.wmem_max=262144
net.ipv4.tcp_rmem=4096 87380 262144
net.ipv4.tcp_wmem=4096 16384 262144
EOF

# I/O scheduling optimization
echo "Configuring I/O scheduling..."
sudo tee -a /etc/udev/rules.d/99-314sign-io.rules > /dev/null << 'EOF'
# I/O scheduling rules for 314Sign
ACTION=="add|change", KERNEL=="sd*", ATTR{queue/scheduler}="deadline"
ACTION=="add|change", KERNEL=="nvme*", ATTR{queue/scheduler}="none"
EOF

# Install performance monitoring tools
echo "Installing performance monitoring tools..."
sudo apt install -y htop iotop sysstat nmon

# Create performance monitoring script
cat > /tmp/314sign-monitor.sh << 'EOF'
#!/bin/bash
# 314Sign Performance Monitor for Pi 5

echo "314Sign Pi 5 Performance Monitor"
echo "================================="

while true; do
    clear
    echo "314Sign Pi 5 Performance Monitor - $(date)"
    echo "============================================"

    echo "CPU Information:"
    echo "  Temperature: $(vcgencmd measure_temp | cut -d= -f2)"
    echo "  Clock: $(vcgencmd measure_clock arm | awk -F= '{printf "%.0f MHz\n", $2/1000000}')"
    echo "  Voltage: $(vcgencmd measure_volts core | cut -d= -f2)"
    echo "  Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
    echo "  Frequency: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq) Hz"
    echo

    echo "Memory Usage:"
    free -h
    echo

    echo "Disk I/O:"
    iostat -x 1 1 | tail -n 5
    echo

    echo "Network:"
    ip -s link show wlan0 2>/dev/null || ip -s link show eth0 2>/dev/null || echo "No network interface found"
    echo

    echo "314Sign Services:"
    systemctl is-active 314sign-main-kiosk.service 2>/dev/null && echo "  Main Kiosk: ✓ Active" || echo "  Main Kiosk: ✗ Inactive"
    systemctl is-active nginx 2>/dev/null && echo "  Web Server: ✓ Active" || echo "  Web Server: ✗ Inactive"
    echo

    echo "Top Processes:"
    ps aux --sort=-%cpu | head -n 10
    echo

    echo "Press Ctrl+C to exit..."
    sleep 5
done
EOF

sudo mv /tmp/314sign-monitor.sh /usr/local/bin/314sign-monitor
sudo chmod +x /usr/local/bin/314sign-monitor

# Create benchmark script for Pi 5
cat > /tmp/314sign-benchmark.sh << 'EOF'
#!/bin/bash
# 314Sign Pi 5 Benchmark Script

echo "314Sign Pi 5 Benchmark"
echo "======================"

LOG_FILE="/var/log/314sign/benchmark_$(date +%Y%m%d_%H%M%S).log"

echo "Benchmark started at $(date)" | tee -a "$LOG_FILE"
echo "Pi Model: $(cat /proc/device-tree/model)" | tee -a "$LOG_FILE"
echo | tee -a "$LOG_FILE"

# CPU Benchmark
echo "CPU Benchmark (sysbench):" | tee -a "$LOG_FILE"
if command -v sysbench >/dev/null 2>&1; then
    sysbench cpu --cpu-max-prime=10000 run | grep -E "(total time|events per second)" | tee -a "$LOG_FILE"
else
    echo "sysbench not installed - CPU benchmark skipped" | tee -a "$LOG_FILE"
fi
echo | tee -a "$LOG_FILE"

# Memory Benchmark
echo "Memory Benchmark:" | tee -a "$LOG_FILE"
echo "  Total RAM: $(free -h | grep '^Mem:' | awk '{print $2}')" | tee -a "$LOG_FILE"
echo "  Available RAM: $(free -h | grep '^Mem:' | awk '{print $7}')" | tee -a "$LOG_FILE"
echo | tee -a "$LOG_FILE"

# Storage Benchmark
echo "Storage Benchmark (dd test):" | tee -a "$LOG_FILE"
echo "  Write speed:" | tee -a "$LOG_FILE"
dd if=/dev/zero of=/tmp/testfile bs=1M count=100 conv=fdatasync 2>&1 | grep -v records | tee -a "$LOG_FILE"
rm -f /tmp/testfile
echo | tee -a "$LOG_FILE"

# Network Benchmark (if connected)
echo "Network Benchmark:" | tee -a "$LOG_FILE"
ping -c 4 8.8.8.8 2>/dev/null | tail -n 3 | tee -a "$LOG_FILE"
echo | tee -a "$LOG_FILE"

# GPU Information
echo "GPU Information:" | tee -a "$LOG_FILE"
vcgencmd version 2>/dev/null | head -n 1 | tee -a "$LOG_FILE"
echo "  GPU Memory: $(vcgencmd get_mem gpu)" | tee -a "$LOG_FILE"
echo | tee -a "$LOG_FILE"

# SDL/Pygame Test
echo "Graphics Performance Test:" | tee -a "$LOG_FILE"
python3 -c "
import pygame
import time

print('Testing Pygame initialization...')
try:
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    print('✓ Fullscreen display initialized')

    # Simple render test
    start_time = time.time()
    for i in range(100):
        screen.fill((255, 0, 0))
        pygame.display.flip()
    end_time = time.time()

    fps = 100 / (end_time - start_time)
    print(f'✓ Render performance: {fps:.1f} FPS')

    pygame.quit()
    print('✓ Pygame test completed successfully')

except Exception as e:
    print(f'✗ Pygame test failed: {e}')
" 2>&1 | tee -a "$LOG_FILE"

echo | tee -a "$LOG_FILE"
echo "Benchmark completed at $(date)" | tee -a "$LOG_FILE"
echo "Results saved to: $LOG_FILE"
EOF

sudo mv /tmp/314sign-benchmark.sh /usr/local/bin/314sign-benchmark
sudo chmod +x /usr/local/bin/314sign-benchmark

# Thermal management script
cat > /tmp/314sign-thermal.sh << 'EOF'
#!/bin/bash
# 314Sign Thermal Management for Pi 5

echo "314Sign Pi 5 Thermal Management"
echo "==============================="

# Get current temperature
CURRENT_TEMP=$(vcgencmd measure_temp | sed 's/temp=//' | sed 's/'\''C//')
TEMP_NUM=$(echo $CURRENT_TEMP | cut -d. -f1)

echo "Current CPU temperature: $CURRENT_TEMP"

if [ $TEMP_NUM -gt 80 ]; then
    echo "⚠️  HIGH TEMPERATURE - Throttling active"
    echo "Consider improving cooling or reducing performance"
elif [ $TEMP_NUM -gt 70 ]; then
    echo "⚠️  Warm - Monitor temperature"
elif [ $TEMP_NUM -gt 60 ]; then
    echo "✓ Normal operating temperature"
else
    echo "✓ Cool - Good for performance"
fi

echo
echo "Thermal throttling status:"
vcgencmd get_throttled | sed 's/0x0/No throttling/' | sed 's/0x1/Under-voltage detected/' | sed 's/0x2/Arm frequency capped/' | sed 's/0x4/Currently throttled/' | sed 's/0x8/Soft temperature limit active/'

echo
echo "Fan status (if applicable):"
# Check for common fan control methods
if [ -f /sys/class/thermal/cooling_device0/cur_state ]; then
    echo "Fan state: $(cat /sys/class/thermal/cooling_device0/cur_state)"
fi
EOF

sudo mv /tmp/314sign-thermal.sh /usr/local/bin/314sign-thermal
sudo chmod +x /usr/local/bin/314sign-thermal

# Pi 5 specific power management
echo "Configuring power management..."
cat > /tmp/314sign-power.service << 'EOF'
[Unit]
Description=314Sign Power Management
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c '\
    # Disable USB autosuspend for better responsiveness \
    echo -1 > /sys/module/usbcore/parameters/autosuspend; \
    # Set CPU scaling governor \
    for cpu in /sys/devices/system/cpu/cpu[0-3]; do \
        echo performance > $cpu/cpufreq/scaling_governor; \
    done; \
'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/314sign-power.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 314sign-power.service

# Update package manager for better performance
echo "Optimizing package management..."
sudo tee -a /etc/apt/apt.conf.d/99-314sign-apt > /dev/null << 'EOF'
# Apt optimizations for 314Sign
Acquire::http::Pipeline-Depth "200";
Acquire::https::Pipeline-Depth "200";
Acquire::http::Timeout "30";
Acquire::https::Timeout "30";
EOF

# Setup complete
echo
echo "Pi 5 Optimization Complete!"
echo "==========================="
echo
echo "Optimizations applied:"
echo "  • CPU performance tuning (2.4GHz max)"
echo "  • GPU memory set to 1024MB"
echo "  • PCIe Gen 3 enabled"
echo "  • USB optimizations for low latency"
echo "  • Memory management tuning"
echo "  • I/O scheduling optimization"
echo "  • Network buffer tuning"
echo "  • Thermal management setup"
echo
echo "New monitoring commands:"
echo "  314sign-monitor     - Real-time performance monitoring"
echo "  314sign-benchmark   - System performance benchmark"
echo "  314sign-thermal     - Temperature and thermal status"
echo
echo "The system is optimized for 314Sign performance!"
echo
echo "Note: These optimizations are tuned for digital signage workloads."
echo "Monitor temperatures and adjust cooling as needed for your setup."