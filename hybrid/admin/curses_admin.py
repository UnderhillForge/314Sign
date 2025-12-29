#!/usr/bin/env python3
"""
Curses-Based Kiosk Administration Console
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
        self.tabs = ['Dashboard', 'Devices', 'Content', 'Config', 'Logs']
        self.running = True

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

        # Main content area
        content_height = self.height - 6
        self.windows['content'] = curses.newwin(content_height, self.width, 4, 0)
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

    def draw_content(self):
        """Draw the main content area based on current tab"""
        content = self.windows['content']
        content.clear()

        if self.current_tab == 0:
            self.draw_dashboard(content)
        elif self.current_tab == 1:
            self.draw_devices(content)
        elif self.current_tab == 2:
            self.draw_content_tab(content)
        elif self.current_tab == 3:
            self.draw_config(content)
        elif self.current_tab == 4:
            self.draw_logs(content)

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

    def handle_input(self, key):
        """Handle keyboard input"""
        if key == ord('\t'):  # Tab key
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
        elif key == curses.KEY_LEFT:
            self.current_tab = (self.current_tab - 1) % len(self.tabs)
        elif key == curses.KEY_RIGHT:
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
        elif key == ord('q') or key == ord('Q'):
            self.running = False
        elif key == ord('h') or key == ord('H'):
            self.show_help()
        elif key == ord('r') or key == ord('R'):
            # Refresh data
            pass
        elif key == ord('s') or key == ord('S'):
            if self.current_tab == 1:  # Devices tab
                self.scan_devices()
        elif key == ord('p') or key == ord('P'):
            if self.current_tab == 1:  # Devices tab
                self.push_content()

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