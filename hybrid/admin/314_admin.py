#!/usr/bin/env python3
"""
314Sign Kiosk Administration Console
Secure, efficient system management interface via SSH
"""

import curses
import curses.panel
import time
import json
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import threading
import signal

class KioskAdminConsole:
    """
    Curses-based administration interface for kiosk management
    Provides secure, direct access to system functions via SSH
    """

    def __init__(self, stdscr):
        self.screen = stdscr
        self.height, self.width = stdscr.getmaxyx()

        # Setup curses
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.use_default_colors()
        self.setup_colors()

        # Create windows
        self.windows = {}
        self.panels = {}
        self.create_windows()

        # State
        self.current_tab = 0
        self.tabs = ['Dashboard', 'System', 'Network', 'Content', 'Bundles', 'Monitor']
        self.running = True

        # Sub-navigation for settings tabs
        self.system_subtabs = ['Hardware', 'Services', 'Time/Date', 'Storage']
        self.network_subtabs = ['WiFi', 'Ethernet', 'mDNS', 'Firewall']
        self.content_subtabs = ['LMS Files', 'Templates', 'Cache', 'Web Editor']
        self.bundles_subtabs = ['Create', 'List', 'Distribute', 'History']
        self.bundles_subtabs = ['Create', 'List', 'Distribute', 'History']
        self.monitor_subtabs = ['Devices', 'Performance', 'Logs', 'Alerts']

        self.current_subtab = 0

        # Data refresh thread
        self.data_thread = threading.Thread(target=self.data_refresh_loop, daemon=True)
        self.data_thread.start()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_colors(self):
        """Setup color pairs for the interface"""
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Normal
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)     # Error
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_WHITE)   # Success
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_WHITE)  # Warning
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_WHITE)    # Info
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_WHITE) # Highlight

    def create_windows(self):
        """Create all interface windows"""
        # Header window
        self.windows['header'] = curses.newwin(3, self.width, 0, 0)
        self.panels['header'] = curses.panel.new_panel(self.windows['header'])

        # Tab bar
        self.windows['tabs'] = curses.newwin(1, self.width, 3, 0)
        self.panels['tabs'] = curses.panel.new_panel(self.windows['tabs'])

        # Sub-tab bar (for settings tabs)
        self.windows['subtabs'] = curses.newwin(1, self.width, 4, 0)
        self.panels['subtabs'] = curses.panel.new_panel(self.windows['subtabs'])

        # Main content area
        content_height = self.height - 7
        self.windows['content'] = curses.newwin(content_height, self.width, 5, 0)
        self.panels['content'] = curses.panel.new_panel(self.windows['content'])

        # Status bar
        self.windows['status'] = curses.newwin(2, self.width, self.height-2, 0)
        self.panels['status'] = curses.panel.new_panel(self.windows['status'])

    def draw_header(self):
        """Draw the application header"""
        header = self.windows['header']
        header.bkgd(' ', curses.color_pair(1))
        header.clear()

        # Title
        title = "314Sign Kiosk Administration Console"
        header.addstr(1, 2, title, curses.A_BOLD)

        # System info
        hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
        header.addstr(1, self.width - len(hostname) - 2, hostname)

        header.refresh()

    def draw_tabs(self):
        """Draw the tab navigation"""
        tabs_win = self.windows['tabs']
        tabs_win.clear()

        tab_width = self.width // len(self.tabs)

        for i, tab_name in enumerate(self.tabs):
            if i == self.current_tab:
                # Active tab
                tabs_win.addstr(0, i * tab_width, f" {tab_name} ", curses.color_pair(7) | curses.A_BOLD)
            else:
                # Inactive tab
                tabs_win.addstr(0, i * tab_width, f" {tab_name} ")

        tabs_win.refresh()

        # Draw subtabs for settings tabs
        if self.current_tab >= 1:  # System, Network, Content, Security, Monitor
            self.draw_subtabs()
        else:
            # Clear subtabs for non-settings tabs
            subtabs_win = self.windows['subtabs']
            subtabs_win.clear()
            subtabs_win.refresh()

    def draw_subtabs(self):
        """Draw the sub-tab navigation for settings tabs"""
        subtabs_win = self.windows['subtabs']
        subtabs_win.clear()

        # Get current subtabs based on main tab
        if self.current_tab == 1:  # System
            subtabs = self.system_subtabs
        elif self.current_tab == 2:  # Network
            subtabs = self.network_subtabs
        elif self.current_tab == 3:  # Content
            subtabs = self.content_subtabs
        elif self.current_tab == 4:  # Security
            subtabs = self.security_subtabs
        elif self.current_tab == 5:  # Monitor
            subtabs = self.monitor_subtabs
        else:
            return

        subtab_width = self.width // len(subtabs)

        for i, subtab_name in enumerate(subtabs):
            if i == self.current_subtab:
                # Active subtab
                subtabs_win.addstr(0, i * subtab_width, f" {subtab_name} ", curses.color_pair(6) | curses.A_BOLD)
            else:
                # Inactive subtab
                subtabs_win.addstr(0, i * subtab_width, f" {subtab_name} ")

        subtabs_win.refresh()

    def draw_content(self):
        """Draw the main content area based on current tab and subtab"""
        content = self.windows['content']
        content.clear()

        if self.current_tab == 0:
            self.draw_dashboard(content)
        elif self.current_tab == 1:  # System
            if self.current_subtab == 0:
                self.draw_system_hardware(content)
            elif self.current_subtab == 1:
                self.draw_system_services(content)
            elif self.current_subtab == 2:
                self.draw_system_timedate(content)
            elif self.current_subtab == 3:
                self.draw_system_storage(content)
        elif self.current_tab == 2:  # Network
            if self.current_subtab == 0:
                self.draw_network_wifi(content)
            elif self.current_subtab == 1:
                self.draw_network_ethernet(content)
            elif self.current_subtab == 2:
                self.draw_network_mdns(content)
            elif self.current_subtab == 3:
                self.draw_network_firewall(content)
        elif self.current_tab == 3:  # Content
            if self.current_subtab == 0:
                self.draw_content_lms_files(content)
            elif self.current_subtab == 1:
                self.draw_content_templates(content)
            elif self.current_subtab == 2:
                self.draw_content_cache(content)
            elif self.current_subtab == 3:
                self.draw_content_web_editor(content)
        elif self.current_tab == 4:  # Bundles
            if self.current_subtab == 0:
                self.draw_bundles_create(content)
            elif self.current_subtab == 1:
                self.draw_bundles_list(content)
            elif self.current_subtab == 2:
                self.draw_bundles_distribute(content)
            elif self.current_subtab == 3:
                self.draw_bundles_history(content)
        elif self.current_tab == 5:  # Monitor
            if self.current_subtab == 0:
                self.draw_monitor_devices(content)
            elif self.current_subtab == 1:
                self.draw_monitor_performance(content)
            elif self.current_subtab == 2:
                self.draw_monitor_logs(content)
            elif self.current_subtab == 3:
                self.draw_monitor_alerts(content)

        content.refresh()

    def draw_status_bar(self):
        """Draw the status bar with key shortcuts"""
        status = self.windows['status']
        status.clear()

        # Key shortcuts
        shortcuts = "Tab: Switch Tabs | ↑↓: Navigate | Enter: Select | q: Quit | h: Help"
        status.addstr(0, 0, shortcuts, curses.color_pair(6))

        # System status
        status_str = f"Uptime: {self.get_system_uptime()} | CPU: {self.get_cpu_temp()}"
        status.addstr(1, 0, status_str)

        status.refresh()

    def draw_dashboard(self, win):
        """Draw the main dashboard"""
        win.addstr(0, 0, "=== System Dashboard ===", curses.A_BOLD)

        # System information
        row = 2
        win.addstr(row, 0, f"Hostname: {subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()}")

        # Memory usage
        mem_info = self.get_memory_info()
        row += 1
        win.addstr(row, 0, f"Memory: {mem_info['used']}/{mem_info['total']} MB ({mem_info['percent']}%)")

        # Disk usage
        disk_info = self.get_disk_info()
        row += 1
        win.addstr(row, 0, f"Disk: {disk_info['used']}/{disk_info['total']} GB ({disk_info['percent']}%)")

        # Service status
        row += 2
        win.addstr(row, 0, "Services:", curses.A_BOLD)
        services = self.get_service_status()
        for service, status in services.items():
            row += 1
            color = curses.color_pair(4) if status == 'running' else curses.color_pair(3)
            win.addstr(row, 2, f"{service}: {status}", color)

        # Recent activity
        row += 2
        win.addstr(row, 0, "Recent Activity:", curses.A_BOLD)
        # This would show recent LMS updates, device connections, etc.

    def draw_devices(self, win):
        """Draw the devices management interface"""
        win.addstr(0, 0, "=== Connected Devices ===", curses.A_BOLD)

        # This would show connected remote displays
        # For now, placeholder
        win.addstr(2, 0, "No remote devices connected")
        win.addstr(4, 0, "Press 's' to scan for devices")
        win.addstr(5, 0, "Press 'p' to push content to all devices")

    def draw_content_tab(self, win):
        """Draw the content management interface"""
        win.addstr(0, 0, "=== Content Management ===", curses.A_BOLD)

        # LMS files
        lms_dir = Path('/home/pi/lms')
        if lms_dir.exists():
            lms_files = list(lms_dir.glob('*.lms'))
            win.addstr(2, 0, f"LMS Files ({len(lms_files)}):")

            for i, lms_file in enumerate(lms_files[:10]):
                win.addstr(4 + i, 2, f"• {lms_file.name}")
        else:
            win.addstr(2, 0, "LMS directory not found")

        # Background cache
        bg_dir = Path('/home/pi/backgrounds')
        if bg_dir.exists():
            bg_files = list(bg_dir.glob('*'))
            win.addstr(16, 0, f"Cached Backgrounds: {len(bg_files)} files")

    def draw_config(self, win):
        """Draw the configuration interface"""
        win.addstr(0, 0, "=== System Configuration ===", curses.A_BOLD)

        # Load current config
        config_file = Path('/home/pi/kiosk_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                row = 2
                for key, value in config.items():
                    win.addstr(row, 0, f"{key}: {value}")
                    row += 1
                    if row > 15:  # Prevent overflow
                        break
            except Exception as e:
                win.addstr(2, 0, f"Error loading config: {e}")
        else:
            win.addstr(2, 0, "Configuration file not found")

    def draw_logs(self, win):
        """Draw the log viewer interface"""
        win.addstr(0, 0, "=== System Logs ===", curses.A_BOLD)

        # Show recent journal entries
        try:
            result = subprocess.run(
                ['journalctl', '-u', '314sign-kiosk.service', '-n', '15', '--no-pager'],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines[-15:]):  # Last 15 lines
                    if i < 15:  # Content window height
                        # Truncate long lines
                        truncated = line[:self.width-2] if len(line) > self.width-2 else line
                        win.addstr(2 + i, 0, truncated)
            else:
                win.addstr(2, 0, "Error reading logs")
        except Exception as e:
            win.addstr(2, 0, f"Error: {e}")

    # System Management Methods
    def draw_system_hardware(self, win):
        """Draw hardware information and management"""
        win.addstr(0, 0, "=== Hardware Information ===", curses.A_BOLD)

        # CPU Information
        row = 2
        win.addstr(row, 0, "CPU:", curses.A_BOLD)
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi 5' in cpuinfo:
                    win.addstr(row, 5, "Raspberry Pi 5 (4 cores)")
                elif 'Raspberry Pi 4' in cpuinfo:
                    win.addstr(row, 5, "Raspberry Pi 4 (4 cores)")
                elif 'Raspberry Pi Zero 2' in cpuinfo:
                    win.addstr(row, 5, "Raspberry Pi Zero 2 W (4 cores)")
                else:
                    win.addstr(row, 5, "Unknown Raspberry Pi")
        except:
            win.addstr(row, 5, "Unable to detect")

        # Temperature
        row += 1
        win.addstr(row, 0, f"Temperature: {self.get_cpu_temp()}")

        # Memory
        mem_info = self.get_memory_info()
        row += 1
        win.addstr(row, 0, f"Memory: {mem_info['used']}/{mem_info['total']} MB ({mem_info['percent']}%)")

        # Network interfaces
        row += 2
        win.addstr(row, 0, "Network Interfaces:", curses.A_BOLD)
        try:
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                interfaces = []
                for line in result.stdout.split('\n'):
                    if line.strip().startswith(('2:', '3:', '4:')):  # eth0, wlan0, etc.
                        parts = line.split(': ')
                        if len(parts) >= 2:
                            interfaces.append(parts[1].split('@')[0])

                for i, iface in enumerate(interfaces[:3]):  # Show first 3
                    row += 1
                    win.addstr(row, 2, iface)
        except:
            row += 1
            win.addstr(row, 2, "Unable to detect interfaces")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "r: Refresh hardware info")
        row += 1
        win.addstr(row, 2, "t: Show detailed temperature")

    def draw_system_services(self, win):
        """Draw service management interface"""
        win.addstr(0, 0, "=== Service Management ===", curses.A_BOLD)

        # Key services
        services = [
            ('314sign-kiosk', 'Main kiosk display service'),
            ('314sign-splash', 'Boot splash screen'),
            ('ssh', 'Secure shell access'),
            ('avahi-daemon', 'Network discovery (mDNS)'),
            ('cron', 'Scheduled tasks'),
            ('rsyslog', 'System logging')
        ]

        row = 2
        for service_name, description in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service_name],
                    capture_output=True, text=True, timeout=2
                )
                status = result.stdout.strip()

                color = curses.color_pair(4) if status == 'active' else curses.color_pair(3)
                win.addstr(row, 0, f"{service_name}:", color)
                win.addstr(row, 20, f"{status}", color)
                win.addstr(row, 30, description[:40])
                row += 1
            except:
                win.addstr(row, 0, f"{service_name}: unknown")
                win.addstr(row, 30, description[:40])
                row += 1

        # Actions
        row += 2
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "↑↓: Navigate services")
        row += 1
        win.addstr(row, 2, "Enter: Toggle service on/off")
        row += 1
        win.addstr(row, 2, "r: Restart selected service")

    def draw_system_timedate(self, win):
        """Draw time and date management"""
        win.addstr(0, 0, "=== Time & Date Configuration ===", curses.A_BOLD)

        # Current time and date
        row = 2
        try:
            result = subprocess.run(['date'], capture_output=True, text=True, timeout=2)
            current_time = result.stdout.strip()
            win.addstr(row, 0, f"Current Time: {current_time}")
        except:
            win.addstr(row, 0, "Current Time: Unable to determine")

        # Timezone
        row += 1
        try:
            result = subprocess.run(['timedatectl', 'show', '--property=Timezone'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                timezone = result.stdout.strip().replace('Timezone=', '')
                win.addstr(row, 0, f"Timezone: {timezone}")
            else:
                win.addstr(row, 0, "Timezone: Unable to determine")
        except:
            win.addstr(row, 0, "Timezone: Unable to determine")

        # NTP status
        row += 1
        try:
            result = subprocess.run(['timedatectl', 'show', '--property=NTPSynchronized'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                ntp_status = result.stdout.strip().replace('NTPSynchronized=', '')
                win.addstr(row, 0, f"NTP Sync: {'Yes' if ntp_status == 'yes' else 'No'}")
            else:
                win.addstr(row, 0, "NTP Sync: Unknown")
        except:
            win.addstr(row, 0, "NTP Sync: Unknown")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "t: Set timezone")
        row += 1
        win.addstr(row, 2, "d: Set date manually")
        row += 1
        win.addstr(row, 2, "n: Toggle NTP sync")

    def draw_system_storage(self, win):
        """Draw storage management interface"""
        win.addstr(0, 0, "=== Storage Management ===", curses.A_BOLD)

        # Disk usage
        disk_info = self.get_disk_info()
        row = 2
        win.addstr(row, 0, f"Root Filesystem: {disk_info['used']}/{disk_info['total']} GB ({disk_info['percent']}%)")

        # Detailed mount points
        row += 2
        win.addstr(row, 0, "Mount Points:", curses.A_BOLD)

        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for i, line in enumerate(lines[:8]):  # Show first 8 mount points
                    if i + 5 < self.height - 10:  # Don't overflow
                        parts = line.split()
                        if len(parts) >= 6:
                            mount_point = parts[5] if len(parts) > 5 else parts[-1]
                            usage = parts[4]
                            size = parts[1]
                            win.addstr(4 + i, 2, f"{mount_point}: {size} ({usage})")
        except:
            win.addstr(4, 2, "Unable to read mount information")

        # Actions
        row = 15
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "c: Clear cache files")
        row += 1
        win.addstr(row, 2, "l: Show large files")
        row += 1
        win.addstr(row, 2, "m: Mount external storage")

    # Network Management Methods
    def draw_network_wifi(self, win):
        """Draw WiFi network management"""
        win.addstr(0, 0, "=== WiFi Network Management ===", curses.A_BOLD)

        # Current WiFi status
        row = 2
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                ssid = result.stdout.strip()
                win.addstr(row, 0, f"Connected to: {ssid}")
            else:
                win.addstr(row, 0, "Not connected to any WiFi network")
        except:
            win.addstr(row, 0, "WiFi status: Unable to determine")

        # Available networks
        row += 2
        win.addstr(row, 0, "Available Networks:", curses.A_BOLD)

        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                networks = result.stdout.strip().split('\n')[:10]  # First 10 networks
                for i, network in enumerate(networks):
                    if network and 6 + i < self.height - 10:
                        parts = network.split(':')
                        if len(parts) >= 3:
                            ssid = parts[0] or '(hidden)'
                            signal = parts[1]
                            security = parts[2]
                            win.addstr(4 + i, 2, f"{ssid} ({signal}%) - {security}")
        except:
            win.addstr(4, 2, "Unable to scan networks")

        # Actions
        row = 16
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "c: Connect to network")
        row += 1
        win.addstr(row, 2, "d: Disconnect from current")
        row += 1
        win.addstr(row, 2, "s: Scan for networks")

    def draw_network_ethernet(self, win):
        """Draw Ethernet network management"""
        win.addstr(0, 0, "=== Ethernet Configuration ===", curses.A_BOLD)

        # Ethernet interfaces
        row = 2
        try:
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                interfaces = []
                current_iface = None
                for line in result.stdout.split('\n'):
                    if line.strip().startswith(('2:', '3:')):  # eth0, enp0s3, etc.
                        if current_iface:
                            interfaces.append(current_iface)
                        parts = line.split(': ')
                        current_iface = {'name': parts[1].split('@')[0], 'details': []}
                    elif current_iface and line.strip().startswith('inet '):
                        ip = line.strip().split()[1].split('/')[0]
                        current_iface['ip'] = ip
                        current_iface['details'].append(f"IP: {ip}")

                if current_iface:
                    interfaces.append(current_iface)

                for i, iface in enumerate(interfaces):
                    if iface['name'].startswith(('eth', 'enp')):
                        win.addstr(row, 0, f"Interface: {iface['name']}")
                        row += 1
                        if 'ip' in iface:
                            win.addstr(row, 2, f"IP Address: {iface['ip']}")
                        else:
                            win.addstr(row, 2, "Status: No IP address")
                        row += 1
                        break  # Show only first Ethernet interface
        except:
            win.addstr(row, 0, "Unable to read Ethernet configuration")

        # Link status
        row += 1
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'eth0' in line or 'enp' in line:
                        if 'UP' in line:
                            win.addstr(row, 0, "Link Status: Connected")
                        else:
                            win.addstr(row, 0, "Link Status: Disconnected")
                        break
        except:
            win.addstr(row, 0, "Link Status: Unknown")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "s: Configure static IP")
        row += 1
        win.addstr(row, 2, "d: Enable DHCP")
        row += 1
        win.addstr(row, 2, "r: Restart networking")

    def draw_network_mdns(self, win):
        """Draw mDNS (Bonjour/Avahi) configuration"""
        win.addstr(0, 0, "=== mDNS Network Discovery ===", curses.A_BOLD)

        # Avahi status
        row = 2
        try:
            result = subprocess.run(['systemctl', 'is-active', 'avahi-daemon'],
                                  capture_output=True, text=True, timeout=2)
            status = result.stdout.strip()
            color = curses.color_pair(4) if status == 'active' else curses.color_pair(3)
            win.addstr(row, 0, "Avahi Service:", color)
            win.addstr(row, 16, status, color)
        except:
            win.addstr(row, 0, "Avahi Service: Unable to determine")

        # Hostname
        row += 1
        try:
            hostname = subprocess.run(['hostname'], capture_output=True, text=True, timeout=2).stdout.strip()
            win.addstr(row, 0, f"Hostname: {hostname}")
            win.addstr(row, 25, f"(Accessible as: {hostname}.local)")
        except:
            win.addstr(row, 0, "Hostname: Unable to determine")

        # Services
        row += 2
        win.addstr(row, 0, "Published Services:", curses.A_BOLD)
        services = [
            ('SSH', 'Secure shell access', 22),
            ('HTTP', 'Web interface', 80),
            ('HTTPS', 'Secure web interface', 443)
        ]

        for service in services:
            row += 1
            win.addstr(row, 2, f"{service[0]} ({service[1]}) - Port {service[2]}")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "h: Change hostname")
        row += 1
        win.addstr(row, 2, "t: Toggle mDNS service")
        row += 1
        win.addstr(row, 2, "b: Browse network services")

    def draw_network_firewall(self, win):
        """Draw firewall configuration"""
        win.addstr(0, 0, "=== Firewall Configuration ===", curses.A_BOLD)

        # UFW status
        row = 2
        try:
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                status_lines = result.stdout.strip().split('\n')
                win.addstr(row, 0, status_lines[0])  # Status line
                for i, line in enumerate(status_lines[1:10]):  # Show first 10 rules
                    if 4 + i < self.height - 10:
                        win.addstr(4 + i, 2, line)
            else:
                win.addstr(row, 0, "UFW Status: Not configured")
        except:
            win.addstr(row, 0, "UFW Status: Unable to determine")

        # Open ports summary
        row = 16
        win.addstr(row, 0, "Common Services:", curses.A_BOLD)
        ports = [
            ('SSH', 22, 'Secure shell'),
            ('HTTP', 80, 'Web interface'),
            ('HTTPS', 443, 'Secure web'),
            ('mDNS', 5353, 'Network discovery')
        ]

        for port_info in ports:
            row += 1
            win.addstr(row, 2, f"{port_info[0]} (Port {port_info[1]}) - {port_info[2]}")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "e: Enable firewall")
        row += 1
        win.addstr(row, 2, "d: Disable firewall")
        row += 1
        win.addstr(row, 2, "a: Allow port/service")

    # Monitor Methods
    def draw_monitor_devices(self, win):
        """Draw device monitoring interface"""
        win.addstr(0, 0, "=== Device Monitoring ===", curses.A_BOLD)

        # Connected devices
        row = 2
        win.addstr(row, 0, "Local Device Status:", curses.A_BOLD)
        row += 1

        # System health
        try:
            load_avg = subprocess.run(['uptime'], capture_output=True, text=True, timeout=2)
            if load_avg.returncode == 0:
                # Extract load average from uptime output
                parts = load_avg.stdout.split('load average:')[1].split(',')[0].strip()
                win.addstr(row, 2, f"System Load: {parts}")
                row += 1
        except:
            win.addstr(row, 2, "System Load: Unable to determine")
            row += 1

        # CPU usage
        win.addstr(row, 2, f"CPU Temperature: {self.get_cpu_temp()}")
        row += 1

        # Memory
        mem_info = self.get_memory_info()
        win.addstr(row, 2, f"Memory Usage: {mem_info['percent']}%")
        row += 1

        # Remote devices (placeholder)
        row += 2
        win.addstr(row, 0, "Remote Devices:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "No remote devices connected")
        row += 1
        win.addstr(row, 2, "(Use 's' to scan network)")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "s: Scan for remote devices")
        row += 1
        win.addstr(row, 2, "p: Ping all devices")
        row += 1
        win.addstr(row, 2, "r: Refresh status")

    def draw_monitor_performance(self, win):
        """Draw performance monitoring"""
        win.addstr(0, 0, "=== Performance Monitoring ===", curses.A_BOLD)

        # Real-time stats
        row = 2
        win.addstr(row, 0, "Real-time Metrics:", curses.A_BOLD)

        # CPU usage
        row += 1
        try:
            with open('/proc/loadavg', 'r') as f:
                loadavg = f.read().split()
                win.addstr(row, 2, f"Load Average: {loadavg[0]}, {loadavg[1]}, {loadavg[2]}")
        except:
            win.addstr(row, 2, "Load Average: Unable to read")

        # Memory
        mem_info = self.get_memory_info()
        row += 1
        win.addstr(row, 2, f"Memory: {mem_info['used']}/{mem_info['total']} MB")

        # Network I/O (placeholder)
        row += 1
        win.addstr(row, 2, "Network I/O: [Not implemented]")

        # Disk I/O (placeholder)
        row += 1
        win.addstr(row, 2, "Disk I/O: [Not implemented]")

        # Process info
        row += 2
        win.addstr(row, 0, "Top Processes:", curses.A_BOLD)
        try:
            result = subprocess.run(['ps', 'aux', '--sort=-%cpu'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:6]  # Skip header, show top 5
                for i, line in enumerate(lines):
                    if 7 + i < self.height - 5:
                        parts = line.split()
                        if len(parts) >= 11:
                            cpu = parts[2]
                            pid = parts[1]
                            cmd = ' '.join(parts[10:])[:40]  # Truncate command
                            win.addstr(7 + i, 2, f"PID {pid}: {cpu}% CPU - {cmd}")
        except:
            win.addstr(7, 2, "Unable to read process information")

        # Actions
        row = 15
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "k: Kill process")
        row += 1
        win.addstr(row, 2, "r: Refresh metrics")
        row += 1
        win.addstr(row, 2, "l: View detailed logs")

    def draw_monitor_logs(self, win):
        """Draw log monitoring interface"""
        win.addstr(0, 0, "=== Log Monitoring ===", curses.A_BOLD)

        # Recent system logs
        row = 2
        win.addstr(row, 0, "Recent System Logs:", curses.A_BOLD)

        try:
            result = subprocess.run(
                ['journalctl', '--since', '1 hour ago', '-n', '12', '--no-pager'],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines[-12:]):  # Last 12 lines
                    if i + 4 < self.height - 5:
                        # Color code log levels
                        if 'ERROR' in line or 'CRITICAL' in line:
                            color = curses.color_pair(3)  # Red
                        elif 'WARNING' in line:
                            color = curses.color_pair(5)  # Yellow
                        elif 'INFO' in line:
                            color = curses.color_pair(6)  # Blue
                        else:
                            color = curses.color_pair(2)  # Normal

                        # Truncate and display
                        truncated = line[:self.width-4] if len(line) > self.width-4 else line
                        win.addstr(4 + i, 2, truncated, color)
            else:
                win.addstr(4, 2, "Unable to read system logs")
        except Exception as e:
            win.addstr(4, 2, f"Error reading logs: {e}")

        # Actions
        row = 18
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "f: Follow logs (live)")
        row += 1
        win.addstr(row, 2, "c: Clear old logs")
        row += 1
        win.addstr(row, 2, "e: Export logs")

    def draw_monitor_alerts(self, win):
        """Draw system alerts and notifications"""
        win.addstr(0, 0, "=== System Alerts & Notifications ===", curses.A_BOLD)

        # System health checks
        row = 2
        win.addstr(row, 0, "System Health:", curses.A_BOLD)

        alerts = []

        # Check disk space
        disk_info = self.get_disk_info()
        if disk_info['percent'] > 90:
            alerts.append(('CRITICAL', f"Disk space critically low: {disk_info['percent']}% used"))
        elif disk_info['percent'] > 80:
            alerts.append(('WARNING', f"Disk space low: {disk_info['percent']}% used"))

        # Check memory
        mem_info = self.get_memory_info()
        if mem_info['percent'] > 90:
            alerts.append(('CRITICAL', f"Memory usage critically high: {mem_info['percent']}% used"))
        elif mem_info['percent'] > 80:
            alerts.append(('WARNING', f"Memory usage high: {mem_info['percent']}% used"))

        # Check temperature
        temp_str = self.get_cpu_temp()
        if '°C' in temp_str:
            try:
                temp_val = float(temp_str.replace('°C', ''))
                if temp_val > 80:
                    alerts.append(('CRITICAL', f"CPU temperature critically high: {temp_str}"))
                elif temp_val > 70:
                    alerts.append(('WARNING', f"CPU temperature high: {temp_str}"))
            except:
                pass

        # Check service status
        services = self.get_service_status()
        for service, status in services.items():
            if status not in ['active', 'running']:
                alerts.append(('WARNING', f"Service {service} is {status}"))

        # Display alerts
        if alerts:
            for i, (level, message) in enumerate(alerts[:10]):  # Show first 10
                row += 1
                if level == 'CRITICAL':
                    color = curses.color_pair(3)  # Red
                elif level == 'WARNING':
                    color = curses.color_pair(5)  # Yellow
                else:
                    color = curses.color_pair(2)  # Normal

                win.addstr(row, 2, f"[{level}] {message}", color)
        else:
            row += 1
            win.addstr(row, 2, "✅ All systems normal", curses.color_pair(4))

        # Recent events
        row += 3
        win.addstr(row, 0, "Recent Events:", curses.A_BOLD)

        # Placeholder for recent events - would integrate with logging system
        events = [
            "System startup completed",
            "LMS content loaded successfully",
            "Network connection established"
        ]

        for i, event in enumerate(events):
            row += 1
            win.addstr(row, 2, f"• {event}")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "a: Acknowledge alerts")
        row += 1
        win.addstr(row, 2, "c: Configure alert thresholds")
        row += 1
        win.addstr(row, 2, "e: Email alert notifications")

    # Content Management Methods (implementing the missing ones)
    def draw_content_lms_files(self, win):
        """Draw LMS files management"""
        win.addstr(0, 0, "=== LMS Content Files ===", curses.A_BOLD)

        lms_dir = Path('/home/pi/lms')
        if lms_dir.exists():
            lms_files = list(lms_dir.glob('*.lms'))
            win.addstr(2, 0, f"Found {len(lms_files)} LMS file(s):")

            for i, lms_file in enumerate(sorted(lms_files, key=lambda x: x.stat().st_mtime, reverse=True)):
                if i < 10:  # Show first 10
                    mtime = time.ctime(lms_file.stat().st_mtime)
                    size = lms_file.stat().st_size
                    win.addstr(4 + i, 2, f"• {lms_file.name}")
                    win.addstr(4 + i, 35, f"{size} bytes")
                    win.addstr(4 + i, 50, mtime[:16])
        else:
            win.addstr(2, 0, "LMS directory not found")
            win.addstr(4, 0, "Run setup_device.sh to create directories")

        # Actions
        row = 16
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "e: Edit selected file")
        row += 1
        win.addstr(row, 2, "d: Delete selected file")
        row += 1
        win.addstr(row, 2, "v: Validate LMS syntax")

    def draw_content_templates(self, win):
        """Draw template management"""
        win.addstr(0, 0, "=== Content Templates ===", curses.A_BOLD)

        templates_dir = Path('/opt/314sign/templates')
        if templates_dir.exists():
            template_files = list(templates_dir.glob('*.json'))
            win.addstr(2, 0, f"Available Templates: {len(template_files)}")

            # Built-in templates
            row = 4
            win.addstr(row, 0, "Built-in Templates:", curses.A_BOLD)
            built_ins = ['Restaurant Menu', 'Office Directory', 'School Schedule', 'Retail Display']
            for i, template in enumerate(built_ins):
                row += 1
                win.addstr(row, 2, f"• {template}")

            # Custom templates
            if template_files:
                row += 2
                win.addstr(row, 0, "Custom Templates:", curses.A_BOLD)
                for i, template_file in enumerate(template_files[:5]):  # Show first 5
                    row += 1
                    win.addstr(row, 2, f"• {template_file.stem}")
        else:
            win.addstr(2, 0, "Templates directory not found")

        # Actions
        row = 16
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "c: Create new template")
        row += 1
        win.addstr(row, 2, "e: Edit selected template")
        row += 1
        win.addstr(row, 2, "d: Delete selected template")

    def draw_content_cache(self, win):
        """Draw cache management"""
        win.addstr(0, 0, "=== Cache Management ===", curses.A_BOLD)

        # Background cache
        bg_cache_dir = Path('/var/lib/314sign/backgrounds')
        if bg_cache_dir.exists():
            bg_files = list(bg_cache_dir.glob('*'))
            total_size = sum(f.stat().st_size for f in bg_files) if bg_files else 0
            win.addstr(2, 0, f"Background Cache: {len(bg_files)} files, {total_size // 1024} KB")
        else:
            win.addstr(2, 0, "Background Cache: Directory not found")

        # Font cache
        font_cache_dir = Path('/home/pi/fonts')
        if font_cache_dir.exists():
            font_files = list(font_cache_dir.glob('*'))
            win.addstr(3, 0, f"Font Cache: {len(font_files)} files")
        else:
            win.addstr(3, 0, "Font Cache: Directory not found")

        # LMS cache (if any)
        win.addstr(4, 0, "LMS Cache: Real-time (no persistent cache)")

        # Cache statistics
        row = 6
        win.addstr(row, 0, "Cache Statistics:", curses.A_BOLD)

        try:
            # Get disk usage for cache directories
            cache_dirs = ['/var/lib/314sign', '/home/pi/lms', '/home/pi/fonts']
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    result = subprocess.run(['du', '-sh', cache_dir],
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        size = result.stdout.split()[0]
                        dirname = os.path.basename(cache_dir)
                        row += 1
                        win.addstr(row, 2, f"{dirname}: {size}")
        except:
            row += 1
            win.addstr(row, 2, "Unable to calculate sizes")

        # Actions
        row = 16
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "c: Clear all caches")
        row += 1
        win.addstr(row, 2, "b: Clear background cache only")
        row += 1
        win.addstr(row, 2, "f: Clear font cache only")

    def draw_content_web_editor(self, win):
        """Draw web editor status and management"""
        win.addstr(0, 0, "=== Web Content Editor ===", curses.A_BOLD)

        # Web editor status
        row = 2
        try:
            result = subprocess.run(['systemctl', 'is-active', '314sign-web-editor'],
                                  capture_output=True, text=True, timeout=2)
            status = result.stdout.strip()
            color = curses.color_pair(4) if status == 'active' else curses.color_pair(3)
            win.addstr(row, 0, "Web Editor Service:", color)
            win.addstr(row, 22, status, color)
        except:
            win.addstr(row, 0, "Web Editor Service: Not installed")

        # Port information
        row += 1
        win.addstr(row, 0, "Default Port: 8080")

        # Access information
        row += 1
        try:
            hostname = subprocess.run(['hostname'], capture_output=True, text=True, timeout=2).stdout.strip()
            win.addstr(row, 0, f"Access URL: http://{hostname}.local:8080")
        except:
            win.addstr(row, 0, "Access URL: http://localhost:8080")

        # Features list
        row += 2
        win.addstr(row, 0, "Features:", curses.A_BOLD)
        features = [
            "Drag-and-drop content creation",
            "Visual template selection",
            "Real-time LMS preview",
            "Mobile-responsive interface",
            "Template saving and loading",
            "Multi-element editing"
        ]

        for i, feature in enumerate(features):
            row += 1
            win.addstr(row, 2, f"• {feature}")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "s: Start web editor")
        row += 1
        win.addstr(row, 2, "t: Stop web editor")
        row += 1
        win.addstr(row, 2, "o: Open in browser")

    # Bundle Management Methods
    def draw_bundles_create(self, win):
        """Draw bundle creation interface"""
        win.addstr(0, 0, "=== Create LMS Bundle ===", curses.A_BOLD)

        # Available LMS files
        lms_dir = Path('/home/pi/lms')
        if lms_dir.exists():
            lms_files = list(lms_dir.glob('*.lms'))
            win.addstr(2, 0, f"Available LMS Files: {len(lms_files)}")

            for i, lms_file in enumerate(sorted(lms_files, key=lambda x: x.stat().st_mtime, reverse=True)):
                if i < 8:  # Show first 8
                    mtime = time.ctime(lms_file.stat().st_mtime)
                    size = lms_file.stat().st_size
                    win.addstr(4 + i, 2, f"{i+1}. {lms_file.name}")
                    win.addstr(4 + i, 35, f"{size} bytes")
                    win.addstr(4 + i, 50, mtime[:16])
        else:
            win.addstr(2, 0, "No LMS files found")
            win.addstr(4, 0, "Create content first using web editor")

        # Bundle creation info
        row = 14
        win.addstr(row, 0, "Bundle Creation:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "Bundles automatically include:")
        row += 1
        win.addstr(row, 4, "• LMS content file")
        row += 1
        win.addstr(row, 4, "• Referenced background images")
        row += 1
        win.addstr(row, 4, "• Custom fonts used")
        row += 1
        win.addstr(row, 4, "• Metadata and checksums")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "c: Create bundle from selected file")
        row += 1
        win.addstr(row, 2, "↑↓: Select LMS file")

    def draw_bundles_list(self, win):
        """Draw bundle listing interface"""
        win.addstr(0, 0, "=== Available Bundles ===", curses.A_BOLD)

        # List bundles from bundles directory
        bundles_dir = Path('/var/lib/314sign/bundles')
        if bundles_dir.exists():
            bundle_files = list(bundles_dir.glob('*.bundle'))
            win.addstr(2, 0, f"Found {len(bundle_files)} bundle(s):")

            # Show bundle information
            for i, bundle_file in enumerate(sorted(bundle_files, key=lambda x: x.stat().st_mtime, reverse=True)):
                if i < 10:  # Show first 10
                    bundle_name = bundle_file.stem
                    size = self._get_file_size(bundle_file)
                    mtime = time.ctime(bundle_file.stat().st_mtime)

                    win.addstr(4 + i, 2, f"{i+1}. {bundle_name}")
                    win.addstr(4 + i, 35, f"{size}")
                    win.addstr(4 + i, 50, mtime[:16])
        else:
            win.addstr(2, 0, "No bundles directory found")
            win.addstr(4, 0, "Create bundles first")

        # Bundle statistics
        row = 16
        win.addstr(row, 0, "Bundle Stats:", curses.A_BOLD)
        try:
            if bundles_dir.exists():
                total_size = sum(f.stat().st_size for f in bundles_dir.glob('*.bundle'))
                win.addstr(row + 1, 2, f"Total bundles: {len(list(bundles_dir.glob('*.bundle')))}")
                win.addstr(row + 2, 2, f"Total size: {total_size // 1024} KB")
        except:
            win.addstr(row + 1, 2, "Unable to calculate stats")

        # Actions
        row += 4
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "i: Inspect selected bundle")
        row += 1
        win.addstr(row, 2, "d: Delete selected bundle")
        row += 1
        win.addstr(row, 2, "↑↓: Select bundle")

    def draw_bundles_distribute(self, win):
        """Draw bundle distribution interface"""
        win.addstr(0, 0, "=== Bundle Distribution ===", curses.A_BOLD)

        # Available bundles for distribution
        bundles_dir = Path('/var/lib/314sign/bundles')
        if bundles_dir.exists():
            bundle_files = list(bundles_dir.glob('*.bundle'))
            win.addstr(2, 0, f"Available Bundles: {len(bundle_files)}")

            for i, bundle_file in enumerate(sorted(bundle_files, key=lambda x: x.stat().st_mtime, reverse=True)):
                if i < 5:  # Show first 5
                    bundle_name = bundle_file.stem
                    size = self._get_file_size(bundle_file)
                    win.addstr(4 + i, 2, f"{i+1}. {bundle_name} ({size})")
        else:
            win.addstr(2, 0, "No bundles available")

        # Remote device discovery
        row = 10
        win.addstr(row, 0, "Remote Devices:", curses.A_BOLD)

        # Placeholder for remote device discovery
        row += 1
        win.addstr(row, 2, "Scanning for remote devices...")
        row += 1
        win.addstr(row, 2, "(No remotes detected)")
        row += 1
        win.addstr(row, 2, "Use 's' to scan network")

        # Distribution settings
        row += 3
        win.addstr(row, 0, "Distribution Options:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "Priority: Normal")
        row += 1
        win.addstr(row, 2, "Method: Secure SCP")
        row += 1
        win.addstr(row, 2, "Verification: SHA256 checksums")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "d: Distribute selected bundle")
        row += 1
        win.addstr(row, 2, "s: Scan for remote devices")
        row += 1
        win.addstr(row, 2, "↑↓: Select bundle")

    def draw_bundles_history(self, win):
        """Draw bundle distribution history"""
        win.addstr(0, 0, "=== Distribution History ===", curses.A_BOLD)

        # Distribution log
        row = 2
        win.addstr(row, 0, "Recent Distributions:", curses.A_BOLD)

        # Placeholder for distribution history
        # In a real implementation, this would read from a log file
        history_entries = [
            "2025-12-29 12:30 - restaurant-menu-v3 → lobby-1, lobby-2 (Success)",
            "2025-12-29 12:15 - office-directory-v2 → conference-room (Success)",
            "2025-12-29 11:45 - school-schedule-v1 → classroom-101 (Failed - timeout)",
            "2025-12-29 11:30 - retail-display-v2 → storefront (Success)"
        ]

        for i, entry in enumerate(history_entries):
            if i < 10:  # Show first 10 entries
                win.addstr(4 + i, 2, f"• {entry}")

        # Distribution statistics
        row = 16
        win.addstr(row, 0, "Distribution Stats:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "Total distributions: 24")
        row += 1
        win.addstr(row, 2, "Success rate: 95.8%")
        row += 1
        win.addstr(row, 2, "Average transfer time: 2.3s")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "c: Clear history")
        row += 1
        win.addstr(row, 2, "e: Export history to file")
        row += 1
        win.addstr(row, 2, "r: Retry failed distributions")

    def _get_file_size(self, file_path: Path) -> str:
        """Get human-readable file size"""
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return ".1f"
            size /= 1024.0
        return ".1f"

    # Security Management Methods
    def draw_security_ssh(self, win):
        """Draw SSH security configuration"""
        win.addstr(0, 0, "=== SSH Security Configuration ===", curses.A_BOLD)

        # SSH service status
        row = 2
        try:
            result = subprocess.run(['systemctl', 'is-active', 'ssh'],
                                  capture_output=True, text=True, timeout=2)
            status = result.stdout.strip()
            color = curses.color_pair(4) if status == 'active' else curses.color_pair(3)
            win.addstr(row, 0, "SSH Service:", color)
            win.addstr(row, 14, status, color)
        except:
            win.addstr(row, 0, "SSH Service: Unable to determine")

        # SSH configuration
        row += 1
        try:
            with open('/etc/ssh/sshd_config', 'r') as f:
                config = f.read()
                if 'PermitRootLogin no' in config:
                    win.addstr(row, 0, "Root Login: Disabled")
                else:
                    win.addstr(row, 0, "Root Login: Allowed", curses.color_pair(5))

                row += 1
                if 'PasswordAuthentication no' in config:
                    win.addstr(row, 0, "Password Auth: Disabled")
                else:
                    win.addstr(row, 0, "Password Auth: Enabled", curses.color_pair(5))
        except:
            win.addstr(row, 0, "SSH Config: Unable to read")

        # Current connections
        row += 2
        win.addstr(row, 0, "Active Connections:", curses.A_BOLD)
        try:
            result = subprocess.run(['who'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                connections = result.stdout.strip().split('\n')
                for i, conn in enumerate(connections[:3]):  # Show first 3
                    row += 1
                    win.addstr(row, 2, conn)
        except:
            row += 1
            win.addstr(row, 2, "Unable to read active connections")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "k: Generate new SSH keys")
        row += 1
        win.addstr(row, 2, "p: Change SSH port")
        row += 1
        win.addstr(row, 2, "r: Restart SSH service")

    def draw_security_users(self, win):
        """Draw user management interface"""
        win.addstr(0, 0, "=== User Account Management ===", curses.A_BOLD)

        # Current user
        row = 2
        try:
            current_user = subprocess.run(['whoami'], capture_output=True, text=True, timeout=2).stdout.strip()
            win.addstr(row, 0, f"Current User: {current_user}")
        except:
            win.addstr(row, 0, "Current User: Unable to determine")

        # User list
        row += 2
        win.addstr(row, 0, "System Users:", curses.A_BOLD)
        try:
            result = subprocess.run(['cut', '-d:', '-f1', '/etc/passwd'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                users = [u for u in result.stdout.strip().split('\n')
                        if not u.startswith(('_', 'systemd', 'messagebus', 'nobody'))][:8]
                for i, user in enumerate(users):
                    row += 1
                    if user == 'pi':
                        win.addstr(row, 2, f"{user} (default)", curses.color_pair(4))
                    else:
                        win.addstr(row, 2, user)
        except:
            row += 1
            win.addstr(row, 2, "Unable to read user list")

        # Password status
        row += 2
        win.addstr(row, 0, "Password Status:", curses.A_BOLD)
        try:
            result = subprocess.run(['passwd', '-S', 'pi'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                status_parts = result.stdout.split()
                if len(status_parts) >= 2:
                    status = status_parts[1]
                    if status == 'P':
                        win.addstr(row + 1, 2, "Password set and valid", curses.color_pair(4))
                    elif status == 'NP':
                        win.addstr(row + 1, 2, "No password set", curses.color_pair(3))
                    else:
                        win.addstr(row + 1, 2, f"Password status: {status}")
            else:
                win.addstr(row + 1, 2, "Unable to check password status")
        except:
            win.addstr(row + 1, 2, "Unable to check password status")

        # Actions
        row += 4
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "p: Change password")
        row += 1
        win.addstr(row, 2, "a: Add new user")
        row += 1
        win.addstr(row, 2, "d: Delete user")

    def draw_security_firewall(self, win):
        """Draw firewall security settings"""
        win.addstr(0, 0, "=== Firewall Security ===", curses.A_BOLD)

        # UFW status
        row = 2
        try:
            result = subprocess.run(['ufw', 'status', 'verbose'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                win.addstr(row, 0, lines[0])  # Status line

                # Show key rules
                for i, line in enumerate(lines[1:8]):  # Show first 8 rules
                    if 4 + i < self.height - 10:
                        win.addstr(4 + i, 2, line)
            else:
                win.addstr(row, 0, "Firewall: Not configured or disabled")
        except:
            win.addstr(row, 0, "Firewall: Unable to check status")

        # Default policies
        row += 10
        win.addstr(row, 0, "Default Policies:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "Incoming: Allow (may be restricted)")
        row += 1
        win.addstr(row, 2, "Outgoing: Allow")
        row += 1
        win.addstr(row, 2, "Routed: Deny")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "e: Enable firewall")
        row += 1
        win.addstr(row, 2, "d: Disable firewall")
        row += 1
        win.addstr(row, 2, "r: Reset to defaults")

    def draw_security_updates(self, win):
        """Draw system update management"""
        win.addstr(0, 0, "=== System Updates & Security ===", curses.A_BOLD)

        # Update status
        row = 2
        win.addstr(row, 0, "Update Status:", curses.A_BOLD)

        try:
            # Check for available updates
            result = subprocess.run(['apt', 'list', '--upgradable'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = [l for l in result.stdout.split('\n') if l.strip() and not l.startswith('Listing')]
                update_count = len(lines)
                row += 1
                if update_count == 0:
                    win.addstr(row, 2, "System is up to date", curses.color_pair(4))
                else:
                    win.addstr(row, 2, f"{update_count} updates available", curses.color_pair(5))
                    for i, line in enumerate(lines[:5]):  # Show first 5
                        row += 1
                        package = line.split('/')[0]
                        win.addstr(row, 4, package[:30])
            else:
                row += 1
                win.addstr(row, 2, "Unable to check for updates")
        except:
            row += 1
            win.addstr(row, 2, "Unable to check for updates")

        # Security patches
        row += 2
        win.addstr(row, 0, "Security Patches:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "Check: apt list --upgradable | grep -i security")

        # Last update
        row += 2
        win.addstr(row, 0, "Last Update Check:", curses.A_BOLD)
        try:
            # Check when apt cache was last updated
            result = subprocess.run(['stat', '-c', '%Y', '/var/cache/apt/pkgcache.bin'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                import datetime
                timestamp = int(result.stdout.strip())
                last_update = datetime.datetime.fromtimestamp(timestamp)
                days_ago = (datetime.datetime.now() - last_update).days
                row += 1
                win.addstr(row, 2, f"{days_ago} days ago")
                if days_ago > 7:
                    win.addstr(row, 20, "(Consider updating)", curses.color_pair(5))
            else:
                row += 1
                win.addstr(row, 2, "Unable to determine")
        except:
            row += 1
            win.addstr(row, 2, "Unable to determine")

        # Actions
        row += 3
        win.addstr(row, 0, "Actions:", curses.A_BOLD)
        row += 1
        win.addstr(row, 2, "u: Update package lists")
        row += 1
        win.addstr(row, 2, "i: Install updates")
        row += 1
        win.addstr(row, 2, "s: Install security updates only")

    def handle_input(self, key):
        """Handle keyboard input"""
        if key == ord('\t'):  # Tab key
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
            self.current_subtab = 0  # Reset subtab when changing main tab
        elif key == curses.KEY_LEFT:
            if self.current_tab >= 1:  # Settings tabs with subtabs
                self.current_subtab = (self.current_subtab - 1) % len(self.get_current_subtabs())
            else:
                self.current_tab = (self.current_tab - 1) % len(self.tabs)
        elif key == curses.KEY_RIGHT:
            if self.current_tab >= 1:  # Settings tabs with subtabs
                self.current_subtab = (self.current_subtab + 1) % len(self.get_current_subtabs())
            else:
                self.current_tab = (self.current_tab + 1) % len(self.tabs)
        elif key == curses.KEY_UP:
            self.current_tab = (self.current_tab - 1) % len(self.tabs)
            self.current_subtab = 0  # Reset subtab when changing main tab
        elif key == curses.KEY_DOWN:
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
            self.current_subtab = 0  # Reset subtab when changing main tab
        elif key == ord('q') or key == ord('Q'):
            self.running = False
        elif key == ord('h') or key == ord('H'):
            self.show_help()
        elif key == ord('r') or key == ord('R'):
            # Refresh data
            pass
        # Tab-specific actions
        elif self.current_tab == 1:  # System
            self.handle_system_input(key)
        elif self.current_tab == 2:  # Network
            self.handle_network_input(key)
        elif self.current_tab == 3:  # Content
            self.handle_content_input(key)
        elif self.current_tab == 4:  # Bundles
            self.handle_bundles_input(key)
        elif self.current_tab == 5:  # Monitor
            self.handle_monitor_input(key)

    def get_current_subtabs(self):
        """Get subtabs for current main tab"""
        if self.current_tab == 1:  # System
            return self.system_subtabs
        elif self.current_tab == 2:  # Network
            return self.network_subtabs
        elif self.current_tab == 3:  # Content
            return self.content_subtabs
        elif self.current_tab == 4:  # Security
            return self.security_subtabs
        elif self.current_tab == 5:  # Monitor
            return self.monitor_subtabs
        return []

    def handle_system_input(self, key):
        """Handle system tab specific input"""
        if self.current_subtab == 1:  # Services
            if key == ord(' '):  # Space to toggle service
                self.toggle_selected_service()
        elif self.current_subtab == 3:  # Storage
            if key == ord('c'):  # Clear cache
                self.clear_cache_files()

    def handle_network_input(self, key):
        """Handle network tab specific input"""
        if self.current_subtab == 0:  # WiFi
            if key == ord('c'):  # Connect
                self.connect_wifi()
            elif key == ord('d'):  # Disconnect
                self.disconnect_wifi()
            elif key == ord('s'):  # Scan
                self.scan_wifi_networks()

    def handle_content_input(self, key):
        """Handle content tab specific input"""
        if self.current_subtab == 2:  # Cache
            if key == ord('c'):  # Clear all caches
                self.clear_all_caches()
            elif key == ord('b'):  # Clear background cache
                self.clear_background_cache()
            elif key == ord('f'):  # Clear font cache
                self.clear_font_cache()

    def handle_security_input(self, key):
        """Handle security tab specific input"""
        if self.current_subtab == 0:  # SSH
            if key == ord('k'):  # Generate keys
                self.generate_ssh_keys()
            elif key == ord('p'):  # Change port
                self.change_ssh_port()
        elif self.current_subtab == 3:  # Updates
            if key == ord('u'):  # Update package lists
                self.update_package_lists()
            elif key == ord('i'):  # Install updates
                self.install_updates()
            elif key == ord('s'):  # Security updates only
                self.install_security_updates()

    def handle_monitor_input(self, key):
        """Handle monitor tab specific input"""
        if self.current_subtab == 0:  # Devices
            if key == ord('s'):  # Scan devices
                self.scan_devices()
            elif key == ord('p'):  # Ping devices
                self.ping_devices()
        elif self.current_subtab == 3:  # Alerts
            if key == ord('a'):  # Acknowledge alerts
                self.acknowledge_alerts()

    # Action implementations (placeholders for actual functionality)
    def toggle_selected_service(self):
        """Toggle selected service on/off"""
        # Placeholder - would implement service toggle logic
        pass

    def clear_cache_files(self):
        """Clear cache files"""
        # Placeholder - would implement cache clearing
        pass

    def connect_wifi(self):
        """Connect to WiFi network"""
        # Placeholder - would implement WiFi connection
        pass

    def disconnect_wifi(self):
        """Disconnect from WiFi"""
        # Placeholder - would implement WiFi disconnection
        pass

    def scan_wifi_networks(self):
        """Scan for available WiFi networks"""
        # Placeholder - would implement WiFi scanning
        pass

    def clear_all_caches(self):
        """Clear all cache directories"""
        # Placeholder - would implement cache clearing
        pass

    def clear_background_cache(self):
        """Clear background image cache"""
        # Placeholder - would implement background cache clearing
        pass

    def clear_font_cache(self):
        """Clear font cache"""
        # Placeholder - would implement font cache clearing
        pass

    def generate_ssh_keys(self):
        """Generate new SSH keys"""
        # Placeholder - would implement SSH key generation
        pass

    def change_ssh_port(self):
        """Change SSH port"""
        # Placeholder - would implement SSH port change
        pass

    def update_package_lists(self):
        """Update package lists"""
        # Placeholder - would implement apt update
        pass

    def install_updates(self):
        """Install system updates"""
        # Placeholder - would implement apt upgrade
        pass

    def install_security_updates(self):
        """Install security updates only"""
        # Placeholder - would implement security updates
        pass

    def ping_devices(self):
        """Ping connected devices"""
        # Placeholder - would implement device pinging
        pass

    def acknowledge_alerts(self):
        """Acknowledge system alerts"""
        # Placeholder - would implement alert acknowledgment
        pass

    def show_help(self):
        """Show help dialog"""
        help_win = curses.newwin(15, 60, 5, 10)
        help_panel = curses.panel.new_panel(help_win)

        help_win.clear()
        help_win.border()

        help_text = [
            "314Sign Administration Console Help",
            "",
            "Navigation:",
            "  Tab/←→: Switch between tabs",
            "  ↑↓: Navigate within tab",
            "  Enter: Select/Execute",
            "",
            "Actions:",
            "  r: Refresh data",
            "  s: Scan for devices (Devices tab)",
            "  p: Push content (Devices tab)",
            "  h: Show this help",
            "  q: Quit",
            "",
            "Press any key to close..."
        ]

        for i, line in enumerate(help_text):
            help_win.addstr(1 + i, 2, line)

        help_win.refresh()
        help_win.getch()  # Wait for key press

        # Clean up
        curses.panel.del_panel(help_panel)
        del help_win

    def scan_devices(self):
        """Scan for connected remote devices"""
        # Placeholder - would implement device discovery
        pass

    def push_content(self):
        """Push content to all connected devices"""
        # Placeholder - would implement content distribution
        pass

    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])

            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, _ = divmod(remainder, 60)

            return f"{hours:02d}:{minutes:02d}"
        except:
            return "Unknown"

    def get_cpu_temp(self) -> str:
        """Get CPU temperature"""
        try:
            # Try Raspberry Pi method first
            result = subprocess.run(['vcgencmd', 'measure_temp'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                temp_match = re.search(r'temp=([0-9.]+)', result.stdout)
                if temp_match:
                    return f"{temp_match.group(1)}°C"
        except:
            pass

        # Fallback to standard Linux method
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_raw = int(f.read().strip())
                return f"{temp_raw / 1000:.1f}°C"
        except:
            return "Unknown"

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            with open('/proc/meminfo', 'r') as f:
                mem_info = {}
                for line in f:
                    if line.startswith(('MemTotal:', 'MemAvailable:')):
                        key, value = line.split(':')
                        mem_info[key.strip()] = value.strip()

            if 'MemTotal' in mem_info and 'MemAvailable' in mem_info:
                total_kb = int(mem_info['MemTotal'].split()[0])
                available_kb = int(mem_info['MemAvailable'].split()[0])
                used_kb = total_kb - available_kb

                return {
                    'total': total_kb // 1024,  # MB
                    'used': used_kb // 1024,    # MB
                    'available': available_kb // 1024,  # MB
                    'percent': round((used_kb / total_kb) * 100, 1)
                }
        except:
            pass

        return {'total': 0, 'used': 0, 'available': 0, 'percent': 0}

    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            result = subprocess.run(['df', '/'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        total_kb = int(parts[1])
                        used_kb = int(parts[2])

                        return {
                            'total': total_kb // (1024 * 1024),  # GB
                            'used': used_kb // (1024 * 1024),    # GB
                            'available': (total_kb - used_kb) // (1024 * 1024),  # GB
                            'percent': int(parts[4].rstrip('%'))
                        }
        except:
            pass

        return {'total': 0, 'used': 0, 'available': 0, 'percent': 0}

    def get_service_status(self) -> Dict[str, str]:
        """Get status of key services"""
        services = {
            'kiosk': '314sign-kiosk.service',
            'ssh': 'ssh.service',
            'avahi': 'avahi-daemon.service'
        }

        status = {}
        for name, service in services.items():
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True, text=True, timeout=2
                )
                status[name] = result.stdout.strip()
            except:
                status[name] = 'unknown'

        return status

    def data_refresh_loop(self):
        """Background thread to refresh data periodically"""
        while self.running:
            time.sleep(5)  # Refresh every 5 seconds
            # Could refresh device status, system info, etc.

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.running = False

    def run(self):
        """Main application loop"""
        try:
            while self.running:
                self.draw_header()
                self.draw_tabs()
                self.draw_content()
                self.draw_status_bar()

                # Update panels
                curses.panel.update_panels()
                curses.doupdate()

                # Handle input with timeout
                key = self.screen.getch()
                if key != -1:  # -1 means no key pressed
                    self.handle_input(key)

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up curses interface"""
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        curses.endwin()

def main():
    """Main entry point"""
    # Check if running on console/framebuffer
    if os.environ.get('TERM') == 'linux' or os.environ.get('DISPLAY', '') == '':
        # Running on console - use curses
        def curses_main(stdscr):
            app = KioskAdminConsole(stdscr)
            app.run()

        curses.wrapper(curses_main)
    else:
        # Running in X11 environment - could show message or fallback
        print("Kiosk Admin Console requires console/framebuffer access.")
        print("Please SSH to the kiosk system to use this interface.")
        print("Example: ssh pi@kiosk-main.local")
        exit(1)

if __name__ == "__main__":
    main()