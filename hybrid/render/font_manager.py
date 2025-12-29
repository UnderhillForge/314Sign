#!/usr/bin/env python3
"""
Font Management System
Handles font loading, caching, and rendering for LMS text overlays
"""

import pygame
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import os

class FontManager:
    """
    Manages font loading and caching for text rendering
    Supports system fonts and custom font files
    """

    def __init__(self, fonts_dir: str = "/home/pi/fonts", system_fonts_dir: str = "/usr/share/fonts"):
        self.fonts_dir = Path(fonts_dir)
        self.system_fonts_dir = Path(system_fonts_dir)
        self.font_cache: Dict[str, pygame.font.Font] = {}
        self.font_paths: Dict[str, Path] = {}

        # Create fonts directory if it doesn't exist
        self.fonts_dir.mkdir(exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize font discovery
        self._discover_fonts()

    def _discover_fonts(self) -> None:
        """Discover available fonts from system and custom directories"""
        self.logger.info("Discovering available fonts...")

        # Common font names to try (case-insensitive)
        common_fonts = [
            'Arial', 'Helvetica', 'DejaVuSans', 'LiberationSans', 'Ubuntu',
            'Times', 'TimesNewRoman', 'Georgia', 'DejaVuSerif', 'LiberationSerif',
            'Courier', 'CourierNew', 'DejaVuSansMono', 'LiberationMono', 'UbuntuMono',
            'ComicSans', 'Impact', 'Verdana', 'Tahoma', 'TrebuchetMS'
        ]

        # Custom font mappings for better rendering
        custom_font_mappings = {
            'BebasNeue': ['BebasNeue-Regular.ttf', 'BebasNeue-Bold.ttf'],
            'Lato': ['Lato-Regular.ttf', 'Lato-Bold.ttf', 'Lato-Italic.ttf'],
            'PermanentMarker': ['PermanentMarker-Regular.ttf'],
            'Caveat': ['Caveat-Regular.ttf', 'Caveat-Bold.ttf'],
            'ShadowsIntoLight': ['ShadowsIntoLight-Regular.ttf'],
            'WalterTurncoat': ['WalterTurncoat-Regular.ttf']
        }

        # Check for custom fonts first
        for font_name, filenames in custom_font_mappings.items():
            for filename in filenames:
                font_path = self.fonts_dir / filename
                if font_path.exists():
                    self.font_paths[font_name.lower()] = font_path
                    self.logger.debug(f"Found custom font: {font_name} -> {font_path}")
                    break

        # Check system fonts directory
        if self.system_fonts_dir.exists():
            for root, dirs, files in os.walk(self.system_fonts_dir):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf')):
                        font_path = Path(root) / file
                        # Extract font name from filename
                        name = file.rsplit('.', 1)[0]
                        # Clean up common patterns
                        name = name.replace('-Regular', '').replace('-Bold', '').replace('_', ' ')
                        self.font_paths[name.lower()] = font_path

        # Test common fonts
        for font_name in common_fonts:
            try:
                # Try to create a test font
                test_font = pygame.font.SysFont(font_name, 12)
                if test_font:
                    self.font_paths[font_name.lower()] = None  # System font
                    self.logger.debug(f"Available system font: {font_name}")
            except:
                pass

        self.logger.info(f"Font discovery complete. Found {len(self.font_paths)} fonts.")

    def get_font(self, font_name: str, size: int) -> Optional[pygame.font.Font]:
        """
        Get a font object for the specified name and size
        Uses caching for performance
        """
        cache_key = f"{font_name.lower()}_{size}"

        # Check cache first
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        # Try to load/create the font
        font = self._load_font(font_name, size)

        if font:
            # Cache the font (but limit cache size)
            if len(self.font_cache) < 100:  # Arbitrary limit
                self.font_cache[cache_key] = font
            return font

        return None

    def _load_font(self, font_name: str, size: int) -> Optional[pygame.font.Font]:
        """Load a font by name and size"""
        font_name_lower = font_name.lower()

        # Check if we have a path for this font
        if font_name_lower in self.font_paths:
            font_path = self.font_paths[font_name_lower]

            if font_path:  # Custom font file
                try:
                    font = pygame.font.Font(str(font_path), size)
                    self.logger.debug(f"Loaded custom font: {font_name} (size {size})")
                    return font
                except Exception as e:
                    self.logger.warning(f"Failed to load custom font {font_name}: {e}")
            else:  # System font
                try:
                    font = pygame.font.SysFont(font_name, size)
                    if font:
                        self.logger.debug(f"Loaded system font: {font_name} (size {size})")
                        return font
                except Exception as e:
                    self.logger.warning(f"Failed to load system font {font_name}: {e}")

        # Try some variations and fallbacks
        variations = [
            font_name,  # Exact match
            font_name.replace(' ', ''),  # Remove spaces
            font_name.replace(' ', '-'),  # Hyphenate
            font_name.split()[0],  # First word only
        ]

        for variation in variations:
            variation_lower = variation.lower()
            if variation_lower in self.font_paths:
                font_path = self.font_paths[variation_lower]

                try:
                    if font_path:  # Custom font
                        font = pygame.font.Font(str(font_path), size)
                    else:  # System font
                        font = pygame.font.SysFont(variation, size)

                    if font:
                        self.logger.debug(f"Loaded font variation: {variation} -> {font_name} (size {size})")
                        # Cache the mapping for future use
                        self.font_paths[font_name_lower] = font_path
                        return font

                except Exception as e:
                    self.logger.debug(f"Failed to load font variation {variation}: {e}")

        # Final fallback to default system font
        try:
            font = pygame.font.SysFont(None, size)  # Default system font
            if font:
                self.logger.debug(f"Using default system font for {font_name} (size {size})")
                return font
        except Exception as e:
            self.logger.error(f"Failed to load any font for {font_name}: {e}")

        return None

    def get_available_fonts(self) -> List[str]:
        """Get list of available font names"""
        return sorted(self.font_paths.keys())

    def get_font_info(self, font_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific font"""
        font_name_lower = font_name.lower()

        if font_name_lower not in self.font_paths:
            return None

        font_path = self.font_paths[font_name_lower]

        info = {
            'name': font_name,
            'type': 'custom' if font_path else 'system',
            'path': str(font_path) if font_path else None,
        }

        # Try to get font metrics
        try:
            test_font = self.get_font(font_name, 24)
            if test_font:
                # Test rendering to get metrics
                test_surface = test_font.render("Test", True, (255, 255, 255))
                info['metrics'] = {
                    'height': test_font.get_height(),
                    'ascent': test_font.get_ascent(),
                    'descent': test_font.get_descent(),
                    'test_width': test_surface.get_width()
                }
        except Exception as e:
            info['error'] = str(e)

        return info

    def preload_fonts(self, font_list: List[Tuple[str, int]]) -> None:
        """Preload commonly used fonts for better performance"""
        self.logger.info(f"Preloading {len(font_list)} fonts...")

        for font_name, size in font_list:
            font = self.get_font(font_name, size)
            if font:
                self.logger.debug(f"Preloaded: {font_name} (size {size})")
            else:
                self.logger.warning(f"Failed to preload: {font_name} (size {size})")

    def clear_cache(self) -> None:
        """Clear the font cache to free memory"""
        cache_size = len(self.font_cache)
        self.font_cache.clear()
        self.logger.info(f"Cleared font cache: {cache_size} fonts removed")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_fonts': len(self.font_cache),
            'available_fonts': len(self.font_paths),
            'cache_keys': list(self.font_cache.keys())[:10]  # First 10 for debugging
        }

    def add_custom_font(self, font_path: str, font_name: Optional[str] = None) -> bool:
        """Add a custom font file to the font manager"""
        path = Path(font_path)

        if not path.exists():
            self.logger.error(f"Font file does not exist: {font_path}")
            return False

        if not path.suffix.lower() in ['.ttf', '.otf']:
            self.logger.error(f"Unsupported font format: {path.suffix}")
            return False

        # Determine font name
        if not font_name:
            font_name = path.stem

        # Clean up font name
        font_name = font_name.replace('-Regular', '').replace('-Bold', '').replace('_', ' ')

        self.font_paths[font_name.lower()] = path
        self.logger.info(f"Added custom font: {font_name} -> {path}")

        return True

    def test_font_rendering(self, font_name: str, text: str = "Test 123", sizes: List[int] = [12, 24, 36, 48]) -> Dict[str, Any]:
        """Test font rendering at different sizes"""
        results = {}

        for size in sizes:
            try:
                font = self.get_font(font_name, size)
                if font:
                    surface = font.render(text, True, (255, 255, 255))
                    results[size] = {
                        'success': True,
                        'width': surface.get_width(),
                        'height': surface.get_height(),
                        'font_height': font.get_height(),
                        'ascent': font.get_ascent(),
                        'descent': font.get_descent()
                    }
                else:
                    results[size] = {'success': False, 'error': 'Font not found'}
            except Exception as e:
                results[size] = {'success': False, 'error': str(e)}

        return results

# Global instance for easy access
_font_manager = None

def get_font_manager() -> FontManager:
    """Get the global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager

def get_font(font_name: str, size: int) -> Optional[pygame.font.Font]:
    """Global function to get a font"""
    manager = get_font_manager()
    return manager.get_font(font_name, size)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Font Manager Test')
    parser.add_argument('--list', action='store_true', help='List available fonts')
    parser.add_argument('--info', help='Get info for specific font')
    parser.add_argument('--test', help='Test rendering for font')
    parser.add_argument('--add-font', help='Add custom font file')
    parser.add_argument('--font-name', help='Name for added font')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')

    args = parser.parse_args()

    # Initialize pygame for font testing
    pygame.init()

    manager = FontManager()

    try:
        if args.list:
            fonts = manager.get_available_fonts()
            print(f"Available Fonts ({len(fonts)}):")
            for font in fonts[:20]:  # Show first 20
                print(f"  {font}")
            if len(fonts) > 20:
                print(f"  ... and {len(fonts) - 20} more")

        elif args.info:
            info = manager.get_font_info(args.info)
            if info:
                print(f"Font Info: {args.info}")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Font not found: {args.info}")

        elif args.test:
            results = manager.test_font_rendering(args.test)
            print(f"Font Test: {args.test}")
            for size, result in results.items():
                status = "✓" if result['success'] else "✗"
                print(f"  Size {size}: {status}")
                if result['success']:
                    print(f"    Width: {result['width']}, Height: {result['height']}")
                else:
                    print(f"    Error: {result['error']}")

        elif args.add_font:
            success = manager.add_custom_font(args.add_font, args.font_name)
            if success:
                print(f"✓ Added font: {args.font_name or Path(args.add_font).stem}")
            else:
                print("✗ Failed to add font")

        elif args.stats:
            stats = manager.get_cache_stats()
            print("Font Manager Statistics:")
            print(f"  Available Fonts: {stats['available_fonts']}")
            print(f"  Cached Fonts: {stats['cached_fonts']}")
            if stats['cache_keys']:
                print("  Cache Keys (first 10):")
                for key in stats['cache_keys']:
                    print(f"    {key}")

        else:
            # Demo
            print("Font Manager Demo")
            print("=" * 30)

            # Test a few fonts
            test_fonts = ['Arial', 'Times', 'Courier', 'BebasNeue']
            print("Testing common fonts:")

            for font_name in test_fonts:
                font = manager.get_font(font_name, 24)
                if font:
                    print(f"  ✓ {font_name}")
                else:
                    print(f"  ✗ {font_name}")

            print(f"\nTotal available fonts: {len(manager.get_available_fonts())}")

            # Show cache stats
            stats = manager.get_cache_stats()
            print(f"Cached fonts: {stats['cached_fonts']}")

    finally:
        pygame.quit()