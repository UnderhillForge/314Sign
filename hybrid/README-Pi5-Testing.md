# 314Sign Pi 5 Testing Guide

This guide covers everything needed to test the 314Sign system on Raspberry Pi 5, from initial setup to comprehensive validation.

## 📋 Pre-Testing Checklist

### Hardware Requirements
- ✅ **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- ✅ **Power Supply** (27W USB-C PD recommended)
- ✅ **MicroSD Card** (32GB+ Class 10 recommended)
- ✅ **Display** (HDMI monitor/TV, 1920x1080+ resolution)
- ✅ **Cooling** (Active cooling recommended for sustained use)
- ✅ **Network** (Ethernet or WiFi for remote access)

### Software Prerequisites
- ✅ **Raspberry Pi OS** (64-bit Bookworm recommended)
- ✅ **Python 3.11+** (included in Bookworm)
- ✅ **System updated** (`sudo apt update && sudo apt upgrade`)

## 🚀 Installation & Setup

### 1. Clone and Setup
```bash
# Clone repository
git clone https://github.com/UnderhillForge/314Sign.git
cd 314Sign/hybrid

# Run Pi 5 optimizations
sudo bash pi5_optimization.sh

# Run main kiosk setup
sudo bash setup_main_kiosk.sh
```

### 2. Generate Test Content
```bash
# Generate comprehensive test content
python3 test_content_generator.py --output /opt/314sign/test_content

# This creates:
# - 5 LMS test files (basic, restaurant, classroom, performance, dynamic)
# - 3 slideshow test files (text, image, mixed)
# - 1 test .314 package
```

### 3. Start Services
```bash
# Start the main kiosk service
sudo systemctl start 314sign-main-kiosk.service

# Start web server
sudo systemctl start nginx

# Check status
314sign-main-status
```

## 🧪 Testing Phases

### Phase 1: Basic Functionality

#### 1.1 Service Status Check
```bash
# Check all services are running
314sign-main-status

# Expected output:
# 314Sign Main Kiosk Status
# =========================
# Service status:
#   ● 314sign-main-kiosk.service - 314Sign Main Kiosk
#     Loaded: loaded (/etc/systemd/system/314sign-main-kiosk.service; enabled)
#     Active: active (running) since...
```

#### 1.2 Web Interface Test
```bash
# Access web interfaces
curl http://localhost/                    # Main interface
curl http://localhost/admin               # Admin panel
curl http://localhost/mobile              # Mobile view
curl http://localhost/api/stats           # API test
```

#### 1.3 Display Output Test
```bash
# Monitor display output
314sign-monitor

# Expected: Live performance stats, service status
```

### Phase 2: Content Display Testing

#### 2.1 LMS Content Testing
```bash
# Test each LMS file
sudo cp /opt/314sign/test_content/basic_text_test.lms /opt/314sign/lms/
sudo cp /opt/314sign/test_content/restaurant_menu_test.lms /opt/314sign/lms/
sudo cp /opt/314sign/test_content/classroom_schedule_test.lms /opt/314sign/lms/

# Update configuration to use test content
sudo nano /etc/314sign/main_kiosk.json
# Set "current_lms": "basic_text_test"
```

#### 2.2 Slideshow Testing
```bash
# Copy slideshow files
sudo cp /opt/314sign/test_content/*.json /opt/314sign/slideshows/

# Update config for slideshow testing
# Set "current_slideshow": "basic_slideshow"
```

#### 2.3 Package Testing
```bash
# Test .314 package functionality
python3 package_314sign.py info /opt/314sign/test_content/basic_text_test.314
python3 package_314sign.py validate /opt/314sign/test_content/basic_text_test.314
```

### Phase 3: Performance Testing

#### 3.1 Benchmarking
```bash
# Run comprehensive benchmark
314sign-benchmark

# Expected output includes:
# - CPU performance (sysbench results)
# - Memory usage
# - Storage I/O speed
# - Network performance
# - Graphics rendering FPS
```

#### 3.2 Thermal Testing
```bash
# Monitor temperature during load
314sign-thermal

# Run stress test
sudo apt install stress
stress --cpu 4 --timeout 300  # 5 minute CPU stress test

# Monitor temperature changes
watch -n 5 'vcgencmd measure_temp'
```

#### 3.3 Load Testing
```bash
# Test with performance LMS file (70+ elements)
sudo cp /opt/314sign/test_content/performance_test.lms /opt/314sign/lms/
# Update config to use performance_test

# Monitor FPS and memory usage
314sign-monitor
```

### Phase 4: Remote Display Testing

#### 4.1 Setup Remote Pi (Zero 2W)
```bash
# On remote Pi, run setup
cd 314Sign/hybrid
sudo bash setup_remote_kiosk.sh

# Configure to connect to main Pi 5
sudo nano /etc/314sign/config.json
# Set main_kiosk_url to Pi 5's IP address
```

#### 4.2 Content Distribution Testing
```bash
# Create test package on main Pi 5
python3 package_314sign.py create /opt/314sign/test_content/restaurant_menu_test.lms

# Package should be automatically distributed to remote displays
# Verify remote displays show the content
```

#### 4.3 Network Performance Testing
```bash
# Test network speed between devices
iperf3 -c <remote_ip>  # Install iperf3 if needed

# Test package download speed
time curl http://<main_ip>/api/packages/restaurant_menu_test.314 -o /dev/null
```

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Display shows black screen
```bash
# Check framebuffer device
ls -la /dev/fb*

# Check pygame initialization
python3 -c "import pygame; pygame.init(); print('OK')"

# Check display resolution
tvservice -s

# Restart kiosk service
sudo systemctl restart 314sign-main-kiosk.service
```

#### Issue: Web interface not accessible
```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx configuration
sudo nginx -t

# Check firewall
sudo ufw status

# Check if port 80 is in use
sudo netstat -tlnp | grep :80
```

#### Issue: High CPU usage
```bash
# Check what's using CPU
top -n 1

# Check for runaway processes
ps aux | grep python

# Restart service
sudo systemctl restart 314sign-main-kiosk.service
```

#### Issue: Memory issues
```bash
# Check memory usage
free -h

# Check for memory leaks
ps aux --sort=-%mem | head -10

# Clear caches
sudo systemctl restart 314sign-main-kiosk.service
```

#### Issue: Package loading fails
```bash
# Validate package
python3 package_314sign.py validate /path/to/package.314

# Check package contents
python3 package_314sign.py info /path/to/package.314

# Extract manually for debugging
python3 package_314sign.py extract /path/to/package.314 -d debug_extract
```

#### Issue: Remote display not connecting
```bash
# Check network connectivity
ping <main_kiosk_ip>

# Check remote config
cat /etc/314sign/config.json

# Check remote logs
sudo journalctl -u 314sign-display.service -n 50

# Test API connectivity
curl http://<main_ip>/api/remotes
```

### Performance Optimization

#### For Better FPS
```bash
# Reduce display resolution if needed
sudo nano /boot/firmware/config.txt
# Add: framebuffer_width=1280
# Add: framebuffer_height=720

# Disable anti-aliasing for performance
# Edit LMS files: "antialiasing": false
```

#### For Lower Power Consumption
```bash
# Reduce CPU frequency
sudo nano /etc/314sign/cpu-governor.conf
# Change MAX_FREQ to 1800000

# Increase polling intervals
sudo nano /etc/314sign/main_kiosk.json
# Increase config_poll_interval and content_poll_interval
```

## 📊 Expected Test Results

### Performance Benchmarks (Pi 5)
- **CPU**: Sysbench score > 1000 events/second
- **Memory**: < 50% usage during normal operation
- **Display**: 60 FPS with complex LMS content
- **Network**: > 50 Mbps transfer speeds
- **Temperature**: < 70°C under load

### Content Rendering Tests
- ✅ Basic text display (all fonts, colors, sizes)
- ✅ Dynamic content (time, date updates)
- ✅ Image rendering (scaling, positioning)
- ✅ Shape rendering (rectangles, opacity)
- ✅ Animation effects (fade, slide transitions)
- ✅ Performance test (70+ elements at 30+ FPS)

### Package System Tests
- ✅ Package creation (asset embedding)
- ✅ Package validation (integrity checks)
- ✅ Package extraction (content recovery)
- ✅ Package distribution (remote loading)

## 🎯 Success Criteria

### Minimum Viable Test (MVT)
- [ ] System boots successfully
- [ ] Web interface accessible
- [ ] Basic LMS content displays
- [ ] No crashes during 1-hour test run

### Full System Test (FST)
- [ ] All content types render correctly
- [ ] Performance meets benchmarks
- [ ] Remote displays work
- [ ] Package system functions
- [ ] No errors in logs
- [ ] Temperature stays within limits

### Production Ready (PR)
- [ ] 24/7 stable operation
- [ ] Automatic error recovery
- [ ] Performance monitoring
- [ ] Remote management
- [ ] Content distribution
- [ ] Security hardening

## 📞 Support & Debugging

### Log Files
```bash
# Main kiosk logs
sudo journalctl -u 314sign-main-kiosk.service -f

# Web server logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -p err --since today
```

### Diagnostic Commands
```bash
# Full system diagnostic
314sign-main-status

# Hardware information
cat /proc/cpuinfo | head -20
vcgencmd version
vcgencmd get_mem gpu

# Network diagnostic
ip route show
ip addr show
ping -c 4 8.8.8.8
```

### Emergency Recovery
```bash
# Stop all services
sudo systemctl stop 314sign-main-kiosk.service nginx

# Reset configuration
sudo cp /etc/314sign/main_kiosk.json.backup /etc/314sign/main_kiosk.json

# Clear caches
sudo rm -rf /var/cache/314sign/*
sudo rm -rf /tmp/314sign_cache

# Restart services
sudo systemctl start nginx
sudo systemctl start 314sign-main-kiosk.service
```

## 🎉 Post-Testing Checklist

- [ ] All tests pass (MVT, FST, PR)
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Backup configurations created
- [ ] Monitoring alerts configured
- [ ] Remote access secured
- [ ] Production deployment ready

---

**The 314Sign system is now ready for comprehensive Pi 5 testing!** 🚀

Use this guide to methodically validate every aspect of the system before production deployment.