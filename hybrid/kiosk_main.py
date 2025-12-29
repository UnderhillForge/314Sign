#!/usr/bin/env python3
"""
Unified Kiosk Application - Runs as Main Kiosk or Remote Display
Combines web server, display engine, and content management into a single application
"""

import pygame
import json
import time
import logging
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import signal
import sys

# Import our hybrid system components
from render.lms_renderer import LMSRenderer
from render.background_cache import BackgroundCache
from lms.parser import LMSParser

class UnifiedKioskApp:
    """
    Unified application that runs as either:
    - Main Kiosk: Web server + display engine + content management
    - Remote Display: Display engine only
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Core components
        self.display_size = tuple(self.config.get('display_size', [1920, 1080]))
        self.is_main_kiosk = self.config.get('mode', 'remote') == 'main'
        self.device_id = self.config.get('device_id', 'unknown')

        # Initialize subsystems
        self.renderer = LMSRenderer(self.display_size)
        self.background_cache = BackgroundCache(
            kiosk_url=self.config.get('kiosk_url', 'http://localhost:80')
        )
        self.lms_parser = LMSParser()

        # State
        self.current_lms_path = None
        self.running = False
        self.web_server_process = None

        self.logger.info(f"Initialized {'Main Kiosk' if self.is_main_kiosk else 'Remote Display'} - {self.device_id}")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load application configuration"""
        default_config = {
            'mode': 'remote',  # 'main' or 'remote'
            'device_id': 'default-device',
            'display_size': [1920, 1080],
            'kiosk_url': 'http://localhost:80',
            'lms_directory': '/home/pi/lms',
            'update_interval': 300,  # 5 minutes
            'web_server_enabled': True,
            'web_server_port': 80,
            'fullscreen': True,
            'debug': False
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                print(f"Failed to load config {config_path}: {e}")

        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        level = logging.DEBUG if self.config.get('debug') else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def start_web_server(self) -> None:
        """Start the web server (main kiosk only)"""
        if not self.is_main_kiosk or not self.config.get('web_server_enabled', True):
            return

        try:
            port = self.config.get('web_server_port', 80)
            self.logger.info(f"Starting web server on port {port}")

            # For now, we'll use a simple approach - in production this would integrate
            # with the existing Node.js server or run a Python web server
            # This is a placeholder for the web server integration

            self.logger.info("Web server integration placeholder - would start Node.js server here")

        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")

    def stop_web_server(self) -> None:
        """Stop the web server"""
        if self.web_server_process:
            self.web_server_process.terminate()
            self.web_server_process.wait()
            self.web_server_process = None

    def setup_display_environment(self) -> None:
        """Configure display environment for direct hardware access"""
        # Use direct framebuffer for all devices (no X11 anywhere)
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        os.environ['SDL_FBDEV'] = '/dev/fb0'

        # Additional environment variables for kiosk mode
        os.environ['SDL_NOMOUSE'] = '1'  # Disable mouse cursor
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '0'  # Disable screensaver

        self.logger.info("Configured direct framebuffer display (no X11)")

    def display_loop(self) -> None:
        """Main display loop with direct framebuffer access"""
        # Configure for direct hardware rendering
        self.setup_display_environment()

        pygame.init()

        # Always fullscreen for kiosk operation
        try:
            screen = pygame.display.set_mode(self.display_size, pygame.FULLSCREEN)
            self.logger.info(f"Initialized direct framebuffer display: {self.display_size}")
        except Exception as e:
            self.logger.error(f"Failed to initialize framebuffer display: {e}")
            # Fallback for development environments
            self.logger.info("Attempting fallback display mode...")
            del os.environ['SDL_VIDEODRIVER']
            screen = pygame.display.set_mode(self.display_size)
            self.logger.info("Using fallback display mode (X11)")

        pygame.display.set_caption(f"Kiosk Display - {self.device_id}")

        self.logger.info("Starting display loop")

        last_update_check = 0
        update_interval = self.config.get('update_interval', 300)

        while self.running:
            try:
                current_time = time.time()

                # Check for content updates
                if current_time - last_update_check > update_interval:
                    self.check_for_content_updates()
                    last_update_check = current_time

                # Render and display current content
                surface = self.render_current_content()
                if surface:
                    screen.blit(surface, (0, 0))
                    pygame.display.flip()

                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False

                # Small delay to prevent busy waiting
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Display loop error: {e}")
                time.sleep(5)  # Wait before retry

        pygame.quit()
        self.logger.info("Display loop ended")

    def check_for_content_updates(self) -> None:
        """Check for new LMS content files"""
        lms_dir = Path(self.config.get('lms_directory', '/home/pi/lms'))

        if not lms_dir.exists():
            self.logger.debug(f"LMS directory {lms_dir} does not exist")
            return

        # Find LMS files
        lms_files = list(lms_dir.glob("*.lms"))

        if not lms_files:
            self.logger.debug("No LMS files found")
            return

        # Sort by modification time (newest first)
        lms_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_lms = lms_files[0]

        # Check if we need to update
        if self.current_lms_path != latest_lms:
            self.logger.info(f"New LMS content detected: {latest_lms}")
            self.current_lms_path = latest_lms
            # Content will be re-rendered on next display cycle

    def render_current_content(self) -> Optional[pygame.Surface]:
        """Render the current LMS content"""
        if not self.current_lms_path:
            return self.render_standby_screen()

        try:
            # Parse LMS file
            lms_data = self.lms_parser.parse_file(self.current_lms_path)

            # Ensure background images are available
            self.ensure_background_images(lms_data)

            # Render to surface
            surface = self.renderer.render_lms_to_surface(lms_data)

            return surface

        except Exception as e:
            self.logger.error(f"Failed to render content: {e}")
            return self.render_standby_screen()

    def ensure_background_images(self, lms_data: Dict[str, Any]) -> None:
        """Ensure all required background images are cached"""
        if 'background' not in lms_data:
            return

        background = lms_data['background']
        image_name = background.get('image')
        expected_hash = background.get('hash')

        if image_name:
            # Check if cached, download if needed
            cached_path = self.background_cache.get_cached_path(image_name, expected_hash)
            if not cached_path:
                self.logger.info(f"Downloading background: {image_name}")
                self.background_cache.download_and_cache(image_name, expected_hash)

    def render_standby_screen(self) -> pygame.Surface:
        """Render standby screen when no content is available"""
        surface = pygame.Surface(self.display_size)
        surface.fill((0, 20, 40))  # Dark blue

        # Render standby message
        standby_text = [
            "314Sign Digital Display",
            f"Device: {self.device_id}",
            f"Mode: {'Main Kiosk' if self.is_main_kiosk else 'Remote Display'}",
            "",
            "Waiting for content...",
            "",
            f"Last check: {time.strftime('%H:%M:%S')}"
        ]

        y_offset = self.display_size[1] // 2 - 100

        for line in standby_text:
            if line.strip():  # Skip empty lines
                text_surface = self.renderer._get_font('Arial', 24).render(
                    line, True, (255, 255, 255)
                )
                text_rect = text_surface.get_rect(
                    centerx=self.display_size[0] // 2,
                    centery=y_offset
                )
                surface.blit(text_surface, text_rect)
            y_offset += 30

        return surface

    def run(self) -> None:
        """Main application loop"""
        self.running = True
        self.logger.info(f"Starting {'Main Kiosk' if self.is_main_kiosk else 'Remote Display'} application")

        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Start web server if main kiosk
            if self.is_main_kiosk:
                self.start_web_server()

            # Start display loop in main thread
            self.display_loop()

        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.cleanup()

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        self.stop_web_server()
        self.renderer.cleanup()
        self.logger.info("Cleanup complete")

def main():
    parser = argparse.ArgumentParser(description='Unified Kiosk Application')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--mode', choices=['main', 'remote'], help='Override mode in config')
    parser.add_argument('--device-id', help='Override device ID')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-fullscreen', action='store_true', help='Disable fullscreen mode')

    args = parser.parse_args()

    # Load configuration
    config_path = args.config or '/home/pi/kiosk_config.json'

    # Create default config if it doesn't exist
    if not Path(config_path).exists():
        default_config = {
            'mode': args.mode or 'remote',
            'device_id': args.device_id or f"kiosk-{int(time.time())}",
            'display_size': [1920, 1080],
            'kiosk_url': 'http://localhost:80',
            'lms_directory': '/home/pi/lms',
            'update_interval': 300,
            'web_server_enabled': True,
            'web_server_port': 80,
            'fullscreen': not args.no_fullscreen,
            'debug': args.debug
        }

        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default configuration: {config_path}")
        except Exception as e:
            print(f"Failed to create config: {e}")
            sys.exit(1)

    # Create and run application
    app = UnifiedKioskApp(config_path)

    # Override config with command line args
    if args.mode:
        app.config['mode'] = args.mode
        app.is_main_kiosk = args.mode == 'main'
    if args.device_id:
        app.config['device_id'] = args.device_id
    if args.debug:
        app.config['debug'] = True
    if args.no_fullscreen:
        app.config['fullscreen'] = False

    try:
        app.run()
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()