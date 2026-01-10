#!/usr/bin/env python3
"""
314Sign Main Kiosk Application for Raspberry Pi 4/5
Full-featured kiosk with framebuffer display, web server, and mobile access
Optimized for powerful hardware with comprehensive feature set
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
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import argparse
import signal
import sys
import hashlib
import tempfile
import socket
import psutil
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Import our hybrid system components
from render.lms_renderer import LMSRenderer
from render.background_cache import BackgroundCache
from lms.parser import LMSParser
from mobile_generator import MobileHTMLGenerator

# Import blockchain communication (placeholders ready for activation)
from blockchain_communicator import (
    BlockchainCommunicator,
    BlockchainContentManager,
    BlockchainDeviceManager,
    create_blockchain_communicator,
    enable_blockchain_features
)

# Import package system
from package_314sign import SignPackage, PackageError

class MainKioskApp:
    """
    Full-featured main kiosk application for Pi 4/5
    Combines framebuffer display, web server, mobile access, and admin interface
    """

    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Hardware detection and optimization
        self._detect_hardware()
        self._optimize_for_main_hardware()

        # Initialize core components
        self.display_size = self._get_display_size()
        self.renderer = LMSRenderer(self.display_size, quality='high')
        self.lms_parser = LMSParser()
        self.background_cache = BackgroundCache(
            kiosk_url=self.config.get('main_kiosk_url', 'http://localhost:80'),
            cache_size=1024 * 1024 * 1024  # 1GB cache for main kiosk
        )

        # Content management
        self.content_cache = {}
        self.current_content = None
        self.slideshow_state = {
            'current_slide': 0,
            'slide_start_time': 0,
            'paused': False
        }

        # Web server components
        self.flask_app = None
        self.web_thread = None
        self.mobile_clients = {}  # WebSocket connections for live updates

        # Remote management
        self.device_code = self.config.get('device_code', 'MAIN_KIOSK')
        self.managed_remotes = {}  # Remote displays this kiosk manages

        # State
        self.running = False
        self.display_thread = None
        self.content_thread = None

        # Setup directories
        self.cache_dir = Path(self.config.get('cache_dir', '/var/cache/314sign'))
        self.cache_dir.mkdir(exist_ok=True)
        self.web_root = Path(self.config.get('web_root', '/var/www/314sign'))
        self.web_root.mkdir(exist_ok=True, parents=True)

        # Initialize web server
        self._setup_web_server()

        # Initialize blockchain communication (placeholders ready for activation)
        self._setup_blockchain_communication()

        self.logger.info(f"Initialized Main Kiosk - Device: {self.device_code}")
        if not self.blockchain_comm.enabled:
            self.logger.info("Blockchain features ready for activation when implementation is complete")

    def _setup_blockchain_communication(self) -> None:
        """
        Setup blockchain communication placeholders
        Ready for activation when blockchain implementation is complete
        """
        # Initialize blockchain communicator (disabled by default)
        self.blockchain_comm = create_blockchain_communicator(
            node_id=self.device_code,
            enabled=self.config.get('blockchain_enabled', False)
        )

        # Initialize content manager
        self.blockchain_content_mgr = BlockchainContentManager(self.blockchain_comm)

        # Initialize device manager
        self.blockchain_device_mgr = BlockchainDeviceManager(self.blockchain_comm)

        # Register main kiosk on blockchain (placeholder)
        if self.blockchain_comm.enabled:
            self.blockchain_device_mgr.register_device(self.device_code, {
                'role': 'main_kiosk',
                'capabilities': ['content_serving', 'remote_management', 'web_access'],
                'hardware': self.hardware_info,
                'network_address': self.config.get('main_kiosk_url'),
                'managed_remotes': len(self.managed_remotes)
            })

        # Set up event callbacks for blockchain events
        self.blockchain_comm.add_event_callback('message_received', self._handle_blockchain_message)
        self.blockchain_comm.add_event_callback('content_updated', self._handle_content_update)
        self.blockchain_comm.add_event_callback('peer_connected', self._handle_peer_connected)

    def _handle_blockchain_message(self, message_data: Dict[str, Any]) -> None:
        """
        Handle incoming blockchain messages
        PLACEHOLDER: Ready for blockchain message processing
        """
        if not self.blockchain_comm.enabled:
            return

        message_type = message_data.get('type', 'unknown')
        sender = message_data.get('sender', 'unknown')

        self.logger.info(f"Blockchain message received: {message_type} from {sender}")

        # FUTURE: Process different message types
        # - Content updates from peers
        # - Remote management commands
        # - System coordination messages

    def _handle_content_update(self, update_data: Dict[str, Any]) -> None:
        """
        Handle blockchain content updates
        PLACEHOLDER: Ready for decentralized content updates
        """
        if not self.blockchain_comm.enabled:
            return

        content_id = update_data.get('content_id', 'unknown')
        self.logger.info(f"Blockchain content update: {content_id}")

        # FUTURE: Update local content cache from blockchain
        # - Check content versions
        # - Download updated content
        # - Refresh display if needed

    def _handle_peer_connected(self, peer_data: Dict[str, Any]) -> None:
        """
        Handle new blockchain peer connections
        PLACEHOLDER: Ready for peer discovery and management
        """
        if not self.blockchain_comm.enabled:
            return

        peer_id = peer_data.get('peer_id', 'unknown')
        peer_role = peer_data.get('role', 'unknown')

        self.logger.info(f"Blockchain peer connected: {peer_id} ({peer_role})")

        # FUTURE: Update peer registry
        # - Add to known nodes
        # - Update network status
        # - Coordinate content distribution

    def _get_content_info(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about content for blockchain registration
        PLACEHOLDER: Returns basic content info
        """
        # Try LMS content first
        lms_data = self._load_local_lms(content_id)
        if lms_data:
            return {
                'type': 'lms',
                'size': len(json.dumps(lms_data)),
                'hash': hashlib.sha256(json.dumps(lms_data, sort_keys=True).encode()).hexdigest()
            }

        # Try slideshow content
        slideshow_data = self._load_local_slideshow(content_id)
        if slideshow_data:
            return {
                'type': 'slideshow',
                'size': len(json.dumps(slideshow_data)),
                'hash': hashlib.sha256(json.dumps(slideshow_data, sort_keys=True).encode()).hexdigest()
            }

        return None

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load main kiosk configuration"""
        default_config = {
            'device_code': 'MAIN_KIOSK',
            'main_kiosk_url': f"http://{self._get_local_ip()}:80",
            'display_size': [1920, 1080],
            'orientation': 'landscape',
            'cache_dir': '/var/cache/314sign',
            'web_root': '/var/www/314sign',
            'web_port': 80,
            'admin_port': 8080,
            'mobile_enabled': True,
            'remote_management_enabled': True,
            'analytics_enabled': True,
            'debug': False
        }

        config_paths = [
            config_path,
            '/etc/314sign/main_kiosk.json',
            '/opt/314sign/main_kiosk.json'
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
        """Setup comprehensive logging for main kiosk"""
        level = logging.DEBUG if self.config.get('debug') else logging.INFO

        # Create logger with multiple handlers
        logger = logging.getLogger('main_kiosk')
        logger.setLevel(level)

        # File handler
        fh = logging.FileHandler('/var/log/314sign/main_kiosk.log')
        fh.setLevel(level)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def _detect_hardware(self) -> None:
        """Detect Raspberry Pi hardware capabilities"""
        self.hardware_info = {
            'model': 'unknown',
            'cpu_cores': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total // (1024 * 1024),  # MB
            'memory_available': psutil.virtual_memory().available // (1024 * 1024),  # MB
            'has_wifi': False,
            'gpu_memory': 0
        }

        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()

            if 'Raspberry Pi 5' in cpuinfo:
                self.hardware_info.update({
                    'model': 'pi5',
                    'has_wifi': True,
                    'gpu_memory': 512  # Configurable
                })
            elif 'Raspberry Pi 4' in cpuinfo:
                self.hardware_info.update({
                    'model': 'pi4',
                    'has_wifi': True,
                    'gpu_memory': 256  # Configurable
                })

        except Exception as e:
            self.logger.warning(f"Hardware detection failed: {e}")

    def _optimize_for_main_hardware(self) -> None:
        """Set optimizations for powerful Pi 4/5 hardware"""
        # Configure environment for high-performance framebuffer access
        os.environ['SDL_VIDEODRIVER'] = 'fbcon'
        os.environ['SDL_FBDEV'] = '/dev/fb0'
        os.environ['SDL_NOMOUSE'] = '1'
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '0'

        # High-quality rendering settings
        if self.hardware_info['memory_total'] >= 4096:  # 4GB+ RAM
            self.config['render_quality'] = 'ultra'
            self.config['max_cache_size'] = 2 * 1024 * 1024 * 1024  # 2GB
        elif self.hardware_info['memory_total'] >= 2048:  # 2GB+ RAM
            self.config['render_quality'] = 'high'
            self.config['max_cache_size'] = 1 * 1024 * 1024 * 1024  # 1GB
        else:
            self.config['render_quality'] = 'medium'
            self.config['max_cache_size'] = 512 * 1024 * 1024  # 512MB

        # GPU memory allocation
        gpu_mem = self.hardware_info.get('gpu_memory', 256)
        if gpu_mem > 0:
            try:
                with open('/boot/config.txt', 'r') as f:
                    config_content = f.read()
                if 'gpu_mem=' not in config_content:
                    with open('/boot/config.txt', 'a') as f:
                        f.write(f'\ngpu_mem={gpu_mem}\n')
            except:
                pass  # Ignore if we can't modify config

    def _get_display_size(self) -> Tuple[int, int]:
        """Get display size with orientation support"""
        base_size = self.config.get('display_size', [1920, 1080])
        orientation = self.config.get('orientation', 'landscape')

        width, height = base_size

        if orientation == 'portrait':
            return (height, width)
        else:
            return (width, height)

    def _setup_web_server(self) -> None:
        """Setup Flask web server for admin and mobile access"""
        self.flask_app = Flask(__name__,
                              template_folder=str(self.web_root / 'templates'),
                              static_folder=str(self.web_root / 'static'))

        CORS(self.flask_app)

        # Register routes
        self._register_web_routes()

        # Create web directories
        (self.web_root / 'templates').mkdir(exist_ok=True)
        (self.web_root / 'static' / 'css').mkdir(exist_ok=True, parents=True)
        (self.web_root / 'static' / 'js').mkdir(exist_ok=True, parents=True)

    def _register_web_routes(self) -> None:
        """Register Flask routes for web interface"""
        app = self.flask_app

        @app.route('/')
        def index():
            return render_template('index.html',
                                 device_code=self.device_code,
                                 hardware=self.hardware_info,
                                 config=self.config)

        @app.route('/mobile')
        def mobile():
            # Generate mobile-optimized view of current content
            current_content = self._get_current_content_data()
            return render_template('mobile.html',
                                 content=current_content,
                                 timestamp=time.time())

        @app.route('/admin')
        def admin():
            return render_template('admin.html',
                                 device_code=self.device_code,
                                 remotes=self.managed_remotes,
                                 stats=self._get_system_stats())

        @app.route('/api/current-content')
        def api_current_content():
            return jsonify(self._get_current_content_data())

        @app.route('/api/stats')
        def api_stats():
            return jsonify(self._get_system_stats())

        @app.route('/api/remotes')
        def api_remotes():
            return jsonify({
                'remotes': self.managed_remotes,
                'count': len(self.managed_remotes)
            })

        # ============================================================================
        # BLOCKCHAIN PLACEHOLDER ENDPOINTS - Ready for activation
        # ============================================================================

        @app.route('/api/blockchain/status')
        def blockchain_status():
            """Get blockchain network status"""
            if not hasattr(self, 'blockchain_comm'):
                return jsonify({'enabled': False, 'message': 'Blockchain not initialized'})

            status = self.blockchain_comm.get_status()
            # Add main kiosk specific info
            status.update({
                'managed_remotes': len(self.managed_remotes),
                'device_role': 'main_kiosk',
                'content_distribution_ready': self.blockchain_content_mgr is not None
            })
            return jsonify(status)

        @app.route('/api/blockchain/enable-feature/<feature>')
        def enable_blockchain_feature(feature):
            """Enable specific blockchain feature for gradual rollout"""
            if not hasattr(self, 'blockchain_comm'):
                return jsonify({'success': False, 'error': 'Blockchain not initialized'})

            if feature in ['message_passing', 'content_distribution', 'device_authentication', 'token_gating', 'mining_rewards']:
                self.blockchain_comm.enable_feature(feature)
                return jsonify({'success': True, 'feature': feature, 'enabled': True})
            else:
                return jsonify({'success': False, 'error': f'Unknown feature: {feature}'})

        @app.route('/api/blockchain/register-content/<content_id>')
        def register_content_blockchain(content_id):
            """Register content on blockchain (placeholder)"""
            if not hasattr(self, 'blockchain_comm') or not self.blockchain_content_mgr:
                return jsonify({'success': False, 'error': 'Blockchain content management not available'})

            # Get content info
            content_info = self._get_content_info(content_id)
            if not content_info:
                return jsonify({'success': False, 'error': f'Content not found: {content_id}'})

            # Register on blockchain (placeholder)
            registration_id = self.blockchain_comm.register_content(
                content_id,
                content_info.get('type', 'unknown'),
                {
                    'size': content_info.get('size', 0),
                    'hash': content_info.get('hash', ''),
                    'timestamp': time.time(),
                    'device': self.device_code
                }
            )

            if registration_id:
                return jsonify({
                    'success': True,
                    'content_id': content_id,
                    'registration_id': registration_id,
                    'blockchain_registered': self.blockchain_comm.enabled
                })
            else:
                return jsonify({'success': False, 'error': 'Blockchain registration failed'})

        @app.route('/api/blockchain/devices')
        def blockchain_devices():
            """Get blockchain-registered devices"""
            if not hasattr(self, 'blockchain_device_mgr'):
                return jsonify({'devices': [], 'message': 'Device management not available'})

            devices = list(self.blockchain_device_mgr.device_registry.keys())
            return jsonify({
                'devices': devices,
                'count': len(devices),
                'blockchain_enabled': self.blockchain_comm.enabled if hasattr(self, 'blockchain_comm') else False
            })

        @app.route('/api/blockchain/messages')
        def blockchain_messages():
            """Get pending blockchain messages"""
            if not hasattr(self, 'blockchain_comm'):
                return jsonify({'messages': [], 'message': 'Blockchain messaging not available'})

            messages = self.blockchain_comm.receive_messages()
            return jsonify({
                'messages': messages,
                'count': len(messages),
                'blockchain_enabled': self.blockchain_comm.enabled
            })

        @app.route('/api/blockchain/wallet')
        def blockchain_wallet():
            """Get blockchain wallet status"""
            if not hasattr(self, 'blockchain_comm'):
                return jsonify({'balance': 0, 'message': 'Blockchain wallet not available'})

            wallet_info = self.blockchain_comm.get_wallet_balance()
            return jsonify(wallet_info)

    def _get_local_ip(self) -> str:
        """Get local IP address for web server"""
        try:
            # Get the local IP that would be used to reach the internet
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "localhost"

    def _get_current_content_data(self) -> Dict[str, Any]:
        """Get data about currently displayed content"""
        return {
            'type': self.current_content.get('type', 'standby') if self.current_content else 'standby',
            'content': self.current_content,
            'slideshow_state': self.slideshow_state if self.current_content else None,
            'timestamp': time.time(),
            'device': self.device_code
        }

    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for monitoring"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': self.hardware_info['memory_total'],
                'available': psutil.virtual_memory().available // (1024 * 1024),
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total // (1024 * 1024 * 1024),
                'free': psutil.disk_usage('/').free // (1024 * 1024 * 1024),
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'connections': len(psutil.net_connections()),
                'interfaces': list(psutil.net_if_addrs().keys())
            },
            'uptime': time.time() - psutil.boot_time(),
            'temperature': self._get_cpu_temperature()
        }

    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0
            return temp
        except:
            return None

    def setup_framebuffer_display(self) -> pygame.Surface:
        """Initialize pygame with high-quality framebuffer display"""
        pygame.init()

        try:
            # Try direct framebuffer access first
            screen = pygame.display.set_mode(self.display_size, pygame.FULLSCREEN)
            self.logger.info(f"Initialized high-quality framebuffer display: {self.display_size}")
        except Exception as e:
            self.logger.error(f"Failed direct framebuffer: {e}")
            # Fallback for development
            self.logger.info("Attempting fallback display mode...")
            del os.environ['SDL_VIDEODRIVER']
            screen = pygame.display.set_mode(self.display_size)
            self.logger.info("Using fallback display mode")

        pygame.display.set_caption(f"314Sign Main Kiosk - {self.device_code}")
        return screen

    def start(self) -> None:
        """Start the main kiosk application"""
        self.running = True
        self.logger.info("Starting 314Sign Main Kiosk Application")

        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Start web server
            if self.config.get('web_enabled', True):
                self.web_thread = threading.Thread(target=self._run_web_server, daemon=True)
                self.web_thread.start()

            # Start content management thread
            self.content_thread = threading.Thread(target=self._content_management_loop, daemon=True)
            self.content_thread.start()

            # Start main display loop
            self._display_loop()

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            self.cleanup()

    def _run_web_server(self) -> None:
        """Run Flask web server in background thread"""
        try:
            port = self.config.get('web_port', 80)
            self.logger.info(f"Starting web server on port {port}")
            self.flask_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        except Exception as e:
            self.logger.error(f"Web server error: {e}")

    def _content_management_loop(self) -> None:
        """Background thread for content management and remote coordination"""
        while self.running:
            try:
                # Update remote displays
                if self.config.get('remote_management_enabled'):
                    self._update_remote_displays()

                # Collect analytics
                if self.config.get('analytics_enabled'):
                    self._collect_analytics()

                # Clean up old cache
                self._cleanup_cache()

                time.sleep(30)  # Run every 30 seconds

            except Exception as e:
                self.logger.error(f"Content management error: {e}")
                time.sleep(60)

    def _update_remote_displays(self) -> None:
        """Update managed remote displays with current content"""
        # This would coordinate with remote displays
        # Implementation depends on remote management system
        pass

    def _collect_analytics(self) -> None:
        """Collect and store system analytics"""
        # Implementation for analytics collection
        pass

    def _cleanup_cache(self) -> None:
        """Clean up old cached content"""
        try:
            max_age = 24 * 60 * 60  # 24 hours
            current_time = time.time()

            for cache_file in self.cache_dir.glob("*"):
                if cache_file.is_file():
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > max_age:
                        cache_file.unlink()
                        self.logger.debug(f"Cleaned up old cache file: {cache_file}")

        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")

    def _display_loop(self) -> None:
        """Main display rendering loop with high performance"""
        screen = self.setup_framebuffer_display()

        self.logger.info("Starting main display loop")

        while self.running:
            try:
                current_time = time.time()

                # Update content (main kiosk can generate its own content)
                self._update_display_content()

                # Render current content
                surface = self._render_current_content()
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
                        elif event.key == pygame.K_F12:  # Admin key combo
                            self._open_admin_interface()

                # Small delay for high-performance rendering
                time.sleep(0.016)  # ~60 FPS

            except Exception as e:
                self.logger.error(f"Display loop error: {e}")
                time.sleep(1)  # Wait before retry

        pygame.quit()

    def _update_display_content(self) -> None:
        """Update display content based on schedule or remote management"""
        # Implementation for content scheduling
        # For now, use static content or polling
        pass

    def _render_current_content(self) -> Optional[pygame.Surface]:
        """Render the current content based on configuration"""
        mode = self.config.get('display_mode', 'standby')

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
        """Render LMS content with high quality"""
        lms_name = self.config.get('current_lms', 'default-menu')
        if not lms_name:
            return self._render_standby_screen()

        # Check cache first
        cache_key = f"lms_{lms_name}"
        if cache_key in self.content_cache:
            cached_data = self.content_cache[cache_key]
            if time.time() - cached_data['timestamp'] < 1800:  # 30 min cache
                return self.renderer.render_lms_to_surface(cached_data['data'])

        # Load and parse LMS file
        try:
            lms_data = self._load_local_lms(lms_name)
            if lms_data:
                self.content_cache[cache_key] = {
                    'data': lms_data,
                    'timestamp': time.time()
                }

                self._ensure_background_images(lms_data)
                return self.renderer.render_lms_to_surface(lms_data)

        except Exception as e:
            self.logger.error(f"Failed to render LMS {lms_name}: {e}")

        return self._render_standby_screen()

    def _render_slideshow_content(self) -> Optional[pygame.Surface]:
        """Render slideshow content with smooth transitions"""
        slideshow_name = self.config.get('current_slideshow', 'default-slides')
        if not slideshow_name:
            return self._render_standby_screen()

        # Check cache
        cache_key = f"slideshow_{slideshow_name}"
        if cache_key not in self.content_cache:
            try:
                slideshow_data = self._load_local_slideshow(slideshow_name)
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

        # Handle slide transitions with timing
        current_time = time.time() * 1000  # milliseconds
        current_slide = self.slideshow_state['current_slide']
        slide_start_time = self.slideshow_state['slide_start_time']

        if not self.slideshow_state['paused']:
            slide_duration = slides[current_slide].get('duration', 5000)
            transition_duration = slides[current_slide].get('transitionDuration', 1000)

            if current_time - slide_start_time >= slide_duration:
                # Advance to next slide
                self.slideshow_state['current_slide'] = (current_slide + 1) % len(slides)
                self.slideshow_state['slide_start_time'] = current_time

        # Render current slide with high quality
        slide = slides[self.slideshow_state['current_slide']]
        return self._render_slide(slide, slideshow_data)

    def _render_slide(self, slide: Dict[str, Any], slideshow_data: Dict[str, Any]) -> pygame.Surface:
        """Render a single slideshow slide with high quality"""
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

        # Render elements if they exist
        if slide.get('elements'):
            for element in slide['elements']:
                self._render_slide_element(surface, element)

        return surface

    def _render_slide_element(self, surface: pygame.Surface, element: Dict[str, Any]) -> None:
        """Render a slide element (text, image, shape)"""
        element_type = element.get('type', 'text')

        if element_type == 'text':
            self._render_slide_text_element(surface, element)
        elif element_type == 'image':
            self._render_slide_image_element(surface, element)
        elif element_type == 'shape':
            self._render_slide_shape_element(surface, element)

    def _render_slide_text_element(self, surface: pygame.Surface, element: Dict[str, Any]) -> None:
        """Render text element on slide"""
        content = element.get('content', '')
        x, y = element.get('x', 100), element.get('y', 100)
        font_size = element.get('fontSize', 24)
        color = self._parse_color(element.get('color', '#ffffff'))

        try:
            font = pygame.font.SysFont('Arial', font_size)
            text_surface = font.render(content, True, color)

            # Apply opacity if specified
            if element.get('opacity', 1.0) < 1.0:
                text_surface.set_alpha(int(255 * element['opacity']))

            surface.blit(text_surface, (x, y))

        except Exception as e:
            self.logger.error(f"Failed to render slide text element: {e}")

    def _render_slide_image_element(self, surface: pygame.Surface, element: Dict[str, Any]) -> None:
        """Render image element on slide"""
        # Implementation similar to main image rendering but for elements
        pass

    def _render_slide_shape_element(self, surface: pygame.Surface, element: Dict[str, Any]) -> None:
        """Render shape element on slide"""
        # Implementation for rectangles, circles, etc.
        pass

    def _render_text_slide(self, surface: pygame.Surface, slide: Dict[str, Any]) -> None:
        """Render text-based slide with high quality"""
        content = slide.get('content', '')
        font_size = slide.get('fontSize', 8)  # percentage for main slides
        font_family = slide.get('font', 'Lato, sans-serif')
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
        """Render image-based slide with high quality"""
        media_path = slide.get('media', '')
        if not media_path:
            return

        try:
            # Check if it's a remote URL or local path
            if media_path.startswith('http'):
                cached_path = self._download_and_cache_media(media_path)
                if cached_path:
                    image = pygame.image.load(str(cached_path))
                else:
                    return
            else:
                image = pygame.image.load(media_path)

            # Scale image to fit display while maintaining aspect ratio
            img_width, img_height = image.get_size()
            scale_factor = min(self.display_size[0] / img_width, self.display_size[1] / img_height)

            if scale_factor < 1.0:
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                image = pygame.transform.smoothscale(image, (new_width, new_height))

            # Center the image
            x = (self.display_size[0] - image.get_width()) // 2
            y = (self.display_size[1] - image.get_height()) // 2

            surface.blit(image, (x, y))

        except Exception as e:
            self.logger.error(f"Failed to render image slide: {e}")

    def _render_video_slide(self, surface: pygame.Surface, slide: Dict[str, Any]) -> None:
        """Render video-based slide (placeholder)"""
        slide['content'] = f"Video: {slide.get('media', 'Unknown')}"
        slide['type'] = 'text'
        self._render_text_slide(surface, slide)

    def _render_standby_screen(self) -> pygame.Surface:
        """Render standby screen with system info"""
        surface = pygame.Surface(self.display_size)
        surface.fill((0, 20, 40))  # Dark blue

        standby_text = [
            "314Sign Main Kiosk",
            f"Device: {self.device_code}",
            f"Status: Active",
            "",
            f"CPU: {psutil.cpu_percent()}%",
            f"Memory: {psutil.virtual_memory().percent}%",
            "",
            f"Time: {time.strftime('%H:%M:%S')}",
            "",
            "Ready for content..."
        ]

        y_offset = self.display_size[1] // 2 - 150

        for line in standby_text:
            if line.strip():
                try:
                    font = pygame.font.SysFont('Arial', 24)
                    text_surface = font.render(line, True, (255, 255, 255))
                    text_rect = text_surface.get_rect(
                        centerx=self.display_size[0] // 2,
                        centery=y_offset
                    )
                    surface.blit(text_surface, text_rect)
                except:
                    pass
            y_offset += 35

        return surface

    def _load_local_lms(self, lms_name: str) -> Optional[Dict[str, Any]]:
        """Load LMS content from local storage"""
        try:
            lms_dir = Path(self.config.get('lms_dir', '/opt/314sign/lms'))
            lms_file = lms_dir / f"{lms_name}.lms"

            if lms_file.exists():
                with open(lms_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.lms_parser.parse_string(content)

        except Exception as e:
            self.logger.error(f"Failed to load local LMS {lms_name}: {e}")

        return None

    def _load_local_slideshow(self, slideshow_name: str) -> Optional[Dict[str, Any]]:
        """Load slideshow content from local storage"""
        try:
            slideshow_dir = Path(self.config.get('slideshow_dir', '/opt/314sign/slideshows'))
            slideshow_file = slideshow_dir / f"{slideshow_name}.json"

            if slideshow_file.exists():
                with open(slideshow_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        except Exception as e:
            self.logger.error(f"Failed to load local slideshow {slideshow_name}: {e}")

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
        """Download and cache media file"""
        try:
            url_hash = hashlib.md5(media_url.encode()).hexdigest()
            cache_path = self.cache_dir / f"media_{url_hash}"

            if cache_path.exists():
                return cache_path

            response = requests.get(media_url, timeout=60, stream=True)
            response.raise_for_status()

            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Cached media: {media_url} -> {cache_path}")
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

        named_colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
        }

        return named_colors.get(color_str.lower(), (255, 255, 255))

    def _open_admin_interface(self) -> None:
        """Open admin interface (for development/debugging)"""
        try:
            # Open admin interface in browser
            admin_url = f"http://localhost:{self.config.get('admin_port', 8080)}/admin"
            subprocess.run(['xdg-open', admin_url], check=False)
        except:
            pass

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources"""
        self.logger.info("Cleaning up main kiosk resources...")
        self.renderer.cleanup()

        # Clear cache if needed
        if self.config.get('clear_cache_on_exit'):
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
            except:
                pass

        self.logger.info("Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description='314Sign Main Kiosk')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--device-code', help='Override device code')
    parser.add_argument('--web-port', type=int, help='Web server port')
    parser.add_argument('--no-web', action='store_true', help='Disable web server')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Create main kiosk instance
    kiosk = MainKioskApp(args.config)

    # Override config with command line args
    if args.device_code:
        kiosk.config['device_code'] = args.device_code
        kiosk.device_code = args.device_code
    if args.web_port:
        kiosk.config['web_port'] = args.web_port
    if args.no_web:
        kiosk.config['web_enabled'] = False
    if args.debug:
        kiosk.config['debug'] = True
        kiosk.logger.setLevel(logging.DEBUG)

    try:
        kiosk.start()
    except KeyboardInterrupt:
        print("Main kiosk stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()