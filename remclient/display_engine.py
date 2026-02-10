#!/usr/bin/env python3
"""
Basic Image Display Engine for Pi Zero 2 W
Core component of the image-based remote display system
"""

import pygame
import time
import json
import os
import logging
from pathlib import Path

class BasicImageDisplay:
    def __init__(self, width=1920, height=1080):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)

        self.display_width = width
        self.display_height = height
        self.images_dir = Path("/home/pi/images")
        self.images_dir.mkdir(exist_ok=True)

        # Basic logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def load_image(self, image_path):
        """Load and scale image for display"""
        try:
            image = pygame.image.load(str(image_path))

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

    def display_image(self, image):
        """Display image centered on screen"""
        if image is None:
            return

        img_width, img_height = image.get_size()

        # Center the image
        x = (self.display_width - img_width) // 2
        y = (self.display_height - img_height) // 2

        # Clear screen and display
        self.screen.fill((0, 0, 0))  # Black background
        self.screen.blit(image, (x, y))
        pygame.display.flip()

        logging.info(f"Displayed image: {img_width}x{img_height} at ({x}, {y})")

    def display_standby(self):
        """Display standby screen when no images available"""
        self.screen.fill((0, 20, 40))  # Dark blue
        pygame.display.flip()
        logging.info("Displaying standby screen")

    def run(self):
        """Main display loop"""
        logging.info("Starting Basic Image Display Engine")
        logging.info(f"Display resolution: {self.display_width}x{self.display_height}")

        while True:
            try:
                # Get list of available images
                image_files = list(self.images_dir.glob("*.png")) + list(self.images_dir.glob("*.jpg"))

                if image_files:
                    # Sort by modification time (newest first)
                    image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                    # Display the most recent image
                    latest_image = image_files[0]
                    logging.info(f"Loading image: {latest_image}")

                    image = self.load_image(latest_image)
                    if image:
                        self.display_image(image)

                        # Display for 30 seconds, then check for updates
                        start_time = time.time()
                        while time.time() - start_time < 30:
                            # Check for quit events
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    return
                                elif event.type == pygame.KEYDOWN:
                                    if event.key == pygame.K_ESCAPE:
                                        logging.info("Exit requested by user")
                                        return

                            time.sleep(0.1)  # Small delay to prevent busy waiting

                        # Continue to check for new images
                        continue

                else:
                    # No images available
                    self.display_standby()

                # Wait before checking again
                time.sleep(10)  # Check every 10 seconds when no images

            except KeyboardInterrupt:
                logging.info("Display engine stopped by user")
                break
            except Exception as e:
                logging.error(f"Display engine error: {e}")
                time.sleep(5)  # Wait before retry

        pygame.quit()

if __name__ == "__main__":
    display = BasicImageDisplay()
    try:
        display.run()
    except KeyboardInterrupt:
        print("Display engine stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise