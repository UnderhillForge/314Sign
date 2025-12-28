#!/usr/bin/env python3
"""
Basic Display Capture System for Kiosk
Captures current display as image for remote distribution
"""

import subprocess
import time
import os
import logging
from pathlib import Path
import argparse

class BasicDisplayCapture:
    def __init__(self, output_dir="/var/lib/314sign/images", kiosk_url="http://localhost"):
        self.output_dir = Path(output_dir)
        self.kiosk_url = kiosk_url
        self.output_dir.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def capture_display(self, display_id="default", width=1920, height=1080):
        """Capture current display as PNG image"""
        timestamp = int(time.time() * 1000)
        output_file = self.output_dir / f"{display_id}_{timestamp}.png"

        logging.info(f"Capturing display to: {output_file}")

        # Use Chromium headless for screenshot
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
            logging.info("Running chromium screenshot command...")
            result = subprocess.run(cmd, timeout=30, capture_output=True, text=True)

            if result.returncode == 0 and output_file.exists():
                file_size = output_file.stat().st_size
                logging.info(f"Successfully captured display: {output_file} ({file_size} bytes)")
                return str(output_file)
            else:
                logging.error(f"Capture failed with return code {result.returncode}")
                if result.stderr:
                    logging.error(f"Chromium stderr: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logging.error("Screenshot command timed out after 30 seconds")
            return None
        except Exception as e:
            logging.error(f"Capture error: {e}")
            return None

    def list_captured_images(self):
        """List all captured images"""
        image_files = list(self.output_dir.glob("*.png"))
        image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        logging.info(f"Found {len(image_files)} captured images:")
        for img_file in image_files[:10]:  # Show latest 10
            mtime = time.ctime(img_file.stat().st_mtime)
            size = img_file.stat().st_size
            logging.info(f"  {img_file.name} - {size} bytes - {mtime}")

        return image_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Basic Display Capture System')
    parser.add_argument('--display-id', default='default', help='Display identifier')
    parser.add_argument('--output-dir', default='/var/lib/314sign/images', help='Output directory')
    parser.add_argument('--kiosk-url', default='http://localhost', help='Kiosk URL to capture')
    parser.add_argument('--width', type=int, default=1920, help='Capture width')
    parser.add_argument('--height', type=int, default=1080, help='Capture height')
    parser.add_argument('--list', action='store_true', help='List captured images instead of capturing')

    args = parser.parse_args()

    capture = BasicDisplayCapture(args.output_dir, args.kiosk_url)

    if args.list:
        capture.list_captured_images()
    else:
        result = capture.capture_display(args.display_id, args.width, args.height)
        if result:
            print(f"Successfully captured display: {result}")
        else:
            print("Display capture failed")
            exit(1)