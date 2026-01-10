#!/usr/bin/env python3
"""
314Sign Test Content Generator
Creates sample LMS files and slideshows for testing the display system
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Any

class TestContentGenerator:
    """Generates test content for 314Sign display validation"""

    def __init__(self, output_dir: str = "test_content"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Sample data
        self.fonts = ['Arial', 'Lato', 'BebasNeue', 'PermanentMarker']
        self.colors = [
            '#FF6B35', '#F7931E', '#FFE135', '#00A676',
            '#2E86AB', '#A23B72', '#F18F01', '#C73E1D'
        ]

    def generate_all_test_content(self) -> Dict[str, List[str]]:
        """Generate all types of test content"""
        results = {}

        # Generate LMS test files
        results['lms'] = self.generate_lms_test_files()

        # Generate slideshow test files
        results['slideshows'] = self.generate_slideshow_test_files()

        # Generate package test
        results['packages'] = self.generate_package_test()

        print("Test Content Generation Complete!")
        print("=================================")

        for content_type, files in results.items():
            print(f"{content_type.upper()}: {len(files)} files")
            for file in files:
                print(f"  • {file}")

        return results

    def generate_lms_test_files(self) -> List[str]:
        """Generate various LMS test files"""
        files = []

        # Basic text display
        files.append(self._create_basic_text_lms())

        # Restaurant menu
        files.append(self._create_restaurant_menu_lms())

        # Classroom schedule
        files.append(self._create_classroom_schedule_lms())

        # Performance test (many elements)
        files.append(self._create_performance_test_lms())

        # Dynamic content test
        files.append(self._create_dynamic_content_lms())

        return files

    def generate_slideshow_test_files(self) -> List[str]:
        """Generate slideshow test files"""
        files = []

        # Basic slideshow
        files.append(self._create_basic_slideshow())

        # Image slideshow
        files.append(self._create_image_slideshow())

        # Mixed content slideshow
        files.append(self._create_mixed_slideshow())

        return files

    def generate_package_test(self) -> List[str]:
        """Generate test package"""
        from package_314sign import SignPackage

        # Create a test LMS file
        test_lms = self._create_basic_text_lms()

        # Create package
        package_tool = SignPackage()
        package_path = package_tool.create_package(
            lms_path=Path(test_lms),
            author="314Sign Test Suite",
            description="Test package for validation"
        )

        return [str(package_path)]

    def _create_basic_text_lms(self) -> str:
        """Create basic text display LMS"""
        lms_data = {
            "version": "1.0",
            "background": {
                "image": "background.jpg",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Valid empty SHA256
                "brightness": 1.0,
                "blur": 0.0,
                "position": "center"
            },
            "overlays": [
                {
                    "type": "text",
                    "content": "314Sign Display Test",
                    "font": "BebasNeue",
                    "size": 72,
                    "color": "#FFFFFF",
                    "position": {"x": 960, "y": 200}
                },
                {
                    "type": "text",
                    "content": "System Status: ACTIVE",
                    "font": "Arial",
                    "size": 36,
                    "color": "#00FF00",
                    "position": {"x": 960, "y": 350}
                },
                {
                    "type": "text",
                    "content": "Display Resolution: 1920x1080",
                    "font": "Arial",
                    "size": 24,
                    "color": "#CCCCCC",
                    "position": {"x": 960, "y": 450}
                },
                {
                    "type": "dynamic",
                    "content": "current_time",
                    "format": "HH:MM:SS",
                    "font": "Arial",
                    "size": 48,
                    "color": "#FFD700",
                    "position": {"x": 960, "y": 550}
                },
                {
                    "type": "text",
                    "content": f"Test ID: {random.randint(1000, 9999)}",
                    "font": "Arial",
                    "size": 18,
                    "color": "#888888",
                    "position": {"x": 960, "y": 650}
                }
            ],
            "animations": [
                {
                    "element": "title",
                    "type": "fade_in",
                    "duration": 2.0,
                    "delay": 0.0
                }
            ],
            "global_settings": {
                "background_color": "#000000",
                "default_font": "Arial",
                "antialiasing": True
            }
        }

        filepath = self.output_dir / "basic_text_test.lms"
        with open(filepath, 'w') as f:
            json.dump(lms_data, f, indent=2)

        return str(filepath)

    def _create_restaurant_menu_lms(self) -> str:
        """Create restaurant menu LMS"""
        lms_data = {
            "version": "1.0",
            "background": {
                "image": "restaurant-bg.jpg",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "brightness": 0.9,
                "blur": 0.0,
                "position": "center"
            },
            "overlays": [
                {
                    "type": "text",
                    "content": "Welcome to 314Sign Café",
                    "font": "BebasNeue",
                    "size": 64,
                    "color": "#FFD700",
                    "position": {"x": 100, "y": 50}
                },
                {
                    "type": "text",
                    "content": "Daily Specials",
                    "font": "Lato",
                    "size": 48,
                    "color": "#FFFFFF",
                    "position": {"x": 100, "y": 150}
                },
                {
                    "type": "text",
                    "content": "Grilled Salmon",
                    "font": "Lato",
                    "size": 32,
                    "color": "#FFFFFF",
                    "position": {"x": 100, "y": 220}
                },
                {
                    "type": "text",
                    "content": "$24.95",
                    "font": "Lato",
                    "size": 28,
                    "color": "#FFD700",
                    "position": {"x": 400, "y": 225}
                },
                {
                    "type": "text",
                    "content": "Fresh Atlantic salmon with seasonal vegetables",
                    "font": "Lato",
                    "size": 20,
                    "color": "#CCCCCC",
                    "position": {"x": 100, "y": 255}
                },
                {
                    "type": "text",
                    "content": "Chicken Parmesan",
                    "font": "Lato",
                    "size": 32,
                    "color": "#FFFFFF",
                    "position": {"x": 100, "y": 300}
                },
                {
                    "type": "text",
                    "content": "$18.95",
                    "font": "Lato",
                    "size": 28,
                    "color": "#FFD700",
                    "position": {"x": 400, "y": 305}
                },
                {
                    "type": "text",
                    "content": "Traditional Italian favorite with marinara sauce",
                    "font": "Lato",
                    "size": 20,
                    "color": "#CCCCCC",
                    "position": {"x": 100, "y": 335}
                },
                {
                    "type": "dynamic",
                    "content": "current_time",
                    "format": "HH:MM",
                    "font": "Digital",
                    "size": 36,
                    "color": "#00FF00",
                    "position": {"x": 1600, "y": 50}
                },
                {
                    "type": "text",
                    "content": "Open Daily 7AM - 10PM",
                    "font": "Arial",
                    "size": 24,
                    "color": "#AAAAAA",
                    "position": {"x": 100, "y": 1000}
                }
            ],
            "animations": [
                {
                    "element": "specials",
                    "type": "slide_up",
                    "duration": 1.5,
                    "delay": 0.5
                }
            ],
            "global_settings": {
                "background_color": "#000000",
                "default_font": "Arial",
                "antialiasing": True
            }
        }

        filepath = self.output_dir / "restaurant_menu_test.lms"
        with open(filepath, 'w') as f:
            json.dump(lms_data, f, indent=2)

        return str(filepath)

    def _create_classroom_schedule_lms(self) -> str:
        """Create classroom schedule LMS"""
        lms_data = {
            "version": "1.0",
            "background": {
                "image": "classroom-bg.jpg",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "brightness": 1.0,
                "blur": 0.0,
                "position": "center"
            },
            "overlays": [
                {
                    "type": "text",
                    "content": "Room 314 - Computer Lab",
                    "font": "Arial",
                    "size": 48,
                    "color": "#2E86AB",
                    "position": {"x": 50, "y": 30}
                },
                {
                    "type": "dynamic",
                    "content": "current_date",
                    "format": "Day, Month DD, YYYY",
                    "font": "Arial",
                    "size": 24,
                    "color": "#666666",
                    "position": {"x": 50, "y": 100}
                },
                {
                    "type": "dynamic",
                    "content": "current_time",
                    "format": "HH:MM",
                    "font": "Digital",
                    "size": 72,
                    "color": "#FF6B35",
                    "position": {"x": 1600, "y": 30}
                },
                {
                    "type": "text",
                    "content": "Today's Schedule",
                    "font": "Arial",
                    "size": 36,
                    "color": "#2E86AB",
                    "position": {"x": 50, "y": 180}
                }
            ] + self._generate_schedule_entries() + [
                {
                    "type": "text",
                    "content": "Lab Rules:",
                    "font": "Arial",
                    "size": 24,
                    "color": "#2E86AB",
                    "position": {"x": 900, "y": 400}
                },
                {
                    "type": "text",
                    "content": "• Respect equipment",
                    "font": "Arial",
                    "size": 16,
                    "color": "#666666",
                    "position": {"x": 900, "y": 440}
                },
                {
                    "type": "text",
                    "content": "• No food or drinks",
                    "font": "Arial",
                    "size": 16,
                    "color": "#666666",
                    "position": {"x": 900, "y": 460}
                },
                {
                    "type": "text",
                    "content": "• Internet use monitored",
                    "font": "Arial",
                    "size": 16,
                    "color": "#666666",
                    "position": {"x": 900, "y": 480}
                }
            ],
            "animations": [
                {
                    "element": "schedule",
                    "type": "fade_in",
                    "duration": 1.0,
                    "delay": 0.0
                }
            ],
            "global_settings": {
                "background_color": "#FFFFFF",
                "default_font": "Arial",
                "antialiasing": True
            }
        }

        filepath = self.output_dir / "classroom_schedule_test.lms"
        with open(filepath, 'w') as f:
            json.dump(lms_data, f, indent=2)

        return str(filepath)

    def _generate_schedule_entries(self) -> List[Dict[str, Any]]:
        """Generate classroom schedule entries"""
        periods = [
            ("8:00 - 9:00", "Mathematics", "#2E86AB"),
            ("9:15 - 10:15", "English Literature", "#A23B72"),
            ("10:30 - 11:30", "Science Lab", "#F18F01"),
            ("11:45 - 12:45", "Physical Education", "#C73E1D"),
            ("1:30 - 2:30", "History", "#2E86AB"),
            ("2:45 - 3:45", "Computer Science", "#F7931E")
        ]

        entries = []
        y_pos = 250

        for time, subject, color in periods:
            entries.extend([
                {
                    "type": "text",
                    "content": time,
                    "font": "Arial",
                    "size": 20,
                    "color": "#333333",
                    "position": {"x": 80, "y": y_pos}
                },
                {
                    "type": "text",
                    "content": subject,
                    "font": "Arial",
                    "size": 24,
                    "color": color,
                    "position": {"x": 250, "y": y_pos - 2}
                }
            ])
            y_pos += 50

        return entries

    def _create_performance_test_lms(self) -> str:
        """Create performance test LMS with many elements"""
        overlays = []

        # Generate many text elements for performance testing
        for i in range(50):
            overlays.append({
                "type": "text",
                "content": f"Performance Test Element {i+1}",
                "font": random.choice(self.fonts),
                "size": random.randint(12, 36),
                "color": random.choice(self.colors),
                "position": {
                    "x": random.randint(50, 1800),
                    "y": random.randint(50, 1000)
                }
            })

        # Add some shapes for rendering performance
        for i in range(20):
            overlays.append({
                "type": "shape",
                "shape": "rectangle",
                "width": random.randint(50, 200),
                "height": random.randint(30, 100),
                "fill_color": random.choice(self.colors),
                "position": {
                    "x": random.randint(100, 1700),
                    "y": random.randint(100, 900)
                },
                "opacity": random.uniform(0.3, 0.8)
            })

        lms_data = {
            "version": "1.0",
            "background": {
                "image": "performance-bg.jpg",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "brightness": 1.0,
                "blur": 0.0,
                "position": "center"
            },
            "overlays": overlays,
            "animations": [],
            "global_settings": {
                "background_color": "#1a1a1a",
                "default_font": "Arial",
                "antialiasing": True
            }
        }

        filepath = self.output_dir / "performance_test.lms"
        with open(filepath, 'w') as f:
            json.dump(lms_data, f, indent=2)

        return str(filepath)

    def _create_dynamic_content_lms(self) -> str:
        """Create LMS with dynamic content elements"""
        lms_data = {
            "version": "1.0",
            "background": {
                "image": "dynamic-bg.jpg",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "brightness": 1.0,
                "blur": 0.0,
                "position": "center"
            },
            "overlays": [
                {
                    "type": "text",
                    "content": "Dynamic Content Test",
                    "font": "BebasNeue",
                    "size": 48,
                    "color": "#FFFFFF",
                    "position": {"x": 960, "y": 100}
                },
                {
                    "type": "dynamic",
                    "content": "current_time",
                    "format": "HH:MM:SS",
                    "font": "Digital",
                    "size": 64,
                    "color": "#00FF00",
                    "position": {"x": 960, "y": 200}
                },
                {
                    "type": "dynamic",
                    "content": "current_date",
                    "format": "Day, Month DD, YYYY",
                    "font": "Arial",
                    "size": 32,
                    "color": "#FFD700",
                    "position": {"x": 960, "y": 300}
                },
                {
                    "type": "text",
                    "content": "System Information:",
                    "font": "Arial",
                    "size": 28,
                    "color": "#FFFFFF",
                    "position": {"x": 100, "y": 400}
                },
                {
                    "type": "text",
                    "content": f"Uptime: Testing active",
                    "font": "Arial",
                    "size": 20,
                    "color": "#CCCCCC",
                    "position": {"x": 100, "y": 450}
                },
                {
                    "type": "text",
                    "content": f"Display: 1920x1080",
                    "font": "Arial",
                    "size": 20,
                    "color": "#CCCCCC",
                    "position": {"x": 100, "y": 480}
                },
                {
                    "type": "text",
                    "content": f"Test ID: {random.randint(10000, 99999)}",
                    "font": "Arial",
                    "size": 20,
                    "color": "#CCCCCC",
                    "position": {"x": 100, "y": 510}
                }
            ],
            "animations": [
                {
                    "element": "time",
                    "type": "pulse",
                    "duration": 1.0,
                    "delay": 0.0,
                    "loop": True
                }
            ],
            "global_settings": {
                "background_color": "#000033",
                "default_font": "Arial",
                "antialiasing": True
            }
        }

        filepath = self.output_dir / "dynamic_content_test.lms"
        with open(filepath, 'w') as f:
            json.dump(lms_data, f, indent=2)

        return str(filepath)

    def _create_basic_slideshow(self) -> str:
        """Create basic text-based slideshow"""
        slideshow_data = {
            "version": "1.0",
            "slides": [
                {
                    "type": "text",
                    "content": "Welcome to 314Sign",
                    "fontSize": 8,
                    "color": "#FFFFFF",
                    "duration": 3000
                },
                {
                    "type": "text",
                    "content": "Digital Signage System",
                    "fontSize": 6,
                    "color": "#FFD700",
                    "duration": 3000
                },
                {
                    "type": "text",
                    "content": "Performance Test",
                    "fontSize": 7,
                    "color": "#00FF00",
                    "duration": 3000
                },
                {
                    "type": "text",
                    "content": "Slideshow Complete",
                    "fontSize": 5,
                    "color": "#FF6B35",
                    "duration": 5000
                }
            ],
            "background_color": "#000000",
            "transition": "fade",
            "loop": True
        }

        filepath = self.output_dir / "basic_slideshow.json"
        with open(filepath, 'w') as f:
            json.dump(slideshow_data, f, indent=2)

        return str(filepath)

    def _create_image_slideshow(self) -> str:
        """Create image-based slideshow"""
        slideshow_data = {
            "version": "1.0",
            "slides": [
                {
                    "type": "image",
                    "media": "slide1.jpg",
                    "duration": 4000
                },
                {
                    "type": "image",
                    "media": "slide2.jpg",
                    "duration": 4000
                },
                {
                    "type": "image",
                    "media": "slide3.jpg",
                    "duration": 4000
                }
            ],
            "background_color": "#000000",
            "transition": "crossfade",
            "loop": True
        }

        filepath = self.output_dir / "image_slideshow.json"
        with open(filepath, 'w') as f:
            json.dump(slideshow_data, f, indent=2)

        return str(filepath)

    def _create_mixed_slideshow(self) -> str:
        """Create mixed content slideshow"""
        slideshow_data = {
            "version": "1.0",
            "slides": [
                {
                    "type": "text",
                    "content": "314Sign System Test",
                    "fontSize": 8,
                    "color": "#FFFFFF",
                    "duration": 2000
                },
                {
                    "type": "image",
                    "media": "test-image.jpg",
                    "duration": 3000
                },
                {
                    "type": "text",
                    "content": "Dynamic Content:",
                    "fontSize": 6,
                    "color": "#FFD700",
                    "duration": 1000
                },
                {
                    "type": "text",
                    "content": "Time and Date Display",
                    "fontSize": 5,
                    "color": "#00FF00",
                    "duration": 2000
                },
                {
                    "type": "text",
                    "content": "Performance: Excellent",
                    "fontSize": 7,
                    "color": "#FF6B35",
                    "duration": 3000
                }
            ],
            "background_color": "#000033",
            "transition": "slide",
            "loop": False
        }

        filepath = self.output_dir / "mixed_slideshow.json"
        with open(filepath, 'w') as f:
            json.dump(slideshow_data, f, indent=2)

        return str(filepath)

def main():
    """Command line interface for test content generation"""
    import argparse

    parser = argparse.ArgumentParser(
        description='314Sign Test Content Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_content_generator.py              # Generate all test content
  python3 test_content_generator.py --output ./test  # Custom output directory
  python3 test_content_generator.py --lms-only     # LMS files only
        """
    )

    parser.add_argument('--output', '-o', default='test_content',
                       help='Output directory for test files')
    parser.add_argument('--lms-only', action='store_true',
                       help='Generate only LMS test files')
    parser.add_argument('--slideshow-only', action='store_true',
                       help='Generate only slideshow test files')

    args = parser.parse_args()

    generator = TestContentGenerator(args.output)

    if args.lms_only:
        results = {'lms': generator.generate_lms_test_files()}
    elif args.slideshow_only:
        results = {'slideshows': generator.generate_slideshow_test_files()}
    else:
        results = generator.generate_all_test_content()

    print(f"\nTest content generated in: {args.output}")
    print("Use these files to test your 314Sign display system!")

if __name__ == "__main__":
    main()