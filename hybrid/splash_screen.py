#!/usr/bin/env python3
"""
314Sign Embedded Splash Screen System
Professional boot splash and status displays for embedded devices
"""

import pygame
import json
import time
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse

class EmbeddedSplashScreen:
    """
    Embedded splash screen system for professional boot displays
    Shows company branding, status information, and system details
    """

    def __init__(self, config_path: Optional[str] = None):
        self.display_size = (1920, 1080)  # Default HD resolution

        # Setup direct framebuffer
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        os.environ['SDL_FBDEV'] = '/dev/fb0'
        os.environ['SDL_NOMOUSE'] = '1'
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '0'

        pygame.init()
        self.screen = pygame.display.set_mode(self.display_size, pygame.FULLSCREEN)

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize fonts and colors
        pygame.font.init()
        self.fonts = self._load_fonts()
        self.colors = self._load_colors()

        # State
        self.start_time = time.time()
        self.system_info = {}

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load splash screen configuration"""
        default_config = {
            'company_name': '314Sign',
            'tagline': 'Digital Signage Platform',
            'logo_path': '/opt/314sign/logo.png',
            'background_color': '#000000',
            'text_color': '#FFFFFF',
            'accent_color': '#FFD700',
            'show_system_info': True,
            'show_network_info': True,
            'show_progress_bar': False,
            'boot_timeout': 30,  # seconds
            'animations': True,
            'status_messages': [
                'Initializing system...',
                'Loading configuration...',
                'Starting services...',
                'System ready!'
            ]
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                print(f"Failed to load config: {e}")

        return default_config

    def _load_fonts(self) -> Dict[str, pygame.font.Font]:
        """Load fonts for the splash screen"""
        fonts = {}

        # Try to load system fonts, fall back to defaults
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
            '/System/Library/Fonts/Arial.ttf'  # macOS fallback
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    fonts['title'] = pygame.font.Font(path, 72)
                    fonts['subtitle'] = pygame.font.Font(path, 36)
                    fonts['body'] = pygame.font.Font(path, 24)
                    fonts['small'] = pygame.font.Font(path, 18)
                    break
                except:
                    continue

        # Fallback to system fonts
        if not fonts:
            fonts['title'] = pygame.font.SysFont('arial', 72, bold=True)
            fonts['subtitle'] = pygame.font.SysFont('arial', 36)
            fonts['body'] = pygame.font.SysFont('arial', 24)
            fonts['small'] = pygame.font.SysFont('arial', 18)

        return fonts

    def _load_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Load color scheme"""
        return {
            'background': self._parse_color(self.config.get('background_color', '#000000')),
            'text': self._parse_color(self.config.get('text_color', '#FFFFFF')),
            'accent': self._parse_color(self.config.get('accent_color', '#FFD700')),
            'success': (0, 255, 0),
            'warning': (255, 255, 0),
            'error': (255, 0, 0)
        }

    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """Parse color string to RGB tuple"""
        if color_str.startswith('#'):
            color_str = color_str[1:]
            if len(color_str) == 6:
                return tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
        return (255, 255, 255)  # Default white

    def run_splash(self, duration: Optional[int] = None) -> None:
        """Run the splash screen for specified duration"""
        duration = duration or self.config.get('boot_timeout', 30)
        end_time = time.time() + duration

        # Collect initial system info
        self.system_info = self._get_system_info()

        try:
            while time.time() < end_time:
                self._render_frame()
                time.sleep(0.1)  # 10 FPS

                # Check for quit events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return

        finally:
            pygame.quit()

    def _render_frame(self) -> None:
        """Render a single frame of the splash screen"""
        # Clear screen
        self.screen.fill(self.colors['background'])

        current_time = time.time()
        elapsed = current_time - self.start_time

        # Draw logo/company branding
        self._draw_branding()

        # Draw status information
        self._draw_status_info(elapsed)

        # Draw system information
        if self.config.get('show_system_info', True):
            self._draw_system_info()

        # Draw network information
        if self.config.get('show_network_info', True):
            self._draw_network_info()

        # Draw progress bar if enabled
        if self.config.get('show_progress_bar', False):
            self._draw_progress_bar(elapsed)

        # Update display
        pygame.display.flip()

    def _draw_branding(self) -> None:
        """Draw company branding and logo"""
        center_x = self.display_size[0] // 2
        y_offset = 100

        # Company name
        company_text = self.fonts['title'].render(
            self.config.get('company_name', '314Sign'),
            True,
            self.colors['accent']
        )
        company_rect = company_text.get_rect(centerx=center_x, centery=y_offset)
        self.screen.blit(company_text, company_rect)

        # Tagline
        y_offset += 80
        tagline_text = self.fonts['subtitle'].render(
            self.config.get('tagline', 'Digital Signage Platform'),
            True,
            self.colors['text']
        )
        tagline_rect = tagline_text.get_rect(centerx=center_x, centery=y_offset)
        self.screen.blit(tagline_text, tagline_rect)

        # Logo if available
        logo_path = self.config.get('logo_path')
        if logo_path and os.path.exists(logo_path):
            try:
                logo = pygame.image.load(logo_path)
                # Scale logo to reasonable size
                max_logo_size = (200, 200)
                logo = pygame.transform.scale(logo, max_logo_size)
                logo_rect = logo.get_rect(centerx=center_x, centery=y_offset - 150)
                self.screen.blit(logo, logo_rect)
            except Exception as e:
                print(f"Failed to load logo: {e}")

    def _draw_status_info(self, elapsed: float) -> None:
        """Draw current status information"""
        center_x = self.display_size[0] // 2
        y_offset = self.display_size[1] // 2 + 50

        # Status messages
        status_messages = self.config.get('status_messages', [])
        if status_messages:
            # Cycle through messages based on elapsed time
            message_index = int(elapsed / 2) % len(status_messages)
            status_text = status_messages[message_index]

            status_surface = self.fonts['body'].render(
                status_text,
                True,
                self.colors['text']
            )
            status_rect = status_surface.get_rect(centerx=center_x, centery=y_offset)
            self.screen.blit(status_surface, status_rect)

        # Boot time
        y_offset += 50
        boot_time_text = f"Boot Time: {elapsed:.1f}s"
        boot_surface = self.fonts['small'].render(
            boot_time_text,
            True,
            self.colors['text']
        )
        boot_rect = boot_surface.get_rect(centerx=center_x, centery=y_offset)
        self.screen.blit(boot_surface, boot_rect)

    def _draw_system_info(self) -> None:
        """Draw system information"""
        x_offset = 50
        y_offset = self.display_size[1] - 200

        # System info header
        header_text = self.fonts['small'].render("System Information:", True, self.colors['accent'])
        self.screen.blit(header_text, (x_offset, y_offset))
        y_offset += 25

        # System details
        info_lines = [
            f"Hostname: {self.system_info.get('hostname', 'Unknown')}",
            f"CPU Temp: {self.system_info.get('cpu_temp', 'Unknown')}",
            f"Memory: {self.system_info.get('memory', 'Unknown')}",
            f"Uptime: {self.system_info.get('uptime', 'Unknown')}"
        ]

        for line in info_lines:
            line_surface = self.fonts['small'].render(line, True, self.colors['text'])
            self.screen.blit(line_surface, (x_offset, y_offset))
            y_offset += 20

    def _draw_network_info(self) -> None:
        """Draw network information"""
        x_offset = self.display_size[0] - 350
        y_offset = self.display_size[1] - 200

        # Network info header
        header_text = self.fonts['small'].render("Network Information:", True, self.colors['accent'])
        self.screen.blit(header_text, (x_offset, y_offset))
        y_offset += 25

        # Network details
        info_lines = [
            f"IP Address: {self.system_info.get('ip_address', 'Not connected')}",
            f"MAC Address: {self.system_info.get('mac_address', 'Unknown')}",
            f"WiFi SSID: {self.system_info.get('wifi_ssid', 'N/A')}",
        ]

        for line in info_lines:
            line_surface = self.fonts['small'].render(line, True, self.colors['text'])
            self.screen.blit(line_surface, (x_offset, y_offset))
            y_offset += 20

    def _draw_progress_bar(self, elapsed: float) -> None:
        """Draw a progress bar"""
        center_x = self.display_size[0] // 2
        y_offset = self.display_size[1] - 100

        bar_width = 400
        bar_height = 20

        # Background
        bg_rect = pygame.Rect(center_x - bar_width//2, y_offset, bar_width, bar_height)
        pygame.draw.rect(self.screen, self.colors['text'], bg_rect, 2)

        # Progress fill (simulate progress)
        progress = min(elapsed / 30.0, 1.0)  # 30 second boot
        fill_width = int(bar_width * progress)
        fill_rect = pygame.Rect(center_x - bar_width//2, y_offset, fill_width, bar_height)
        pygame.draw.rect(self.screen, self.colors['accent'], fill_rect)

    def _get_system_info(self) -> Dict[str, str]:
        """Collect system information"""
        info = {}

        try:
            # Hostname
            info['hostname'] = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()

            # CPU Temperature
            try:
                result = subprocess.run(['vcgencmd', 'measure_temp'],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    import re
                    temp_match = re.search(r'temp=([0-9.]+)', result.stdout)
                    if temp_match:
                        info['cpu_temp'] = f"{temp_match.group(1)}°C"
            except:
                pass

            # Memory usage
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            total_kb = int(line.split()[1])
                        elif line.startswith('MemAvailable:'):
                            available_kb = int(line.split()[1])

                    used_kb = total_kb - available_kb
                    used_percent = (used_kb / total_kb) * 100
                    info['memory'] = f"{used_kb//1024}MB / {total_kb//1024}MB ({used_percent:.1f}%)"
            except:
                pass

            # Uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                    hours, remainder = divmod(int(uptime_seconds), 3600)
                    minutes, _ = divmod(remainder, 60)
                    info['uptime'] = f"{hours:02d}:{minutes:02d}"
            except:
                pass

            # Network info
            try:
                result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    for line in result.stdout.split():
                        if line.count('.') == 3:  # IP address
                            info['ip_address'] = line
                            break
            except:
                pass

            # MAC address
            try:
                result = subprocess.run(['cat', '/sys/class/net/eth0/address'],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    info['mac_address'] = result.stdout.strip()
            except:
                pass

        except Exception as e:
            print(f"Error collecting system info: {e}")

        return info

def main():
    """Main entry point for splash screen"""
    parser = argparse.ArgumentParser(description='314Sign Embedded Splash Screen')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--duration', '-d', type=int, help='Display duration in seconds')
    parser.add_argument('--fullscreen', action='store_true', default=True, help='Run in fullscreen mode')

    args = parser.parse_args()

    try:
        splash = EmbeddedSplashScreen(args.config)
        splash.run_splash(args.duration)
    except KeyboardInterrupt:
        print("Splash screen interrupted")
    except Exception as e:
        print(f"Splash screen error: {e}")

if __name__ == "__main__":
    main()