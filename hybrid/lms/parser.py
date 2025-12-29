#!/usr/bin/env python3
"""
Lightweight Markup Script (LMS) Parser
Parses .lms files for the hybrid display system
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import time

class LMSParseError(Exception):
    """Custom exception for LMS parsing errors"""
    pass

class LMSParser:
    """Parser for Lightweight Markup Script (.lms) files"""

    def __init__(self):
        self.supported_versions = ["1.0", "1.1"]
        self.logger = logging.getLogger(__name__)

    def parse_file(self, lms_path: Path) -> Dict[str, Any]:
        """
        Parse an LMS file and return structured data

        Args:
            lms_path: Path to the .lms file

        Returns:
            Dict containing parsed LMS data

        Raises:
            LMSParseError: If parsing fails
        """
        try:
            with open(lms_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                raise LMSParseError("Empty LMS file")

            # Parse JSON content
            data = json.loads(content)

            # Validate structure
            self._validate_lms_structure(data)

            # Process and enhance data
            processed_data = self._process_lms_data(data, lms_path)

            return processed_data

        except json.JSONDecodeError as e:
            raise LMSParseError(f"Invalid JSON in LMS file: {e}")
        except FileNotFoundError:
            raise LMSParseError(f"LMS file not found: {lms_path}")
        except Exception as e:
            raise LMSParseError(f"Failed to parse LMS file: {e}")

    def _validate_lms_structure(self, data: Dict[str, Any]) -> None:
        """Validate the basic structure of LMS data"""
        if not isinstance(data, dict):
            raise LMSParseError("LMS data must be a JSON object")

        # Check version
        version = data.get('version')
        if not version:
            raise LMSParseError("Missing 'version' field")
        if version not in self.supported_versions:
            raise LMSParseError(f"Unsupported LMS version: {version}")

        # Check for required sections based on version
        if version == "1.0":
            if 'background' not in data:
                raise LMSParseError("LMS v1.0 requires 'background' section")
            if 'overlays' not in data:
                raise LMSParseError("LMS v1.0 requires 'overlays' section")

    def _process_lms_data(self, data: Dict[str, Any], lms_path: Path) -> Dict[str, Any]:
        """Process and enhance LMS data with additional metadata"""
        processed = data.copy()

        # Add file metadata
        processed['_metadata'] = {
            'source_file': str(lms_path),
            'parsed_at': time.time(),
            'file_hash': self._calculate_file_hash(lms_path)
        }

        # Process background section
        if 'background' in processed:
            processed['background'] = self._process_background(processed['background'])

        # Process overlays
        if 'overlays' in processed:
            processed['overlays'] = self._process_overlays(processed['overlays'])

        # Process animations
        if 'animations' in processed:
            processed['animations'] = self._process_animations(processed['animations'])

        # Add defaults for missing optional fields
        processed = self._add_defaults(processed)

        return processed

    def _process_background(self, background: Dict[str, Any]) -> Dict[str, Any]:
        """Process background configuration"""
        processed = background.copy()

        # Validate required fields
        if 'image' not in processed:
            raise LMSParseError("Background section must specify 'image'")

        # Add default values
        processed.setdefault('brightness', 1.0)
        processed.setdefault('blur', 0.0)
        processed.setdefault('position', 'center')
        processed.setdefault('hash', None)  # SHA256 hash for cache validation

        # Validate ranges
        if not (0.0 <= processed['brightness'] <= 2.0):
            raise LMSParseError("Background brightness must be between 0.0 and 2.0")
        if not (0.0 <= processed['blur'] <= 10.0):
            raise LMSParseError("Background blur must be between 0.0 and 10.0")

        # Validate hash format if provided
        if processed['hash'] and not self._is_valid_sha256(processed['hash']):
            raise LMSParseError("Background hash must be a valid SHA256 hash")

        return processed

    def _is_valid_sha256(self, hash_str: str) -> bool:
        """Validate SHA256 hash format"""
        if not hash_str or len(hash_str) != 64:
            return False
        try:
            int(hash_str, 16)
            return True
        except ValueError:
            return False

    def _process_overlays(self, overlays: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process overlay configurations"""
        processed_overlays = []

        for i, overlay in enumerate(overlays):
            try:
                processed = self._process_single_overlay(overlay, i)
                processed_overlays.append(processed)
            except Exception as e:
                raise LMSParseError(f"Error processing overlay {i}: {e}")

        return processed_overlays

    def _process_single_overlay(self, overlay: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Process a single overlay configuration"""
        processed = overlay.copy()

        # Validate required fields
        overlay_type = processed.get('type')
        if not overlay_type:
            raise LMSParseError(f"Overlay {index} missing 'type' field")

        # Type-specific validation and defaults
        if overlay_type == 'text':
            processed = self._process_text_overlay(processed)
        elif overlay_type == 'image':
            processed = self._process_image_overlay(processed)
        elif overlay_type == 'shape':
            processed = self._process_shape_overlay(processed)
        elif overlay_type == 'dynamic':
            processed = self._process_dynamic_overlay(processed)
        else:
            raise LMSParseError(f"Unknown overlay type: {overlay_type}")

        # Common overlay properties
        processed = self._add_common_overlay_properties(processed)

        return processed

    def _process_text_overlay(self, overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Process text overlay specific properties"""
        if 'content' not in overlay:
            raise LMSParseError("Text overlay missing 'content' field")

        # Add text-specific defaults
        overlay.setdefault('font', 'Arial')
        overlay.setdefault('size', 24)
        overlay.setdefault('color', '#FFFFFF')
        overlay.setdefault('align', 'left')
        overlay.setdefault('shadow', None)

        # Validate font size
        if not isinstance(overlay['size'], (int, float)) or overlay['size'] <= 0:
            raise LMSParseError("Text overlay size must be a positive number")

        return overlay

    def _process_image_overlay(self, overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Process image overlay specific properties"""
        if 'src' not in overlay:
            raise LMSParseError("Image overlay missing 'src' field")

        # Add image-specific defaults
        overlay.setdefault('width', None)
        overlay.setdefault('height', None)
        overlay.setdefault('opacity', 1.0)

        return overlay

    def _process_shape_overlay(self, overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Process shape overlay specific properties"""
        if 'shape' not in overlay:
            raise LMSParseError("Shape overlay missing 'shape' field")

        shape = overlay['shape']
        valid_shapes = ['rectangle', 'circle', 'line', 'polygon']
        if shape not in valid_shapes:
            raise LMSParseError(f"Invalid shape type: {shape}. Must be one of {valid_shapes}")

        # Add shape-specific defaults
        overlay.setdefault('fill_color', '#FFFFFF')
        overlay.setdefault('stroke_color', None)
        overlay.setdefault('stroke_width', 1)

        return overlay

    def _process_dynamic_overlay(self, overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Process dynamic content overlay specific properties"""
        if 'content' not in overlay:
            raise LMSParseError("Dynamic overlay missing 'content' field")

        # Validate dynamic content types
        valid_dynamic_types = [
            'current_time', 'current_date', 'weather_temp', 'weather_condition',
            'custom_variable', 'counter', 'uptime'
        ]

        if overlay['content'] not in valid_dynamic_types:
            raise LMSParseError(f"Unknown dynamic content type: {overlay['content']}")

        # Add dynamic-specific defaults
        overlay.setdefault('format', None)
        overlay.setdefault('update_interval', 60)  # seconds

        return overlay

    def _add_common_overlay_properties(self, overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Add common properties to all overlay types"""
        # Position (required for all overlays)
        if 'position' not in overlay:
            raise LMSParseError("Overlay missing required 'position' field")

        # Validate position format
        pos = overlay['position']
        if isinstance(pos, dict):
            if 'x' not in pos or 'y' not in pos:
                raise LMSParseError("Position object must contain 'x' and 'y' coordinates")
        elif isinstance(pos, str):
            valid_positions = ['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right']
            if pos not in valid_positions:
                raise LMSParseError(f"Invalid position string: {pos}. Must be one of {valid_positions}")
        else:
            raise LMSParseError("Position must be either an object {x, y} or a string")

        # Common optional properties
        overlay.setdefault('opacity', 1.0)
        overlay.setdefault('rotation', 0)
        overlay.setdefault('visible', True)

        # Validate ranges
        if not (0.0 <= overlay['opacity'] <= 1.0):
            raise LMSParseError("Overlay opacity must be between 0.0 and 1.0")
        if not (-360 <= overlay['rotation'] <= 360):
            raise LMSParseError("Overlay rotation must be between -360 and 360 degrees")

        return overlay

    def _process_animations(self, animations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process animation configurations"""
        processed_animations = []

        for i, animation in enumerate(animations):
            try:
                processed = animation.copy()

                # Validate required fields
                if 'element' not in animation:
                    raise LMSParseError(f"Animation {i} missing 'element' field")
                if 'type' not in animation:
                    raise LMSParseError(f"Animation {i} missing 'type' field")

                # Add animation defaults
                processed.setdefault('duration', 2.0)
                processed.setdefault('delay', 0.0)
                processed.setdefault('easing', 'linear')
                processed.setdefault('loop', False)

                processed_animations.append(processed)

            except Exception as e:
                raise LMSParseError(f"Error processing animation {i}: {e}")

        return processed_animations

    def _add_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for optional LMS fields"""
        # Global defaults
        data.setdefault('animations', [])
        data.setdefault('global_settings', {})

        # Global settings defaults
        global_settings = data['global_settings']
        global_settings.setdefault('background_color', '#000000')
        global_settings.setdefault('default_font', 'Arial')
        global_settings.setdefault('antialiasing', True)

        return data

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of the LMS file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    def validate_lms_for_display(self, lms_data: Dict[str, Any], display_resolution: Tuple[int, int]) -> List[str]:
        """
        Validate LMS data against display capabilities

        Args:
            lms_data: Parsed LMS data
            display_resolution: (width, height) of target display

        Returns:
            List of validation warnings/issues
        """
        warnings = []
        width, height = display_resolution

        # Check overlay positions
        for i, overlay in enumerate(lms_data.get('overlays', [])):
            pos = overlay['position']

            if isinstance(pos, dict):
                x, y = pos['x'], pos['y']
                if x < 0 or x > width:
                    warnings.append(f"Overlay {i} x-position {x} outside display bounds (0-{width})")
                if y < 0 or y > height:
                    warnings.append(f"Overlay {i} y-position {y} outside display bounds (0-{height})")

        # Check text sizes
        for i, overlay in enumerate(lms_data.get('overlays', [])):
            if overlay['type'] == 'text':
                size = overlay['size']
                if size > height * 0.8:
                    warnings.append(f"Overlay {i} text size {size} very large for display height {height}")

        return warnings

# Convenience functions
def parse_lms_file(file_path: str) -> Dict[str, Any]:
    """Parse an LMS file (convenience function)"""
    parser = LMSParser()
    return parser.parse_file(Path(file_path))

def parse_lms_string(content: str) -> Dict[str, Any]:
    """Parse LMS content from string (convenience function)"""
    import tempfile
    import os

    # Write to temporary file and parse
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lms', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        return parse_lms_file(temp_path)
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='LMS File Parser')
    parser.add_argument('file', help='Path to .lms file to parse')
    parser.add_argument('--validate', nargs=2, metavar=('WIDTH', 'HEIGHT'),
                       help='Validate for specific display resolution')

    args = parser.parse_args()

    try:
        lms_parser = LMSParser()
        data = lms_parser.parse_file(Path(args.file))

        print("✅ LMS file parsed successfully!")
        print(f"Version: {data.get('version')}")
        print(f"Background: {data.get('background', {}).get('image')}")
        print(f"Overlays: {len(data.get('overlays', []))}")
        print(f"Animations: {len(data.get('animations', []))}")

        if args.validate:
            width, height = int(args.validate[0]), int(args.validate[1])
            warnings = lms_parser.validate_lms_for_display(data, (width, height))
            if warnings:
                print("\n⚠️  Validation Warnings:")
                for warning in warnings:
                    print(f"  • {warning}")
            else:
                print(f"\n✅ Valid for {width}x{height} display")

    except LMSParseError as e:
        print(f"❌ Parse Error: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        exit(1)