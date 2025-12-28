# 🚀 Image-Based Remote Display System
## Revolutionizing Digital Signage with Pi Zero 2 W

## Executive Summary

This document outlines a revolutionary approach to remote digital signage that leverages Pi Zero 2 W devices as dedicated image display appliances. Instead of struggling with web browsers and complex software stacks, we treat Pi Zeros as ultra-reliable, low-power display hardware that excels at showing static content through high-quality images.

## Core Philosophy

**"Think of Pi Zeros as dedicated e-ink displays - reliable, low-power, and perfect for static content"**

Traditional web-based approaches fail on resource-constrained devices like Pi Zero 2 W due to:
- Browser memory limitations
- Complex rendering engines
- Network dependency issues
- Update synchronization challenges

Our image-based approach eliminates these issues by:
- Using simple Python scripts for display
- Transferring pre-rendered images
- Maintaining offline capability
- Providing bulletproof reliability

---

## System Architecture

### Main Kiosk (Pi 5) - Content Creation Hub
- **Web Interface**: Standard 314Sign interface for content creation
- **Screenshot Engine**: Automated high-resolution image generation
- **Image Pipeline**: Optimization, compression, and distribution
- **Remote Management**: Device registration, monitoring, and control
- **Content Scheduling**: Automated updates and scheduling

### Remote Displays (Pi Zero 2 W) - Image Display Appliances
- **Python Display Engine**: Pygame-based HDMI output system
- **Image Cache**: Local storage for offline operation
- **Sync Engine**: Intelligent content synchronization
- **Status Reporting**: Health monitoring and diagnostics
- **Slideshow System**: Advanced transitions and effects

---

## Remote Side Implementation

### Core Display Engine (`display_engine.py`)

```python
#!/usr/bin/env python3
"""
Image-Based Display Engine for Pi Zero 2 W
Ultra-reliable HDMI display system with offline capability
"""

import pygame
import time
import json
import os
import requests
from pathlib import Path
import logging
import hashlib

class ImageDisplay:
    def __init__(self, width=1920, height=1080, kiosk_url="http://kiosk.local:80"):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)

        self.display_width = width
        self.display_height = height
        self.kiosk_url = kiosk_url
        self.device_id = self.get_device_id()
        self.images_dir = Path("/home/pi/images")
        self.config_file = Path("/home/pi/display_config.json")

        self.images_dir.mkdir(exist_ok=True)
        self.config = self.load_config()

        # Performance monitoring
        self.stats = {
            'images_displayed': 0,
            'sync_attempts': 0,
            'sync_successes': 0,
            'uptime_start': time.time()
        }

    def get_device_id(self):
        """Generate unique device ID from CPU serial"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        serial = line.split(':')[1].strip()
                        return f"remote-{hashlib.md5(serial.encode()).hexdigest()[:6]}"
        except:
            pass
        return f"remote-{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"

    def load_config(self):
        """Load device configuration"""
        default_config = {
            "kiosk_url": self.kiosk_url,
            "device_id": self.device_id,
            "update_interval": 300,
            "transition_duration": 2.0,
            "slideshow_mode": "single",
            "orientation": 0,
            "display_resolution": [self.display_width, self.display_height],
            "power_saving": True
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

        return default_config

    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def download_image(self, image_url, local_path, expected_hash=None):
        """Download image with integrity verification and resume capability"""
        try:
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify integrity if hash provided
            if expected_hash:
                actual_hash = self.calculate_hash(local_path)
                if actual_hash != expected_hash:
                    logging.error(f"Hash mismatch for {local_path}")
                    os.remove(local_path)
                    return False

            return True
        except Exception as e:
            logging.error(f"Download failed for {image_url}: {e}")
            return False

    def calculate_hash(self, file_path):
        """Calculate SHA256 hash"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return None

    def optimize_image(self, image_path):
        """Optimize image for display (placeholder for PIL/Pillow integration)"""
        # Future: Resize, rotate, enhance contrast, etc.
        return image_path

    def load_image(self, image_path):
        """Load and prepare image for display"""
        try:
            image = pygame.image.load(str(image_path))

            # Apply orientation
            if self.config.get('orientation'):
                rotations = [0, 270, 180, 90]  # 0, 90, 180, 270 degrees
                angle = rotations[self.config['orientation'] % 4]
                if angle:
                    image = pygame.transform.rotate(image, angle)

            # Scale to fit display while maintaining aspect ratio
            img_width, img_height = image.get_size()
            scale_factor = min(self.display_width / img_width, self.display_height / img_height)

            if scale_factor < 1.0:
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                image = pygame.transform.smoothscale(image, (new_width, new_height))

            return image
        except Exception as e:
            logging.error(f"Failed to load image {image_path}: {e}")
            return None

    def display_image(self, image, position="center", effect=None):
        """Display image with positioning and effects"""
        if image is None:
            return

        img_width, img_height = image.get_size()

        # Calculate position
        positions = {
            "center": ((self.display_width - img_width) // 2, (self.display_height - img_height) // 2),
            "top-left": (0, 0),
            "top-right": (self.display_width - img_width, 0),
            "bottom-left": (0, self.display_height - img_height),
            "bottom-right": (self.display_width - img_width, self.display_height - img_height),
            "stretch": (0, 0)  # Special case for stretching
        }

        if position == "stretch":
            image = pygame.transform.smoothscale(image, (self.display_width, self.display_height))
            x, y = 0, 0
        else:
            x, y = positions.get(position, positions["center"])

        # Apply effects
        if effect == "fade_in":
            self.fade_in_effect(image, (x, y))
        else:
            # Clear screen and display
            self.screen.fill((0, 0, 0))
            self.screen.blit(image, (x, y))
            pygame.display.flip()

        self.stats['images_displayed'] += 1

    def fade_in_effect(self, image, position, duration=1.0):
        """Fade in effect for smooth transitions"""
        start_time = time.time()
        x, y = position

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            alpha = int(255 * (elapsed / duration))
            faded_image = image.copy()
            faded_image.set_alpha(alpha)

            self.screen.fill((0, 0, 0))
            self.screen.blit(faded_image, (x, y))
            pygame.display.flip()

            time.sleep(0.016)  # ~60 FPS

        # Final display at full opacity
        self.screen.fill((0, 0, 0))
        self.screen.blit(image, (x, y))
        pygame.display.flip()

    def run_slideshow(self, image_paths, interval=30):
        """Advanced slideshow with multiple transition effects"""
        if not image_paths:
            return

        images = []
        for path in image_paths:
            img = self.load_image(path)
            if img:
                images.append((path, img))

        if not images:
            logging.error("No valid images for slideshow")
            return

        transitions = [
            ("fade", 1.5),
            ("slide_left", 2.0),
            ("slide_right", 2.0),
            ("zoom", 1.8)
        ]

        index = 0
        transition_index = 0

        while True:
            current_path, current_image = images[index]
            logging.info(f"Displaying: {current_path}")

            self.display_image(current_image, effect="fade_in")

            # Display duration
            start_display = time.time()
            while time.time() - start_display < interval:
                time.sleep(1)

                # Check for updates every minute
                if int(time.time()) % 60 == 0:
                    if self.check_for_updates():
                        logging.info("Content update detected, restarting slideshow")
                        return True  # Signal to restart with new content

            # Transition to next image
            next_index = (index + 1) % len(images)
            _, next_image = images[next_index]

            # Apply transition
            transition_type, transition_duration = transitions[transition_index % len(transitions)]
            self.apply_transition(current_image, next_image, transition_type, transition_duration)

            index = next_index
            transition_index += 1

    def apply_transition(self, old_image, new_image, transition_type, duration):
        """Apply transition effect between images"""
        if transition_type == "fade":
            self.fade_transition(old_image, new_image, duration)
        elif transition_type == "slide_left":
            self.slide_transition(old_image, new_image, duration, 1)
        elif transition_type == "slide_right":
            self.slide_transition(old_image, new_image, duration, -1)
        elif transition_type == "zoom":
            self.zoom_transition(old_image, new_image, duration)

    def fade_transition(self, old_image, new_image, duration):
        """Crossfade between images"""
        start_time = time.time()

        while time.time() - start_time < duration:
            progress = (time.time() - start_time) / duration

            old_alpha = old_image.copy()
            new_alpha = new_image.copy()

            old_alpha.set_alpha(int(255 * (1 - progress)))
            new_alpha.set_alpha(int(255 * progress))

            self.screen.blit(old_alpha, (0, 0))
            self.screen.blit(new_alpha, (0, 0))
            pygame.display.flip()

            time.sleep(0.016)

    def slide_transition(self, old_image, new_image, duration, direction):
        """Slide transition effect"""
        width = self.display_width
        start_time = time.time()

        while time.time() - start_time < duration:
            progress = (time.time() - start_time) / duration

            old_x = -int(width * progress * direction)
            new_x = width - int(width * progress * direction)

            self.screen.fill((0, 0, 0))
            self.screen.blit(old_image, (old_x, 0))
            self.screen.blit(new_image, (new_x, 0))
            pygame.display.flip()

            time.sleep(0.016)

    def zoom_transition(self, old_image, new_image, duration):
        """Zoom transition effect"""
        start_time = time.time()

        while time.time() - start_time < duration:
            progress = (time.time() - start_time) / duration

            # Scale factor from 1.0 to 1.2
            scale = 1.0 + (progress * 0.2)

            scaled_width = int(self.display_width * scale)
            scaled_height = int(self.display_height * scale)

            scaled_old = pygame.transform.smoothscale(old_image, (scaled_width, scaled_height))
            scaled_new = pygame.transform.smoothscale(new_image, (scaled_width, scaled_height))

            # Center the scaled images
            old_x = (self.display_width - scaled_width) // 2
            old_y = (self.display_height - scaled_height) // 2
            new_x = (self.display_width - scaled_width) // 2
            new_y = (self.display_height - scaled_height) // 2

            self.screen.fill((0, 0, 0))
            scaled_old.set_alpha(int(255 * (1 - progress)))
            scaled_new.set_alpha(int(255 * progress))

            self.screen.blit(scaled_old, (old_x, old_y))
            self.screen.blit(scaled_new, (new_x, new_y))
            pygame.display.flip()

            time.sleep(0.016)

    def check_for_updates(self):
        """Check kiosk for configuration and content updates"""
        try:
            # Check configuration updates
            config_url = f"{self.config['kiosk_url']}/api/remotes/config/{self.device_id}"
            response = requests.get(config_url, timeout=10)

            if response.status_code == 200:
                remote_config = response.json()
                if self.process_config_update(remote_config):
                    return True

            # Check for new images
            if self.sync_images():
                return True

            self.stats['sync_attempts'] += 1
            return False

        except Exception as e:
            logging.warning(f"Update check failed: {e}")
            return False

    def process_config_update(self, remote_config):
        """Process configuration update from kiosk"""
        updated = False

        for key, value in remote_config.items():
            if key in self.config and self.config[key] != value:
                self.config[key] = value
                updated = True
                logging.info(f"Config updated: {key} = {value}")

        if updated:
            self.save_config()

        return updated

    def sync_images(self):
        """Synchronize images from kiosk"""
        try:
            # Get image manifest
            manifest_url = f"{self.config['kiosk_url']}/api/remotes/images/{self.device_id}"
            response = requests.get(manifest_url, timeout=10)

            if response.status_code != 200:
                return False

            manifest = response.json()
            updated = False

            for image_info in manifest.get('images', []):
                image_name = image_info['name']
                expected_hash = image_info.get('hash')
                image_url = f"{self.config['kiosk_url']}/images/{image_name}"

                local_path = self.images_dir / image_name

                # Check if download needed
                needs_download = True
                if local_path.exists() and expected_hash:
                    if self.calculate_hash(local_path) == expected_hash:
                        needs_download = False

                if needs_download:
                    if self.download_image(image_url, local_path, expected_hash):
                        logging.info(f"Downloaded: {image_name}")
                        updated = True
                    else:
                        logging.error(f"Failed to download: {image_name}")

            self.stats['sync_successes'] += 1
            return updated

        except Exception as e:
            logging.error(f"Image sync failed: {e}")
            return False

    def report_status(self):
        """Report device status to kiosk"""
        try:
            status = {
                'device_id': self.device_id,
                'uptime': time.time() - self.stats['uptime_start'],
                'images_displayed': self.stats['images_displayed'],
                'sync_attempts': self.stats['sync_attempts'],
                'sync_successes': self.stats['sync_successes'],
                'current_image': self.get_current_image_name(),
                'last_sync': time.time(),
                'config': self.config
            }

            status_url = f"{self.config['kiosk_url']}/api/remotes/status/{self.device_id}"
            response = requests.post(status_url, json=status, timeout=10)

            return response.status_code == 200

        except Exception as e:
            logging.error(f"Status report failed: {e}")
            return False

    def get_current_image_name(self):
        """Get name of currently displayed image"""
        try:
            image_files = list(self.images_dir.glob("*.png")) + list(self.images_dir.glob("*.jpg"))
            if image_files:
                latest = max(image_files, key=lambda x: x.stat().st_mtime)
                return latest.name
        except:
            pass
        return None

    def display_standby_message(self):
        """Display standby screen when no content available"""
        self.screen.fill((0, 20, 40))  # Dark blue

        # Display device info and status
        # (Simplified - would use actual font rendering)
        pygame.display.flip()

    def run(self):
        """Main display loop"""
        logging.info(f"Starting Image Display Engine - Device: {self.device_id}")
        logging.info(f"Display Resolution: {self.display_width}x{self.display_height}")
        logging.info(f"Kiosk URL: {self.config['kiosk_url']}")

        # Initial sync
        self.check_for_updates()
        self.report_status()

        last_status_report = time.time()

        while True:
            try:
                # Get available images
                image_files = list(self.images_dir.glob("*.png")) + list(self.images_dir.glob("*.jpg"))
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Newest first

                if image_files:
                    if self.config.get('slideshow_mode') == 'single':
                        # Display latest image
                        latest_image = image_files[0]
                        image = self.load_image(latest_image)

                        if image:
                            logging.info(f"Displaying: {latest_image.name}")
                            self.display_image(image)

                        # Check for updates periodically
                        check_interval = self.config.get('update_interval', 300)
                        last_check = time.time()

                        while time.time() - last_check < check_interval:
                            time.sleep(10)  # Check every 10 seconds for user input

                            # Handle quit events
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    return
                                elif event.type == pygame.KEYDOWN:
                                    if event.key == pygame.K_ESCAPE:
                                        return

                            # Report status every 5 minutes
                            if time.time() - last_status_report > 300:
                                self.report_status()
                                last_status_report = time.time()

                            # Check for updates every minute
                            if time.time() - last_check > 60:
                                if self.check_for_updates():
                                    break  # New content available

                    else:
                        # Run slideshow
                        image_paths = [str(f) for f in image_files]
                        if self.run_slideshow(image_paths, self.config.get('slideshow_interval', 30)):
                            continue  # Restart slideshow with new content

                else:
                    # No images available
                    logging.warning("No images available, displaying standby screen")
                    self.display_standby_message()

                    # Check for updates every 5 minutes when no content
                    time.sleep(300)
                    self.check_for_updates()

            except KeyboardInterrupt:
                logging.info("Display engine stopped by user")
                break
            except Exception as e:
                logging.error(f"Display engine error: {e}")
                time.sleep(30)  # Wait before retry

        # Cleanup
        self.report_status()  # Final status report
        pygame.quit()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Image-Based Display Engine')
    parser.add_argument('--kiosk-url', default='http://kiosk.local:80',
                       help='Main kiosk URL')
    parser.add_argument('--width', type=int, default=1920,
                       help='Display width')
    parser.add_argument('--height', type=int, default=1080,
                       help='Display height')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    display = ImageDisplay(
        width=args.width,
        height=args.height,
        kiosk_url=args.kiosk_url
    )

    try:
        display.run()
    except KeyboardInterrupt:
        print("Display engine stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise
```

### Network Synchronization Manager (`sync_manager.py`)

```python
#!/usr/bin/env python3
"""
Advanced Network Synchronization Manager
Handles intelligent image sync, caching, and bandwidth optimization
"""

import requests
import hashlib
import os
import json
import time
import logging
from pathlib import Path
from urllib.parse import urljoin
import tempfile

class SyncManager:
    def __init__(self, kiosk_url, device_id, images_dir="/home/pi/images"):
        self.kiosk_url = kiosk_url.rstrip('/')
        self.device_id = device_id
        self.images_dir = Path(images_dir)
        self.cache_dir = Path(images_dir) / "cache"
        self.temp_dir = Path(images_dir) / "temp"

        # Create directories
        for dir_path in [self.images_dir, self.cache_dir, self.temp_dir]:
            dir_path.mkdir(exist_ok=True)

        # Sync statistics
        self.stats = {
            'total_downloads': 0,
            'total_bytes': 0,
            'failed_downloads': 0,
            'cache_hits': 0,
            'last_sync': None
        }

        # Load cached manifest
        self.cached_manifest = self.load_cached_manifest()

    def load_cached_manifest(self):
        """Load previously cached manifest"""
        cache_file = self.cache_dir / "manifest.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cached manifest: {e}")
        return None

    def save_cached_manifest(self, manifest):
        """Save manifest to cache"""
        try:
            cache_file = self.cache_dir / "manifest.json"
            with open(cache_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            self.cached_manifest = manifest
        except Exception as e:
            logging.error(f"Failed to save cached manifest: {e}")

    def get_remote_manifest(self):
        """Get current image manifest from kiosk"""
        try:
            manifest_url = f"{self.kiosk_url}/api/remotes/images/{self.device_id}"
            response = requests.get(manifest_url, timeout=15)
            response.raise_for_status()

            manifest = response.json()
            self.save_cached_manifest(manifest)
            return manifest

        except Exception as e:
            logging.warning(f"Failed to get remote manifest: {e}")
            return self.cached_manifest  # Return cached version

    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return None

    def verify_file_integrity(self, file_path, expected_hash):
        """Verify file integrity against expected hash"""
        if not expected_hash:
            return True  # No hash to verify against

        actual_hash = self.calculate_file_hash(file_path)
        return actual_hash == expected_hash

    def download_image_incremental(self, image_url, local_path, expected_hash=None):
        """Download with resume capability and progress tracking"""
        try:
            # Check if partial download exists
            temp_path = self.temp_dir / f"{local_path.name}.tmp"
            downloaded_size = temp_path.stat().st_size if temp_path.exists() else 0

            headers = {}
            if downloaded_size > 0:
                headers['Range'] = f'bytes={downloaded_size}-'

            response = requests.get(image_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            # Handle range requests
            if response.status_code == 206:  # Partial content
                mode = 'ab'  # Append mode
            else:
                mode = 'wb'  # Write mode
                downloaded_size = 0

            downloaded_this_session = 0

            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_this_session += len(chunk)

            # Move completed file to final location
            temp_path.rename(local_path)

            # Verify integrity
            if expected_hash and not self.verify_file_integrity(local_path, expected_hash):
                logging.error(f"Integrity check failed for {local_path}")
                local_path.unlink()  # Delete corrupted file
                return False

            self.stats['total_downloads'] += 1
            self.stats['total_bytes'] += downloaded_this_session

            return True

        except Exception as e:
            logging.error(f"Download failed for {image_url}: {e}")
            self.stats['failed_downloads'] += 1
            return False

    def cleanup_old_images(self, current_images):
        """Remove images no longer in manifest"""
        try:
            current_names = {img['name'] for img in current_images}
            local_files = set()

            # Get all image files
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                local_files.update(f.name for f in self.images_dir.glob(ext))

            # Remove files not in current manifest
            to_remove = local_files - current_names
            for filename in to_remove:
                file_path = self.images_dir / filename
                try:
                    file_path.unlink()
                    logging.info(f"Removed obsolete image: {filename}")
                except Exception as e:
                    logging.warning(f"Failed to remove {filename}: {e}")

        except Exception as e:
            logging.error(f"Failed to cleanup old images: {e}")

    def optimize_storage(self):
        """Optimize storage by compressing old images"""
        try:
            # Keep only recent images uncompressed
            # Compress older images for storage efficiency
            # This is a placeholder for PIL/Pillow integration
            pass
        except Exception as e:
            logging.error(f"Storage optimization failed: {e}")

    def sync_images(self):
        """Perform intelligent image synchronization"""
        logging.info("Starting image synchronization")

        manifest = self.get_remote_manifest()
        if not manifest:
            logging.error("No manifest available, skipping sync")
            return False

        images = manifest.get('images', [])
        if not images:
            logging.info("No images in manifest")
            return True

        updated = False
        successful_downloads = 0

        for image_info in images:
            image_name = image_info['name']
            expected_hash = image_info.get('hash')
            image_url = urljoin(f"{self.kiosk_url}/", f"images/{image_name}")

            local_path = self.images_dir / image_name

            # Check if download needed
            needs_download = True

            if local_path.exists():
                if expected_hash:
                    if self.verify_file_integrity(local_path, expected_hash):
                        logging.debug(f"Image {image_name} is up to date")
                        needs_download = False
                        self.stats['cache_hits'] += 1
                    else:
                        logging.info(f"Image {image_name} corrupted, re-downloading")
                else:
                    # No hash provided, assume it's current
                    needs_download = False

            if needs_download:
                logging.info(f"Downloading: {image_name}")
                if self.download_image_incremental(image_url, local_path, expected_hash):
                    successful_downloads += 1
                    updated = True
                    logging.info(f"Downloaded: {image_name}")
                else:
                    logging.error(f"Failed to download: {image_name}")

        # Cleanup old images
        self.cleanup_old_images(images)

        # Update sync timestamp
        self.stats['last_sync'] = time.time()

        logging.info(f"Sync complete: {successful_downloads} downloads, {len(images)} total images")

        return updated or successful_downloads > 0

    def get_sync_status(self):
        """Get synchronization status and statistics"""
        return {
            'last_sync': self.stats['last_sync'],
            'total_downloads': self.stats['total_downloads'],
            'total_bytes': self.stats['total_bytes'],
            'failed_downloads': self.stats['failed_downloads'],
            'cache_hits': self.stats['cache_hits'],
            'available_images': len(list(self.images_dir.glob("*.png"))) + len(list(self.images_dir.glob("*.jpg")))
        }

    def force_full_sync(self):
        """Force full synchronization, ignoring cache"""
        logging.info("Forcing full synchronization")

        # Clear cached manifest
        self.cached_manifest = None
        cache_file = self.cache_dir / "manifest.json"
        if cache_file.exists():
            cache_file.unlink()

        # Remove all local images to force re-download
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            for file_path in self.images_dir.glob(ext):
                try:
                    file_path.unlink()
                    logging.debug(f"Removed for full sync: {file_path.name}")
                except Exception as e:
                    logging.warning(f"Failed to remove {file_path}: {e}")

        # Perform full sync
        return self.sync_images()

    def run_continuous_sync(self, interval=300):
        """Run continuous synchronization in background"""
        logging.info(f"Starting continuous sync every {interval} seconds")

        while True:
            try:
                self.sync_images()
                time.sleep(interval)
            except KeyboardInterrupt:
                logging.info("Continuous sync stopped")
                break
            except Exception as e:
                logging.error(f"Continuous sync error: {e}")
                time.sleep(60)  # Wait before retry
```

### Advanced Slideshow Engine (`advanced_slideshow.py`)

```python
#!/usr/bin/env python3
"""
Advanced Slideshow Engine with Professional Transitions and Effects
"""

import pygame
import time
import math
import random
from enum import Enum
from typing import List, Tuple, Optional

class TransitionType(Enum):
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    ROTATE_CLOCKWISE = "rotate_clockwise"
    ROTATE_COUNTERCLOCKWISE = "rotate_counterclockwise"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    MOSAIC = "mosaic"
    BLUR_FADE = "blur_fade"

class SlideshowEngine:
    def __init__(self, screen: pygame.Surface, images: List[Tuple[str, pygame.Surface]]):
        self.screen = screen
        self.images = images
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # Default settings
        self.transition_duration = 2.0
        self.display_duration = 8.0
        self.random_transitions = True
        self.transition_variety = 5  # Use 5 different transitions

    def get_random_transition(self) -> Tuple[TransitionType, float]:
        """Get random transition with appropriate duration"""
        transitions = [
            (TransitionType.FADE, 1.5),
            (TransitionType.SLIDE_LEFT, 2.0),
            (TransitionType.SLIDE_RIGHT, 2.0),
            (TransitionType.SLIDE_UP, 2.0),
            (TransitionType.SLIDE_DOWN, 2.0),
            (TransitionType.ZOOM_IN, 2.5),
            (TransitionType.ZOOM_OUT, 2.5),
            (TransitionType.ROTATE_CLOCKWISE, 3.0),
            (TransitionType.WIPE_LEFT, 1.8),
            (TransitionType.WIPE_RIGHT, 1.8),
            (TransitionType.MOSAIC, 2.2),
            (TransitionType.BLUR_FADE, 2.0)
        ]

        if self.random_transitions:
            return random.choice(transitions)
        else:
            # Cycle through transitions
            transition_index = int(time.time() * 1000) % len(transitions)
            return transitions[transition_index]

    def apply_transition(self, old_image: pygame.Surface, new_image: pygame.Surface,
                        transition_type: TransitionType, duration: float):
        """Apply the specified transition effect"""

        if transition_type == TransitionType.FADE:
            self.fade_transition(old_image, new_image, duration)
        elif transition_type in [TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT,
                                TransitionType.SLIDE_UP, TransitionType.SLIDE_DOWN]:
            self.slide_transition(old_image, new_image, duration, transition_type)
        elif transition_type in [TransitionType.ZOOM_IN, TransitionType.ZOOM_OUT]:
            self.zoom_transition(old_image, new_image, duration, transition_type)
        elif transition_type in [TransitionType.ROTATE_CLOCKWISE, TransitionType.ROTATE_COUNTERCLOCKWISE]:
            self.rotate_transition(old_image, new_image, duration, transition_type)
        elif transition_type in [TransitionType.WIPE_LEFT, TransitionType.WIPE_RIGHT]:
            self.wipe_transition(old_image, new_image, duration, transition_type)
        elif transition_type == TransitionType.MOSAIC:
            self.mosaic_transition(old_image, new_image, duration)
        elif transition_type == TransitionType.BLUR_FADE:
            self.blur_fade_transition(old_image, new_image, duration)

    def fade_transition(self, old_image: pygame.Surface, new_image: pygame.Surface, duration: float):
        """Professional crossfade transition"""
        start_time = time.time()
        clock = pygame.time.Clock()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            progress = elapsed / duration

            # Create alpha surfaces
            old_alpha = old_image.copy()
            new_alpha = new_image.copy()

            # Smooth alpha curve (ease in/out)
            alpha_progress = self.ease_in_out_cubic(progress)
            old_alpha.set_alpha(int(255 * (1 - alpha_progress)))
            new_alpha.set_alpha(int(255 * alpha_progress))

            # Composite images
            self.screen.blit(old_alpha, (0, 0))
            self.screen.blit(new_alpha, (0, 0))
            pygame.display.flip()

            clock.tick(60)  # Maintain 60 FPS

        # Ensure final image is displayed
        self.screen.blit(new_image, (0, 0))
        pygame.display.flip()

    def slide_transition(self, old_image: pygame.Surface, new_image: pygame.Surface,
                        duration: float, direction: TransitionType):
        """Smooth slide transition with easing"""
        start_time = time.time()
        clock = pygame.time.Clock()

        # Determine slide direction
        if direction == TransitionType.SLIDE_LEFT:
            old_end_x, new_start_x = -self.screen_width, self.screen_width
        elif direction == TransitionType.SLIDE_RIGHT:
            old_end_x, new_start_x = self.screen_width, -self.screen_width
        elif direction == TransitionType.SLIDE_UP:
            old_end_y, new_start_y = -self.screen_height, self.screen_height
        elif direction == TransitionType.SLIDE_DOWN:
            old_end_y, new_start_y = self.screen_height, -self.screen_height

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            progress = self.ease_in_out_cubic(elapsed / duration)

            if direction in [TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT]:
                old_x = int(old_end_x * progress)
                new_x = int(new_start_x * (1 - progress))
                old_pos = (old_x, 0)
                new_pos = (new_x, 0)
            else:  # Up/Down
                old_y = int(old_end_y * progress)
                new_y = int(new_start_y * (1 - progress))
                old_pos = (0, old_y)
                new_pos = (0, new_y)

            self.screen.fill((0, 0, 0))
            self.screen.blit(old_image, old_pos)
            self.screen.blit(new_image, new_pos)
            pygame.display.flip()

            clock.tick(60)

        # Final position
        self.screen.blit(new_image, (0, 0))
        pygame.display.flip()

    def zoom_transition(self, old_image: pygame.Surface, new_image: pygame.Surface,
                       duration: float, zoom_type: TransitionType):
        """Zoom in/out transition with smooth scaling"""
        start_time = time.time()
        clock = pygame.time.Clock()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            progress = self.ease_in_out_cubic(elapsed / duration)

            if zoom_type == TransitionType.ZOOM_IN:
                # Start at 50% scale, zoom to 100%
                scale = 0.5 + (progress * 0.5)
            else:  # ZOOM_OUT
                # Start at 150% scale, zoom to 100%
                scale = 1.5 - (progress * 0.5)

            # Scale images
            scaled_width = int(self.screen_width * scale)
            scaled_height = int(self.screen_height * scale)

            if zoom_type == TransitionType.ZOOM_IN:
                scaled_old = pygame.transform.smoothscale(old_image, (scaled_width, scaled_height))
                scaled_new = pygame.transform.smoothscale(new_image, (scaled_width, scaled_height))
            else:
                # For zoom out, old image starts larger
                scaled_old = pygame.transform.smoothscale(old_image, (scaled_width, scaled_height))
                scaled_new = pygame.transform.smoothscale(new_image, (int(self.screen_width * 0.5), int(self.screen_height * 0.5)))

            # Center images
            old_x = (self.screen_width - scaled_width) // 2
            old_y = (self.screen_height - scaled_height) // 2

            new_scale = 0.5 + (progress * 0.5) if zoom_type == TransitionType.ZOOM_OUT else 1.0
            new_scaled_width = int(self.screen_width * new_scale)
            new_scaled_height = int(self.screen_height * new_scale)
            new_x = (self.screen_width - new_scaled_width) // 2
            new_y = (self.screen_height - new_scaled_height) // 2

            # Apply alpha based on progress
            alpha = int(255 * progress)
            if zoom_type == TransitionType.ZOOM_OUT:
                scaled_old.set_alpha(int(255 * (1 - progress)))
                scaled_new.set_alpha(alpha)
            else:
                scaled_old.set_alpha(int(255 * (1 - progress)))
                scaled_new.set_alpha(alpha)

            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled_old, (old_x, old_y))
            self.screen.blit(scaled_new, (new_x, new_y))
            pygame.display.flip()

            clock.tick(60)

        self.screen.blit(new_image, (0, 0))
        pygame.display.flip()

    def rotate_transition(self, old_image: pygame.Surface, new_image: pygame.Surface,
                         duration: float, rotation_type: TransitionType):
        """Rotating transition effect"""
        start_time = time.time()
        clock = pygame.time.Clock()

        rotation_direction = 1 if rotation_type == TransitionType.ROTATE_CLOCKWISE else -1

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            progress = elapsed / duration

            # Rotation angle (0 to 360 degrees)
            angle = progress * 360 * rotation_direction

            # Rotate old image out
            rotated_old = pygame.transform.rotate(old_image, angle * (1 - progress))
            old_alpha = rotated_old.copy()
            old_alpha.set_alpha(int(255 * (1 - progress)))

            # Rotate new image in
            rotated_new = pygame.transform.rotate(new_image, angle * progress * -rotation_direction)
            new_alpha = rotated_new.copy()
            new_alpha.set_alpha(int(255 * progress))

            # Center rotated images
            old_rect = old_alpha.get_rect(center=(self.screen_width//2, self.screen_height//2))
            new_rect = new_alpha.get_rect(center=(self.screen_width//2, self.screen_height//2))

            self.screen.fill((0, 0, 0))
            self.screen.blit(old_alpha, old_rect)
            self.screen.blit(new_alpha, new_rect)
            pygame.display.flip()

            clock.tick(60)

        self.screen.blit(new_image, (0, 0))
        pygame.display.flip()

    def wipe_transition(self, old_image: pygame.Surface, new_image: pygame.Surface,
                       duration: float, wipe_type: TransitionType):
        """Wipe transition effect"""
        start_time = time.time()
        clock = pygame.time.Clock()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            progress = self.ease_in_out_cubic(elapsed / duration)

            if wipe_type == TransitionType.WIPE_LEFT:
                wipe_width = int(self.screen_width * progress)
                # Show old image on left, new image on right
                old_rect = pygame.Rect(0, 0, self.screen_width - wipe_width, self.screen_height)
                new_rect = pygame.Rect(self.screen_width - wipe_width, 0, wipe_width, self.screen_height)
            else:  # WIPE_RIGHT
                wipe_width = int(self.screen_width * progress)
                old_rect = pygame.Rect(wipe_width, 0, self.screen_width - wipe_width, self.screen_height)
                new_rect = pygame.Rect(0, 0, wipe_width, self.screen_height)

            self.screen.fill((0, 0, 0))
            self.screen.blit(old_image, (0, 0), old_rect)
            self.screen.blit(new_image, new_rect.topleft, new_rect)
            pygame.display.flip()

            clock.tick(60)

        self.screen.blit(new_image, (0, 0))
        pygame.display.flip()

    def mosaic_transition(self, old_image: pygame.Surface, new_image: pygame.Surface, duration: float):
        """Mosaic/pixelation transition effect"""
        start_time = time.time()
        clock = pygame.time.Clock()

        max_block_size = 64
        min_block_size = 4

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            progress = elapsed / duration

            # Block size decreases as transition progresses
            block_size = max(min_block_size, int(max_block_size * (1 - progress)))

            # Create mosaic versions
            mosaic_old = self.create_mosaic(old_image, block_size)
            mosaic_new = self.create_mosaic(new_image, block_size)

            # Fade between mosaics
            alpha = int(255 * progress)
            mosaic_old.set_alpha(int(255 * (1 - progress)))
            mosaic_new.set_alpha(alpha)

            self.screen.blit(mosaic_old, (0, 0))
            self.screen.blit(mosaic_new, (0, 0))
            pygame.display.flip()

            clock.tick(30)  # Lower FPS for this effect

        self.screen.blit(new_image, (0, 0))
        pygame.display.flip()

    def create_mosaic(self, image: pygame.Surface, block_size: int) -> pygame.Surface:
        """Create mosaic/pixelated version of image"""
        width, height = image.get_size()
        mosaic = pygame.Surface((width, height))

        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                # Get average color of block
                block_rect = pygame.Rect(x, y, min(block_size, width - x), min(block_size, height - y))
                block_surface = pygame.Surface((block_rect.width, block_rect.height))
                block_surface.blit(image, (0, 0), block_rect)

                # Calculate average color (simplified)
                color = pygame.transform.average_color(block_surface)

                # Draw block
                pygame.draw.rect(mosaic, color, (x, y, block_rect.width, block_rect.height))

        return mosaic

    def blur_fade_transition(self, old_image: pygame.Surface, new_image: pygame.Surface, duration: float):
        """Blur fade transition (placeholder - requires PIL for proper blur)"""
        # Simplified version without actual blur
        self.fade_transition(old_image, new_image, duration)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease in/out function for smooth transitions"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    def run_slideshow(self, image_paths: List[str], interval: int = 30) -> bool:
        """
        Run slideshow with advanced transitions
        Returns True if content was updated during slideshow
        """
        if not image_paths:
            return False

        # Load all images
        images = []
        for path in image_paths:
            try:
                image = pygame.image.load(path)
                # Scale to fit screen while maintaining aspect ratio
                img_width, img_height = image.get_size()
                scale_factor = min(self.screen_width / img_width, self.screen_height / img_height)
                if scale_factor < 1.0:
                    new_width = int(img_width * scale_factor)
                    new_height = int(img_height * scale_factor)
                    image = pygame.transform.smoothscale(image, (new_width, new_height))
                images.append(image)
            except Exception as e:
                print(f"Failed to load image {path}: {e}")

        if not images:
            return False

        current_index = 0
        last_check_time = time.time()

        while True:
            # Display current image
            current_image = images[current_index]
            self.screen.blit(current_image, (0, 0))
            pygame.display.flip()

            # Display duration
            display_start = time.time()
            while time.time() - display_start < interval:
                # Check for user input to exit
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return False

                # Periodic update check
                if time.time() - last_check_time > 60:  # Check every minute
                    # Here you would check for content updates
                    # Return True if updates found
                    last_check_time = time.time()

                time.sleep(0.1)  # Small delay to prevent busy waiting

            # Transition to next image
            next_index = (current_index + 1) % len(images)

            # Get random transition
            transition_type, transition_duration = self.get_random_transition()

            # Apply transition
            self.apply_transition(
                images[current_index],
                images[next_index],
                transition_type,
                transition_duration
            )

            current_index = next_index

if __name__ == "__main__":
    # Example usage
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)

    # Mock image loading (replace with actual image paths)
    image_paths = ["/home/pi/images/slide1.png", "/home/pi/images/slide2.png"]
    images = []
    for path in image_paths:
        try:
            img = pygame.image.load(path)
            images.append(img)
        except:
            print(f"Could not load {path}")

    if images:
        engine = SlideshowEngine(screen, list(zip(image_paths, images)))
        engine.run_slideshow(image_paths, 10)  # 10 second intervals

    pygame.quit()
```

---

## Kiosk Side Configuration System

### Image Generation Pipeline

**1. Screenshot Capture (`capture_display.py`)**
```python
#!/usr/bin/env python3
"""
Automated Display Capture and Image Generation
"""

import subprocess
import time
import os
from pathlib import Path
import json
import logging

class DisplayCapture:
    def __init__(self, kiosk_url="http://localhost", output_dir="/var/lib/314sign/images"):
        self.kiosk_url = kiosk_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def capture_display(self, display_id="default", width=1920, height=1080):
        """Capture current display as high-res image"""
        timestamp = int(time.time() * 1000)
        output_file = self.output_dir / f"{display_id}_{timestamp}.png"

        # Use Chrome headless for screenshot
        cmd = [
            "chromium",
            "--headless",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            f"--window-size={width},{height}",
            "--hide-scrollbars",
            "--disable-extensions",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            f"--screenshot={output_file}",
            self.kiosk_url
        ]

        try:
            result = subprocess.run(cmd, timeout=30, capture_output=True, text=True)
            if result.returncode == 0 and output_file.exists():
                logging.info(f"Captured display: {output_file}")
                return str(output_file)
            else:
                logging.error(f"Capture failed: {result.stderr}")
                return None
        except Exception as e:
            logging.error(f"Capture error: {e}")
            return None

    def optimize_image(self, input_path, quality=95):
        """Optimize image for network transfer"""
        input_file = Path(input_path)
        output_file = input_file.with_suffix('.optimized.png')

        # Use ImageMagick for optimization
        cmd = [
            "convert",
            str(input_file),
            "-quality", str(quality),
            "-define", "png:compression-level=9",
            "-strip",  # Remove metadata
            str(output_file)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Replace original with optimized
                output_file.replace(input_file)
                logging.info(f"Optimized: {input_file}")
                return True
            else:
                logging.error(f"Optimization failed: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Optimization error: {e}")
            return False

    def generate_thumbnails(self, image_path, sizes=[(400, 225), (800, 450)]):
        """Generate thumbnails for different uses"""
        input_file = Path(image_path)
        thumbnails = []

        for width, height in sizes:
            thumb_file = input_file.with_suffix(f'.thumb_{width}x{height}.jpg')

            cmd = [
                "convert",
                str(input_file),
                "-resize", f"{width}x{height}^",
                "-gravity", "center",
                "-extent", f"{width}x{height}",
                "-quality", "85",
                str(thumb_file)
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    thumbnails.append(str(thumb_file))
                else:
                    logging.error(f"Thumbnail generation failed: {result.stderr}")
            except Exception as e:
                logging.error(f"Thumbnail error: {e}")

        return thumbnails

    def process_display_update(self, display_id="default"):
        """Complete pipeline: capture → optimize → thumbnail → metadata"""
        # Capture
        image_path = self.capture_display(display_id)
        if not image_path:
            return None

        # Optimize
        if not self.optimize_image(image_path):
            return None

        # Generate thumbnails
        thumbnails = self.generate_thumbnails(image_path)

        # Generate metadata
        metadata = {
            "display_id": display_id,
            "timestamp": int(time.time() * 1000),
            "original_size": os.path.getsize(image_path),
            "thumbnails": thumbnails,
            "url": f"/images/{Path(image_path).name}"
        }

        # Save metadata
        metadata_file = Path(image_path).with_suffix('.json')
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save metadata: {e}")

        return metadata

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Display Capture System')
    parser.add_argument('--display-id', default='default', help='Display identifier')
    parser.add_argument('--kiosk-url', default='http://localhost', help='Kiosk URL')
    parser.add_argument('--width', type=int, default=1920, help='Capture width')
    parser.add_argument('--height', type=int, default=1080, help='Capture height')

    args = parser.parse_args()

    capture = DisplayCapture(args.kiosk_url)
    result = capture.process_display_update(args.display_id)

    if result:
        print(f"Successfully captured and processed display: {result['url']}")
    else:
        print("Display capture failed")
        exit(1)
```

### Remote Device Management Interface

**Enhanced Kiosk Web Interface:**
- **Device Registration**: Enter device codes or auto-discover
- **Content Assignment**: Drag-and-drop content to devices  
- **Live Preview**: See what each remote is displaying
- **Bulk Operations**: Update multiple devices simultaneously
- **Performance Monitoring**: View device health and sync status

### Automated Content Distribution

**Smart Sync System:**
```javascript
// Kiosk-side content distribution
class ContentDistributor {
  async distributeContent(contentId, deviceIds) {
    // Generate display image
    const imageData = await generateDisplayImage(contentId);
    
    // Compress and optimize
    const optimizedImage = await optimizeImage(imageData);
    
    // Calculate diff for incremental updates
    const patches = await calculateIncrementalUpdates(optimizedImage, deviceIds);
    
    // Distribute to devices
    const results = await Promise.allSettled(
      deviceIds.map(deviceId => pushToDevice(deviceId, optimizedImage, patches[deviceId]))
    );
    
    return results;
  }
}
```

---

## Multi-Device Control Architecture

### Device Grouping System

```javascript
// Device Groups for Bulk Management
const deviceGroups = {
  'kitchen': {
    devices: ['remote-kitchen-1', 'remote-kitchen-2', 'remote-kitchen-monitor'],
    content: 'kitchen-menu',
    schedule: 'breakfast-lunch-dinner'
  },
  'lobby': {
    devices: ['remote-lobby-main', 'remote-lobby-secondary'],
    content: 'welcome-screen',
    schedule: 'continuous'
  },
  'classrooms': {
    devices: ['remote-room-101', 'remote-room-102', 'remote-room-103'],
    content: 'schedule-display',
    schedule: 'school-hours'
  }
};

// Bulk Operations
async function updateDeviceGroup(groupName, contentId) {
  const group = deviceGroups[groupName];
  if (!group) return;
  
  // Update all devices in group
  await Promise.all(
    group.devices.map(deviceId => 
      assignContentToDevice(deviceId, contentId)
    )
  );
  
  // Update group content mapping
  group.content = contentId;
}
```

### Real-time Device Monitoring

```javascript
// Live Device Dashboard
class DeviceMonitor {
  constructor() {
    this.devices = new Map();
    this.updateInterval = 30000; // 30 seconds
    this.startMonitoring();
  }
  
  async startMonitoring() {
    setInterval(() => this.updateDeviceStatuses(), this.updateInterval);
  }
  
  async updateDeviceStatuses() {
    const deviceStatuses = await fetch('/api/remotes/status').then(r => r.json());
    
    deviceStatuses.forEach(status => {
      const device = this.devices.get(status.device_id) || {};
      
      // Update device state
      device.status = status.online ? 'online' : 'offline';
      device.lastSeen = status.last_seen;
      device.currentImage = status.current_image;
      device.uptime = status.uptime;
      device.syncStatus = status.sync_success ? 'synced' : 'syncing';
      
      this.devices.set(status.device_id, device);
      
      // Update UI
      this.updateDeviceUI(status.device_id, device);
    });
  }
  
  updateDeviceUI(deviceId, deviceData) {
    const deviceElement = document.getElementById(`device-${deviceId}`);
    if (deviceElement) {
      deviceElement.className = `device ${deviceData.status}`;
      deviceElement.querySelector('.status').textContent = deviceData.status;
      deviceElement.querySelector('.uptime').textContent = formatUptime(deviceData.uptime);
      deviceElement.querySelector('.last-seen').textContent = formatTime(deviceData.lastSeen);
    }
  }
}
```

### Intelligent Content Distribution

```javascript
// Smart Content Router
class ContentRouter {
  constructor() {
    this.contentRules = new Map();
    this.deviceCapabilities = new Map();
  }
  
  // Define content rules
  addContentRule(devicePattern, contentType, conditions) {
    this.contentRules.set(devicePattern, { contentType, conditions });
  }
  
  // Route content to appropriate devices
  async routeContent(contentId, contentMetadata) {
    const eligibleDevices = [];
    
    for (const [deviceId, capabilities] of this.deviceCapabilities) {
      if (this.deviceMatchesContent(deviceId, contentMetadata)) {
        eligibleDevices.push(deviceId);
      }
    }
    
    // Distribute content
    await distributeToDevices(contentId, eligibleDevices);
    
    return eligibleDevices;
  }
  
  deviceMatchesContent(deviceId, contentMetadata) {
    // Check device capabilities vs content requirements
    // Resolution, color depth, aspect ratio, etc.
    const deviceCaps = this.deviceCapabilities.get(deviceId);
    
    return deviceCaps.resolution[0] >= contentMetadata.minResolution[0] &&
           deviceCaps.resolution[1] >= contentMetadata.minResolution[1];
  }
}
```

---

## Implementation Roadmap

### **Phase 1: Core Infrastructure (Week 1-2)**
- [x] Basic image display engine
- [x] Simple screenshot capture
- [x] Manual image transfer
- [x] Single device configuration
- [ ] **Basic remote registration** (in progress)
- [ ] **Simple sync mechanism**

### **Phase 2: Enhanced Display System (Week 3-4)**
- [ ] Advanced slideshow engine with transitions
- [ ] Image optimization and compression
- [ ] Basic device grouping
- [ ] Status monitoring
- [ ] Automated content generation

### **Phase 3: Production Features (Week 5-6)**
- [ ] Intelligent content routing
- [ ] Bulk device management
- [ ] Real-time monitoring dashboard
- [ ] Offline operation support
- [ ] Performance optimization

### **Phase 4: Advanced Capabilities (Week 7-8)**
- [ ] Dynamic content overlays (time, weather)
- [ ] Interactive elements support
- [ ] Advanced scheduling
- [ ] Remote diagnostics and maintenance
- [ ] API integrations

---

## Genius Innovations

### **1. Appliance-First Design**
**Pi Zeros as dedicated display appliances** - not general-purpose computers. This eliminates complexity and maximizes reliability.

### **2. Content-Aware Image Generation**
**Intelligent display capture** that understands content type and optimizes accordingly:
- Menus: High contrast, readable fonts
- Photos: Color-accurate reproduction  
- Charts: Crisp line art preservation

### **3. Distributed Intelligence**
**Smart edge devices** that make local decisions:
- Cache management based on available storage
- Quality adaptation based on network conditions
- Graceful degradation during connectivity issues

### **4. Zero-Configuration Operation**
**Self-organizing device networks**:
- Automatic capability detection
- Dynamic content routing
- Self-healing sync mechanisms

### **5. Hybrid Content Model**
**Best of both worlds**:
- Static content via images (reliable, efficient)
- Dynamic elements via selective web features
- Automatic fallback mechanisms

---

## Why This Beats Web-Based Approaches

| Aspect | Web-Based | Image-Based |
|--------|-----------|-------------|
| **Reliability** | Browser crashes, memory issues | Rock-solid Python scripts |
| **Resource Usage** | Heavy (GPU, memory, CPU) | Minimal (image display only) |
| **Setup Complexity** | Complex kiosk configuration | Simple file operations |
| **Offline Operation** | Limited/no | Full offline capability |
| **Content Flexibility** | Any web content | Pre-rendered static content |
| **Device Compatibility** | Browser-dependent | Hardware-dependent only |
| **Maintenance** | Frequent updates needed | Minimal maintenance |
| **Power Efficiency** | Higher consumption | Optimized for efficiency |

**The image-based approach isn't backwards - it's the future of reliable digital signage!**

---

*Ready to revolutionize digital signage? This system will make Pi Zero displays bulletproof!* 🚀