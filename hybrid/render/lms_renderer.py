#!/usr/bin/env python3
"""
LMS Renderer - Converts Lightweight Markup Script to rendered images
Core rendering engine for the hybrid display system
"""

import pygame
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import math

class LMSRenderer:
    """
    Renders LMS (Lightweight Markup Script) files to display-ready images
    Handles text, shapes, images, and dynamic content overlays
    """

    def __init__(self, display_size: Tuple[int, int] = (1920, 1080)):
        pygame.init()
        self.display_width, self.display_height = display_size

        # Font cache for performance
        self.font_cache = {}
        self.font_paths = {}

        # Color cache for performance
        self.color_cache = {}

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def render_lms_to_surface(self, lms_data: Dict[str, Any]) -> pygame.Surface:
        """
        Render LMS data to a Pygame surface

        Args:
            lms_data: Parsed LMS data from parser

        Returns:
            Pygame surface ready for display
        """
        # Create base surface
        surface = pygame.Surface((self.display_width, self.display_height))

        # Fill with global background color
        bg_color = self._parse_color(lms_data.get('global_settings', {}).get('background_color', '#000000'))
        surface.fill(bg_color)

        # Render background if specified
        if 'background' in lms_data:
            self._render_background(surface, lms_data['background'])

        # Render overlays in order
        if 'overlays' in lms_data:
            for overlay in lms_data['overlays']:
                if overlay.get('visible', True):
                    self._render_overlay(surface, overlay)

        return surface

    def _render_background(self, surface: pygame.Surface, background: Dict[str, Any]) -> None:
        """Render background image with effects"""
        # Background rendering would integrate with the background cache
        # For now, we'll handle color-only backgrounds
        # Full image background support comes in Phase 2B

        # Apply brightness adjustment (placeholder for image backgrounds)
        brightness = background.get('brightness', 1.0)
        if brightness != 1.0:
            # This would apply brightness to background image
            pass

    def _render_overlay(self, surface: pygame.Surface, overlay: Dict[str, Any]) -> None:
        """Render a single overlay element"""
        overlay_type = overlay['type']

        try:
            if overlay_type == 'text':
                self._render_text_overlay(surface, overlay)
            elif overlay_type == 'image':
                self._render_image_overlay(surface, overlay)
            elif overlay_type == 'shape':
                self._render_shape_overlay(surface, overlay)
            elif overlay_type == 'dynamic':
                self._render_dynamic_overlay(surface, overlay)
            else:
                self.logger.warning(f"Unknown overlay type: {overlay_type}")
        except Exception as e:
            self.logger.error(f"Failed to render overlay {overlay}: {e}")

    def _render_text_overlay(self, surface: pygame.Surface, overlay: Dict[str, Any]) -> None:
        """Render text overlay with full formatting support"""
        content = overlay['content']
        font_name = overlay.get('font', 'Arial')
        size = overlay.get('size', 24)
        color = self._parse_color(overlay.get('color', '#FFFFFF'))
        position = overlay['position']
        opacity = overlay.get('opacity', 1.0)
        rotation = overlay.get('rotation', 0)
        align = overlay.get('align', 'left')

        # Get font
        font = self._get_font(font_name, size)
        if not font:
            self.logger.error(f"Could not load font: {font_name}")
            return

        # Render text
        text_surface = font.render(content, True, color)

        # Apply opacity
        if opacity < 1.0:
            text_surface.set_alpha(int(255 * opacity))

        # Apply rotation
        if rotation != 0:
            text_surface = pygame.transform.rotate(text_surface, rotation)

        # Calculate position
        x, y = self._calculate_position(position, text_surface.get_size(), align)

        # Apply shadow if specified
        shadow = overlay.get('shadow')
        if shadow:
            self._render_text_shadow(surface, text_surface, x, y, shadow)

        # Blit text
        surface.blit(text_surface, (x, y))

    def _render_image_overlay(self, surface: pygame.Surface, overlay: Dict[str, Any]) -> None:
        """Render image overlay (placeholder for Phase 2B)"""
        # Image overlay support comes in Phase 2B with asset management
        self.logger.debug("Image overlay rendering not yet implemented")

    def _render_shape_overlay(self, surface: pygame.Surface, overlay: Dict[str, Any]) -> None:
        """Render shape overlay (rectangle, circle, etc.)"""
        shape_type = overlay['shape']
        position = overlay['position']
        opacity = overlay.get('opacity', 1.0)

        x, y = self._resolve_position(position)

        if shape_type == 'rectangle':
            width = overlay.get('width', 100)
            height = overlay.get('height', 100)
            fill_color = self._parse_color(overlay.get('fill_color'))
            stroke_color = self._parse_color(overlay.get('stroke_color'))
            stroke_width = overlay.get('stroke_width', 0)

            # Create shape surface
            shape_surface = pygame.Surface((width, height), pygame.SRCALPHA)

            if fill_color:
                shape_surface.fill(fill_color)

            if stroke_color and stroke_width > 0:
                pygame.draw.rect(shape_surface, stroke_color, (0, 0, width, height), stroke_width)

            # Apply opacity
            if opacity < 1.0:
                shape_surface.set_alpha(int(255 * opacity))

            surface.blit(shape_surface, (x, y))

        elif shape_type == 'circle':
            radius = overlay.get('radius', 50)
            fill_color = self._parse_color(overlay.get('fill_color'))
            stroke_color = self._parse_color(overlay.get('stroke_color'))
            stroke_width = overlay.get('stroke_width', 0)

            # Draw circle
            center_x, center_y = x + radius, y + radius

            if fill_color:
                pygame.draw.circle(surface, fill_color, (center_x, center_y), radius)

            if stroke_color and stroke_width > 0:
                pygame.draw.circle(surface, stroke_color, (center_x, center_y), radius, stroke_width)

    def _render_dynamic_overlay(self, surface: pygame.Surface, overlay: Dict[str, Any]) -> None:
        """Render dynamic content overlay (time, date, etc.)"""
        content_type = overlay['content']
        format_str = overlay.get('format')

        # Generate dynamic content
        dynamic_text = self._generate_dynamic_content(content_type, format_str)

        # Convert to text overlay format
        text_overlay = overlay.copy()
        text_overlay['type'] = 'text'
        text_overlay['content'] = dynamic_text

        # Render as text
        self._render_text_overlay(surface, text_overlay)

    def _generate_dynamic_content(self, content_type: str, format_str: Optional[str]) -> str:
        """Generate dynamic content based on type"""
        now = time.time()
        local_time = time.localtime(now)

        if content_type == 'current_time':
            if format_str == 'HH:MM':
                return time.strftime('%H:%M', local_time)
            elif format_str == 'HH:MM:SS':
                return time.strftime('%H:%M:%S', local_time)
            else:
                return time.strftime('%I:%M %p', local_time)

        elif content_type == 'current_date':
            if format_str:
                return time.strftime(format_str, local_time)
            else:
                return time.strftime('%B %d, %Y', local_time)

        elif content_type == 'uptime':
            # This would need system uptime - placeholder
            return "2d 14h 32m"

        elif content_type == 'counter':
            # Placeholder for custom counters
            return "42"

        else:
            return f"[{content_type}]"

    def _render_text_shadow(self, surface: pygame.Surface, text_surface: pygame.Surface,
                           x: int, y: int, shadow_config: Dict[str, Any]) -> None:
        """Render text shadow"""
        shadow_color = self._parse_color(shadow_config.get('color', '#000000'))
        blur = shadow_config.get('blur', 0)
        offset = shadow_config.get('offset', {'x': 1, 'y': 1})

        # Create shadow surface
        shadow_surface = text_surface.copy()
        shadow_surface.fill(shadow_color, special_flags=pygame.BLEND_RGBA_MULT)

        # Apply blur effect (simplified)
        if blur > 0:
            # Basic blur approximation
            for _ in range(blur):
                shadow_surface = pygame.transform.smoothscale(shadow_surface, (text_surface.get_width() - 1, text_surface.get_height() - 1))
                shadow_surface = pygame.transform.smoothscale(shadow_surface, (text_surface.get_width(), text_surface.get_height()))

        # Blit shadow
        surface.blit(shadow_surface, (x + offset.get('x', 1), y + offset.get('y', 1)))

    def _get_font(self, font_name: str, size: int) -> Optional[pygame.font.Font]:
        """Get or create font with caching"""
        cache_key = f"{font_name}_{size}"

        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        # Try to load font (placeholder - full font management in Phase 2C)
        try:
            # For now, use default system fonts
            font = pygame.font.SysFont(font_name, size)
            self.font_cache[cache_key] = font
            return font
        except Exception as e:
            self.logger.error(f"Failed to load font {font_name}: {e}")
            return None

    def _parse_color(self, color_str: Optional[str]) -> Tuple[int, int, int, int]:
        """Parse color string to RGBA tuple"""
        if not color_str:
            return (255, 255, 255, 255)  # Default white

        if color_str.startswith('#'):
            # Hex color
            hex_str = color_str[1:]
            if len(hex_str) == 6:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                return (r, g, b, 255)
            elif len(hex_str) == 8:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                a = int(hex_str[6:8], 16)
                return (r, g, b, a)

        # Named colors (basic support)
        named_colors = {
            'black': (0, 0, 0, 255),
            'white': (255, 255, 255, 255),
            'red': (255, 0, 0, 255),
            'green': (0, 255, 0, 255),
            'blue': (0, 0, 255, 255),
            'yellow': (255, 255, 0, 255),
            'cyan': (0, 255, 255, 255),
            'magenta': (255, 0, 255, 255),
            'gray': (128, 128, 128, 255),
            'orange': (255, 165, 0, 255),
            'purple': (128, 0, 128, 255),
        }

        return named_colors.get(color_str.lower(), (255, 255, 255, 255))

    def _resolve_position(self, position: Any) -> Tuple[int, int]:
        """Resolve position to x,y coordinates"""
        if isinstance(position, dict):
            return position.get('x', 0), position.get('y', 0)
        elif isinstance(position, str):
            # Named positions
            positions = {
                'center': (self.display_width // 2, self.display_height // 2),
                'top-left': (0, 0),
                'top-right': (self.display_width, 0),
                'bottom-left': (0, self.display_height),
                'bottom-right': (self.display_width, self.display_height),
            }
            return positions.get(position, (0, 0))
        else:
            return (0, 0)

    def _calculate_position(self, position: Any, element_size: Tuple[int, int],
                           align: str = 'left') -> Tuple[int, int]:
        """Calculate position with alignment"""
        x, y = self._resolve_position(position)
        element_width, element_height = element_size

        # Apply alignment
        if align == 'center':
            x -= element_width // 2
        elif align == 'right':
            x -= element_width

        return x, y

    def render_lms_file(self, lms_path: Path) -> Optional[pygame.Surface]:
        """
        Render LMS file directly to surface

        Args:
            lms_path: Path to .lms file

        Returns:
            Rendered surface or None if failed
        """
        try:
            from .parser import LMSParser

            parser = LMSParser()
            lms_data = parser.parse_file(lms_path)

            return self.render_lms_to_surface(lms_data)

        except Exception as e:
            self.logger.error(f"Failed to render LMS file {lms_path}: {e}")
            return None

    def cleanup(self) -> None:
        """Clean up resources"""
        pygame.quit()

# Convenience functions
def render_lms_to_image(lms_data: Dict[str, Any], output_path: Path,
                       display_size: Tuple[int, int] = (1920, 1080)) -> bool:
    """Render LMS data to image file"""
    renderer = LMSRenderer(display_size)

    try:
        surface = renderer.render_lms_to_surface(lms_data)

        # Save as PNG
        pygame.image.save(surface, str(output_path))

        renderer.cleanup()
        return True

    except Exception as e:
        logging.error(f"Failed to render LMS to image: {e}")
        renderer.cleanup()
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='LMS Renderer')
    parser.add_argument('lms_file', help='Path to .lms file to render')
    parser.add_argument('--output', '-o', help='Output image path')
    parser.add_argument('--width', type=int, default=1920, help='Display width')
    parser.add_argument('--height', type=int, default=1080, help='Display height')
    parser.add_argument('--display', action='store_true', help='Display rendered result')

    args = parser.parse_args()

    renderer = LMSRenderer((args.width, args.height))

    # Render LMS file
    surface = renderer.render_lms_file(Path(args.lms_file))

    if surface:
        if args.display:
            # Create a window to display the result
            screen = pygame.display.set_mode((args.width, args.height))
            pygame.display.set_caption("LMS Render Preview")

            screen.blit(surface, (0, 0))
            pygame.display.flip()

            print("Press ESC to exit preview")
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False

        if args.output:
            pygame.image.save(surface, args.output)
            print(f"Rendered image saved to: {args.output}")

        print("✅ LMS file rendered successfully!")
    else:
        print("❌ Failed to render LMS file")

    renderer.cleanup()