#!/usr/bin/env python3
"""
314Sign Remote Kiosk Application for Raspberry Pi Zero 2W
Lightweight display-only application optimized for minimal hardware
Efficient framebuffer rendering with network content synchronization
"""

import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

import pygame
import json
import time
import logging
import threading
import requests
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import argparse
import signal
import sys
import hashlib
import socket

# Import our hybrid system components
from render.lms_renderer import LMSRenderer
from render.background_cache import BackgroundCache
from lms.parser import LMSParser

# Import blockchain communication (placeholders ready for activation)
from blockchain_communicator import (
    BlockchainCommunicator,
    create_blockchain_communicator,
    enable_blockchain_features
)

# Import package system for .314 file support
from package_314sign import SignPackage, PackageError

class RemoteKioskApp:
    """
    Lightweight remote kiosk application for Pi Zero 2W
    Optimized for minimal resource usage with efficient display rendering
    """

    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Hardware detection and optimization
        self._detect_hardware()
        self._optimize_for_remote_hardware()

        # Initialize core components
        self.display_size = self._get_display_size()
        self.renderer = LMSRenderer(self.display_size, quality='low')
        self.lms_parser = LMSParser()
        self.background_cache = BackgroundCache(
            kiosk_url=self.config.get('main_kiosk_url', 'http://localhost:80'),
            cache_size=50 * 1024 * 1024  # 50MB cache for remote kiosk
        )

        # Content management (minimal)
        self.content_cache = {}
        self.current_content = None
        self.slideshow_state = {
            'current_slide': 0,
            'slide_start_time': 0,
            'paused': False
        }

        # Remote management
        self.device_code = self.config.get('device_code')
        self.main_kiosk_url = self.config.get('main_kiosk_url', 'http://localhost:80')
        self.last_config_check = 0
        self.last_content_update = 0
        self.remote_config = {}

        # State
        self.running = False
        self.network_thread = None

        # Setup directories
        self.cache_dir = Path(self.config.get('cache_dir', '/tmp/314sign_cache'))
        self.cache_dir.mkdir(exist_ok=True)

        self.logger.info(f"Initialized Remote Kiosk - Device: {self.device_code}")

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load remote kiosk configuration"""
        default_config = {
            'device_code': 'REMOTE001',
            'main_kiosk_url': 'http://192.168.1.100:80',
            'display_size': [1920, 1080],
            'orientation': 'landscape',
            'cache_dir': '/tmp/314sign_cache',
            'config_poll_interval': 120,  # 2 minutes for low-power device
            'content_poll_interval': 600,  # 10 minutes for low-power device
            'debug': False,
            'offline_mode': False
        }

        config_paths = [
            config_path,
            '/etc/314sign/remote_kiosk.json',
            '/opt/314sign/remote_kiosk.json'
        ]

        for path in config_paths:
            if path and Path(path).exists():
                try:
                    with open(path, 'r') as f:
                        loaded = json.load(f)
                        default_config.update(loaded)
                    break
                except Exception as e:
                    print(f"Failed to load config {path}: {e}")

        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Setup lightweight logging for remote kiosk"""
        level = logging.DEBUG if self.config.get('debug') else logging.INFO

        # Simple console-only logging for minimal resource usage
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        logger = logging.getLogger('remote_kiosk')

        # Optional file logging (disabled by default for storage efficiency)
        if self.config.get('enable_file_logging', False):
            fh = logging.FileHandler('/tmp/314sign_remote.log')
            fh.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        return logger

    def _detect_hardware(self) -> None:
        """Detect Raspberry Pi hardware capabilities"""
        self.hardware_info = {
            'model': 'unknown',
            'cpu_cores': 1,
            'memory_mb': 512,
            'has_wifi': False
        }

        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()

            if 'Raspberry Pi Zero 2' in cpuinfo:
                self.hardware_info.update({
                    'model': 'pi02w',
                    'cpu_cores': 4,
                    'memory_mb': 512,
                    'has_wifi': True
                })
            elif 'Raspberry Pi Zero W' in cpuinfo:
                self.hardware_info.update({
                    'model': 'pi0w',
                    'cpu_cores': 1,
                    'memory_mb': 512,
                    'has_wifi': True
                })
            elif 'Raspberry Pi 3' in cpuinfo:
                self.hardware_info.update({
                    'model': 'pi3',
                    'cpu_cores': 4,
                    'memory_mb': 1024,
                    'has_wifi': True
                })

        except Exception as e:
            self.logger.warning(f"Hardware detection failed: {e}")

    def _optimize_for_remote_hardware(self) -> None:
        """Set optimizations for resource-constrained Pi Zero 2W"""
        # Configure environment for efficient framebuffer access
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        os.environ['SDL_FBDEV'] = '/dev/fb0'
        os.environ['SDL_NOMOUSE'] = '1'
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '0'

        # Memory optimizations for limited RAM
        self.config['max_cache_size'] = 50 * 1024 * 1024  # 50MB total cache
        self.config['image_cache_size'] = 10 * 1024 * 1024  # 10MB for images
        os.environ['PYGAME_FREETYPE'] = '0'  # Disable advanced font rendering

        # CPU optimizations for efficiency
        if self.hardware_info['cpu_cores'] <= 1:
            # Even more conservative polling for single-core devices
            self.config['config_poll_interval'] = 240  # 4 minutes
            self.config['content_poll_interval'] = 1200  # 20 minutes

        # Disable unnecessary features
        self.config['analytics_enabled'] = False
        self.config['remote_management'] = False

    def _get_display_size(self) -> Tuple[int, int]:
        """Get display size with orientation support"""
        base_size = self.config.get('display_size', [1920, 1080])
        orientation = self.config.get('orientation', 'landscape')

        width, height = base_size

        if orientation == 'portrait':
            return (height, width)
        else:
            return (width, height)

    def setup_framebuffer_display(self) -> pygame.Surface:
        """Initialize pygame with efficient framebuffer display"""
        pygame.init()

        try:
            # Direct framebuffer access optimized for performance
            screen = pygame.display.set_mode(self.display_size, pygame.FULLSCREEN)
            self.logger.info(f"Initialized efficient framebuffer display: {self.display_size}")
        except Exception as e:
            self.logger.error(f"Failed direct framebuffer: {e}")
            # Minimal fallback
            self.logger.info("Attempting minimal fallback display mode...")
            del os.environ['SDL_VIDEODRIVER']
            screen = pygame.display.set_mode(self.display_size)
            self.logger.info("Using fallback display mode")

        pygame.display.set_caption(f"314Sign Remote - {self.device_code}")
        return screen

    def start(self) -> None:
        """Start the remote kiosk application"""
        self.running = True
        self.logger.info("Starting 314Sign Remote Kiosk Application")

        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Initial configuration check
            if not self.config.get('offline_mode'):
                self._poll_remote_config()

            # Start network polling thread
            if not self.config.get('offline_mode'):
                self.network_thread = threading.Thread(target=self._network_polling_loop, daemon=True)
                self.network_thread.start()

            # Start main display loop
            self._display_loop()

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            self.cleanup()

    def _display_loop(self) -> None:
        """Main display rendering loop optimized for efficiency"""
        screen = self.setup_framebuffer_display()

        self.logger.info("Starting remote display loop")

        while self.running:
            try:
                current_time = time.time()

                # Update content based on remote config
                if not self.config.get('offline_mode'):
                    self._check_content_updates()

                # Render current content
                surface = self._render_current_content()
                if surface:
                    screen.blit(surface, (0, 0))
                    pygame.display.flip()

                # Minimal event handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False

                # Conservative frame rate for power efficiency
                time.sleep(0.1)  # ~10 FPS (sufficient for signage)

            except Exception as e:
                self.logger.error(f"Display loop error: {e}")
                time.sleep(5)  # Longer wait before retry

        pygame.quit()

    def _render_current_content(self) -> Optional[pygame.Surface]:
        """Render the current content based on remote config"""
        mode = self.remote_config.get('mode', 'standby')

        try:
            if mode == 'lms':
                return self._render_lms_content()
            elif mode == 'slideshow':
                return self._render_slideshow_content()
            else:
                return self._render_standby_screen()

        except Exception as e:
            self.logger.error(f"Content rendering error: {e}")
            return self._render_standby_screen()

    def _render_lms_content(self) -> Optional[pygame.Surface]:
        """Render LMS content with efficiency optimizations"""
        lms_name = self.remote_config.get('lms_name')
        if not lms_name:
            return self._render_standby_screen()

        # Check cache first (longer cache times for remote)
        cache_key = f"lms_{lms_name}"
        if cache_key in self.content_cache:
            cached_data = self.content_cache[cache_key]
            if time.time() - cached_data['timestamp'] < 7200:  # 2 hour cache
                return self.renderer.render_lms_to_surface(cached_data['data'])

        # Load and parse LMS file
        try:
            lms_data = self._load_remote_lms(lms_name)
            if lms_data:
                # Cache the parsed data
                self.content_cache[cache_key] = {
                    'data': lms_data,
                    'timestamp': time.time()
                }

                # Ensure background images are cached
                self._ensure_background_images(lms_data)

                return self.renderer.render_lms_to_surface(lms_data)

        except Exception as e:
            self.logger.error(f"Failed to render LMS {lms_name}: {e}")

        return self._render_standby_screen()

    def _render_slideshow_content(self) -> Optional[pygame.Surface]:
        """Render slideshow content with minimal resource usage"""
        slideshow_name = self.remote_config.get('slideshow_name')
        if not slideshow_name:
            return self._render_standby_screen()

        # Check cache
        cache_key = f"slideshow_{slideshow_name}"
        if cache_key not in self.content_cache:
            try:
                slideshow_data = self._load_remote_slideshow(slideshow_name)
                if slideshow_data:
                    self.content_cache[cache_key] = {
                        'data': slideshow_data,
                        'timestamp': time.time()
                    }
            except Exception as e:
                self.logger.error(f"Failed to load slideshow {slideshow_name}: {e}")
                return self._render_standby_screen()

        slideshow_data = self.content_cache[cache_key]['data']
        slides = slideshow_data.get('slides', [])

        if not slides:
            return self._render_standby_screen()

        # Handle slide transitions
        current_time = time.time() * 1000  # milliseconds
        current_slide = self.slideshow_state['current_slide']
        slide_start_time = self.slideshow_state['slide_start_time']

        if not self.slideshow_state['paused']:
            slide_duration = slides[current_slide].get('duration', 8000)  # Longer default for remote

            if current_time - slide_start_time >= slide_duration:
                # Advance to next slide
                self.slideshow_state['current_slide'] = (current_slide + 1) % len(slides)
                self.slideshow_state['slide_start_time'] = current_time

        # Render current slide
        slide = slides[self.slideshow_state['current_slide']]
        return self._render_slide(slide, slideshow_data)

    def _render_slide(self, slide: Dict[str, Any], slideshow_data: Dict[str, Any]) -> pygame.Surface:
        """Render a single slideshow slide efficiently"""
        surface = pygame.Surface(self.display_size)

        # Fill background
        bg_color = slideshow_data.get('background_color', '#000000')
        surface.fill(self._parse_color(bg_color))

        # Render based on slide type
        slide_type = slide.get('type', 'text')

        if slide_type == 'text':
            self._render_text_slide(surface, slide)
        elif slide_type == 'image':
            self._render_image_slide(surface, slide)
        elif slide_type == 'video':
            self._render_video_slide(surface, slide)

        return surface

    def _render_text_slide(self, surface: pygame.Surface, slide: Dict[str, Any]) -> None:
        """Render text-based slide efficiently"""
        content = slide.get('content', '')
        font_size = slide.get('fontSize', 6)  # Slightly larger default for remote displays
        font_family = slide.get('font', 'Arial, sans-serif')
        color = self._parse_color(slide.get('color', '#FFFFFF'))

        # Convert font size percentage to pixels
        font_pixel_size = int(self.display_size[1] * font_size / 100)

        try:
            font = pygame.font.SysFont(font_family.split(',')[0].strip(), font_pixel_size)
            text_surface = font.render(content, True, color)

            # Center the text
            x = (self.display_size[0] - text_surface.get_width()) // 2
            y = (self.display_size[1] - text_surface.get_height()) // 2

            surface.blit(text_surface, (x, y))

        except Exception as e:
            self.logger.error(f"Failed to render text slide: {e}")

    def _render_image_slide(self, surface: pygame.Surface, slide: Dict[str, Any]) -> None:
        """Render image-based slide with caching"""
        media_path = slide.get('media', '')
        if not media_path:
            return

        try:
            # Check if it's a remote URL or local path
            if media_path.startswith('http'):
                # Download and cache image
                cached_path = self._download_and_cache_media(media_path)
                if cached_path:
                    image = pygame.image.load(str(cached_path))
                else:
                    return
            else:
                # Local path
                image = pygame.image.load(media_path)

            # Scale image to fit display while maintaining aspect ratio
            img_width, img_height = image.get_size()
            scale_factor = min(self.display_size[0] / img_width, self.display_size[1] / img_height)

            if scale_factor < 1.0:
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                # Use faster scaling for remote devices
                image = pygame.transform.scale(image, (new_width, new_height))

            # Center the image
            x = (self.display_size[0] - image.get_width()) // 2
            y = (self.display_size[1] - image.get_height()) // 2

            surface.blit(image, (x, y))

        except Exception as e:
            self.logger.error(f"Failed to render image slide: {e}")

    def _render_video_slide(self, surface: pygame.Surface, slide: Dict[str, Any]) -> None:
        """Render video-based slide (minimal implementation)"""
        # For remote kiosks, just show video info as text
        slide['content'] = f"Video Content\n{slide.get('media', 'Unknown')}"
        slide['type'] = 'text'
        self._render_text_slide(surface, slide)

    def _render_standby_screen(self) -> pygame.Surface:
        """Render minimal standby screen"""
        surface = pygame.Surface(self.display_size)
        surface.fill((0, 10, 20))  # Dark blue

        standby_text = [
            "314Sign Remote Display",
            f"Device: {self.device_code}",
            f"Mode: {self.remote_config.get('mode', 'standby')}",
            "",
            "Waiting for content...",
            "",
            f"Last check: {time.strftime('%H:%M')}"
        ]

        y_offset = self.display_size[1] // 2 - 80

        for line in standby_text:
            if line.strip():
                try:
                    font = pygame.font.SysFont('Arial', 20)
                    text_surface = font.render(line, True, (200, 200, 200))
                    text_rect = text_surface.get_rect(
                        centerx=self.display_size[0] // 2,
                        centery=y_offset
                    )
                    surface.blit(text_surface, text_rect)
                except:
                    pass  # Skip font errors
            y_offset += 25

        return surface

    def _network_polling_loop(self) -> None:
        """Efficient network polling for remote configuration"""
        while self.running:
            try:
                current_time = time.time()

                # Poll for configuration updates
                if current_time - self.last_config_check > self.config['config_poll_interval']:
                    self._poll_remote_config()
                    self.last_config_check = current_time

                # Poll for content updates (less frequent)
                if current_time - self.last_content_update > self.config['content_poll_interval']:
                    self._poll_content_updates()
                    self.last_content_update = current_time

            except Exception as e:
                self.logger.error(f"Network polling error: {e}")

            # Longer sleep for power efficiency
            time.sleep(30)  # Poll every 30 seconds

    def _poll_remote_config(self) -> None:
        """Poll main kiosk for configuration updates"""
        try:
            if not self.device_code:
                self.logger.warning("No device code configured")
                return

            config_url = f"{self.main_kiosk_url}/api/remotes/config/{self.device_code}"

            # Shorter timeout for efficiency
            response = requests.get(config_url, timeout=15)
            response.raise_for_status()

            new_config = response.json()

            if new_config.get('registered'):
                # Update our configuration
                old_mode = self.remote_config.get('mode')
                self.remote_config.update({
                    'mode': new_config.get('mode', 'standby'),
                    'lms_name': new_config.get('lmsName'),
                    'slideshow_name': new_config.get('slideshowName'),
                    'orientation': new_config.get('orientation', {}),
                    'last_update': new_config.get('lastUpdate')
                })

                # Clear content cache if mode changed
                if old_mode != self.remote_config.get('mode'):
                    self.content_cache.clear()
                    self.logger.info(f"Mode changed to {self.remote_config.get('mode')}")

                self.logger.info("Configuration updated")
            else:
                self.logger.info("Device not registered")

        except requests.RequestException as e:
            self.logger.warning(f"Failed to poll remote config: {e}")
        except Exception as e:
            self.logger.error(f"Config polling error: {e}")

    def _poll_content_updates(self) -> None:
        """Check for content updates (minimal implementation)"""
        try:
            # Simple cache validation - in production this would check server timestamps
            mode = self.remote_config.get('mode')

            if mode == 'lms' and self.remote_config.get('lms_name'):
                content_name = self.remote_config['lms_name']
                cache_key = f"lms_{content_name}"
                # Force refresh every content poll interval
                if cache_key in self.content_cache:
                    del self.content_cache[cache_key]

            elif mode == 'slideshow' and self.remote_config.get('slideshow_name'):
                content_name = self.remote_config['slideshow_name']
                cache_key = f"slideshow_{content_name}"
                if cache_key in self.content_cache:
                    del self.content_cache[cache_key]

        except Exception as e:
            self.logger.error(f"Content update check error: {e}")

    def _load_remote_lms(self, lms_name: str) -> Optional[Dict[str, Any]]:
        """Load LMS content from remote server (supports .314 packages)"""
        try:
            # First try to load as .314 package
            package_data = self._load_remote_package(lms_name)
            if package_data:
                self.logger.info(f"Loaded .314 package: {lms_name}")
                return package_data['lms_data']

            # Fall back to regular LMS file
            lms_url = f"{self.main_kiosk_url}/api/lms/{lms_name}"
            response = requests.get(lms_url, timeout=30)
            response.raise_for_status()

            lms_content = response.text
            return self.lms_parser.parse_string(lms_content)

        except requests.RequestException as e:
            self.logger.error(f"Failed to load LMS {lms_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"LMS parsing error for {lms_name}: {e}")
            return None

    def _load_remote_package(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Load .314 package from remote server"""
        try:
            # Try package URL first
            package_url = f"{self.main_kiosk_url}/api/packages/{package_name}.314"

            response = requests.get(package_url, timeout=60)  # Longer timeout for packages
            if response.status_code == 404:
                return None  # Package doesn't exist, fall back to LMS

            response.raise_for_status()

            # Save package to temporary file
            with tempfile.NamedTemporaryFile(suffix='.314', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name

            try:
                # Load and validate package
                package_tool = SignPackage()
                package_data = package_tool.load_package(Path(temp_path))

                # Extract embedded assets to cache
                self._extract_package_assets(package_data)

                self.logger.info(f"Successfully loaded package: {package_name}.314")
                return package_data

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except requests.RequestException as e:
            self.logger.warning(f"Failed to load package {package_name}: {e}")
            return None
        except PackageError as e:
            self.logger.error(f"Package validation error for {package_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error loading package {package_name}: {e}")
            return None

    def _extract_package_assets(self, package_data: Dict[str, Any]) -> None:
        """Extract and cache embedded package assets"""
        try:
            for filename, asset_data in package_data.get('assets', {}).items():
                # Decode base64 data
                asset_bytes = base64.b64decode(asset_data['data'])

                # Save to cache directory
                cache_path = self.cache_dir / f"pkg_{filename}"
                cache_path.parent.mkdir(parents=True, exist_ok=True)

                with open(cache_path, 'wb') as f:
                    f.write(asset_bytes)

                self.logger.debug(f"Extracted package asset: {filename}")

        except Exception as e:
            self.logger.error(f"Failed to extract package assets: {e}")

    def _load_remote_slideshow(self, slideshow_name: str) -> Optional[Dict[str, Any]]:
        """Load slideshow content from remote server"""
        try:
            slideshow_url = f"{self.main_kiosk_url}/api/slideshows/{slideshow_name}"

            response = requests.get(slideshow_url, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            self.logger.error(f"Failed to load slideshow {slideshow_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Slideshow parsing error for {slideshow_name}: {e}")
            return None

    def _ensure_background_images(self, lms_data: Dict[str, Any]) -> None:
        """Ensure background images are cached locally"""
        if 'background' not in lms_data:
            return

        background = lms_data['background']
        image_name = background.get('image')
        expected_hash = background.get('hash')

        if image_name:
            cached_path = self.background_cache.get_cached_path(image_name, expected_hash)
            if not cached_path:
                self.logger.info(f"Downloading background: {image_name}")
                self.background_cache.download_and_cache(image_name, expected_hash)

    def _download_and_cache_media(self, media_url: str) -> Optional[Path]:
        """Download and cache media file efficiently"""
        try:
            # Simple hash-based caching
            url_hash = hashlib.md5(media_url.encode()).hexdigest()
            cache_path = self.cache_dir / f"media_{url_hash}"

            if cache_path.exists():
                return cache_path

            # Download with reasonable timeout
            response = requests.get(media_url, timeout=45, stream=True)
            response.raise_for_status()

            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=4096):  # Smaller chunks for low memory
                    f.write(chunk)

            self.logger.info(f"Cached media: {cache_path.name}")
            return cache_path

        except Exception as e:
            self.logger.error(f"Failed to cache media {media_url}: {e}")
            return None

    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """Parse color string to RGB tuple"""
        if not color_str:
            return (255, 255, 255)

        if color_str.startswith('#'):
            hex_str = color_str[1:]
            if len(hex_str) == 6:
                return (
                    int(hex_str[0:2], 16),
                    int(hex_str[2:4], 16),
                    int(hex_str[4:6], 16)
                )

        # Minimal color support for efficiency
        named_colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
        }

        return named_colors.get(color_str.lower(), (255, 255, 255))

    def _check_content_updates(self) -> None:
        """Minimal content update checking"""
        # Implementation for real-time updates if needed
        pass

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources efficiently"""
        self.logger.info("Cleaning up remote kiosk resources...")
        self.renderer.cleanup()

        # Minimal cleanup for remote kiosks
        if self.config.get('clear_cache_on_exit'):
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
            except:
                pass

        self.logger.info("Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description='314Sign Remote Kiosk')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--device-code', help='Override device code')
    parser.add_argument('--main-kiosk-url', help='Main kiosk server URL')
    parser.add_argument('--offline', action='store_true', help='Run in offline mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Create remote kiosk instance
    kiosk = RemoteKioskApp(args.config)

    # Override config with command line args
    if args.device_code:
        kiosk.config['device_code'] = args.device_code
        kiosk.device_code = args.device_code
    if args.main_kiosk_url:
        kiosk.config['main_kiosk_url'] = args.main_kiosk_url
    if args.offline:
        kiosk.config['offline_mode'] = True
    if args.debug:
        kiosk.config['debug'] = True
        kiosk.logger.setLevel(logging.DEBUG)

    try:
        kiosk.start()
    except KeyboardInterrupt:
        print("Remote kiosk stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()