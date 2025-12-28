#!/usr/bin/env python3
"""
Basic Image Synchronization Script
Manually sync images from kiosk to remote devices
"""

import subprocess
import time
import os
import logging
from pathlib import Path
import argparse

class BasicImageSync:
    def __init__(self, images_dir="/var/lib/314sign/images"):
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def list_available_images(self):
        """List all available images on kiosk"""
        image_files = list(self.images_dir.glob("*.png")) + list(self.images_dir.glob("*.jpg"))
        image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        logging.info(f"Available images in {self.images_dir}:")
        for i, img_file in enumerate(image_files[:10]):  # Show latest 10
            mtime = time.ctime(img_file.stat().st_mtime)
            size = img_file.stat().st_size
            marker = " ← LATEST" if i == 0 else ""
            logging.info(f"  {img_file.name} - {size} bytes - {mtime}{marker}")

        return image_files

    def sync_image_to_device(self, image_path, device_hostname, username="pi", remote_path="/home/pi/images/"):
        """Sync single image to remote device via SCP"""
        image_file = Path(image_path)

        if not image_file.exists():
            logging.error(f"Image file does not exist: {image_path}")
            return False

        # Ensure remote directory exists (create if needed)
        mkdir_cmd = [
            "ssh",
            f"{username}@{device_hostname}",
            f"mkdir -p {remote_path}"
        ]

        logging.info(f"Ensuring remote directory exists: {username}@{device_hostname}:{remote_path}")
        try:
            result = subprocess.run(mkdir_cmd, timeout=10, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Failed to create remote directory: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"SSH connection failed: {e}")
            return False

        # Copy image file
        scp_cmd = [
            "scp",
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",  # For initial setup - remove in production
            str(image_file),
            f"{username}@{device_hostname}:{remote_path}"
        ]

        logging.info(f"Copying {image_file.name} to {device_hostname}")
        try:
            result = subprocess.run(scp_cmd, timeout=30, capture_output=True, text=True)

            if result.returncode == 0:
                file_size = image_file.stat().st_size
                logging.info(f"Successfully synced {image_file.name} ({file_size} bytes) to {device_hostname}")
                return True
            else:
                logging.error(f"SCP failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logging.error("SCP command timed out")
            return False
        except Exception as e:
            logging.error(f"Sync error: {e}")
            return False

    def sync_latest_to_device(self, device_hostname, username="pi"):
        """Sync the most recent image to a device"""
        image_files = self.list_available_images()

        if not image_files:
            logging.error("No images available to sync")
            return False

        latest_image = image_files[0]
        logging.info(f"Syncing latest image: {latest_image.name}")

        return self.sync_image_to_device(latest_image, device_hostname, username)

    def sync_to_multiple_devices(self, device_hostnames, username="pi"):
        """Sync latest image to multiple devices"""
        if not device_hostnames:
            logging.error("No device hostnames provided")
            return

        image_files = self.list_available_images()
        if not image_files:
            return

        latest_image = image_files[0]
        logging.info(f"Syncing {latest_image.name} to {len(device_hostnames)} devices")

        results = []
        for hostname in device_hostnames:
            success = self.sync_image_to_device(latest_image, hostname, username)
            results.append((hostname, success))

        # Report results
        successful = sum(1 for _, success in results if success)
        logging.info(f"Sync complete: {successful}/{len(results)} devices successful")

        for hostname, success in results:
            status = "✓" if success else "✗"
            logging.info(f"  {status} {hostname}")

        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Basic Image Synchronization')
    parser.add_argument('--images-dir', default='/var/lib/314sign/images', help='Local images directory')
    parser.add_argument('--device', help='Remote device hostname (e.g., remote-272ff1.local)')
    parser.add_argument('--devices', nargs='+', help='Multiple device hostnames')
    parser.add_argument('--username', default='pi', help='SSH username for remote devices')
    parser.add_argument('--list', action='store_true', help='List available images')
    parser.add_argument('--image', help='Specific image file to sync')

    args = parser.parse_args()

    sync = BasicImageSync(args.images_dir)

    if args.list:
        sync.list_available_images()
    elif args.image and args.device:
        success = sync.sync_image_to_device(args.image, args.device, args.username)
        exit(0 if success else 1)
    elif args.devices:
        results = sync.sync_to_multiple_devices(args.devices, args.username)
        successful = sum(1 for _, success in results if success)
        exit(0 if successful == len(results) else 1)
    elif args.device:
        success = sync.sync_latest_to_device(args.device, args.username)
        exit(0 if success else 1)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # List available images")
        print("  python3 sync_images.py --list")
        print()
        print("  # Sync latest image to single device")
        print("  python3 sync_images.py --device remote-272ff1.local")
        print()
        print("  # Sync to multiple devices")
        print("  python3 sync_images.py --devices remote-1.local remote-2.local")
        print()
        print("  # Sync specific image")
        print("  python3 sync_images.py --image /path/to/image.png --device remote-1.local")
        exit(1)