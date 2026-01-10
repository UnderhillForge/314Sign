#!/usr/bin/env python3
"""
314Sign Mobile HTML Generator
Generates mobile-optimized HTML views of current display content for QR code access
"""

import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

class MobileHTMLGenerator:
    """
    Generates mobile-optimized HTML for current display content
    Used by main kiosk for QR code mobile access
    """

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path("/var/www/314sign/templates")
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load HTML templates"""
        try:
            mobile_template = self.template_dir / "mobile.html"
            if mobile_template.exists():
                with open(mobile_template, 'r', encoding='utf-8') as f:
                    self.templates['mobile'] = f.read()
            else:
                self.templates['mobile'] = self._get_default_mobile_template()

        except Exception as e:
            print(f"Failed to load templates: {e}")
            self.templates['mobile'] = self._get_default_mobile_template()

    def _get_default_mobile_template(self) -> str:
        """Default mobile template if file not found"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>314Sign Mobile View</title>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial; background: #000; color: white; }
        .content { max-width: 100%; }
        .header { text-align: center; margin-bottom: 20px; }
        .qr-notice { background: #333; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .timestamp { color: #ccc; font-size: 0.9em; }
        .display-content { padding: 20px; background: #111; border-radius: 8px; margin: 20px 0; }
        .lms-content { background: #222; padding: 15px; border-radius: 6px; margin: 10px 0; }
        .slideshow-info { background: #333; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="content">
        <div class="header">
            <h1>314Sign Display</h1>
            <div class="qr-notice">
                📱 Mobile view of current display content
            </div>
        </div>

        <div id="display-content" class="display-content">
            <p>Loading current display content...</p>
        </div>

        <div class="timestamp" id="timestamp">
            Last updated: Loading...
        </div>
    </div>

    <script>
        // Content will be populated by server
        const content = {{ content|tojson }};
        const timestamp = {{ timestamp|tojson }};

        function updateDisplay() {
            const container = document.getElementById('display-content');
            const timestampEl = document.getElementById('timestamp');

            if (content.type === 'lms') {
                container.innerHTML = `
                    <div class="lms-content">
                        <h2>LMS Content Active</h2>
                        <p>Content: ${content.content?.name || 'Unknown'}</p>
                        <p>Version: ${content.content?.version || 'Unknown'}</p>
                    </div>
                `;
            } else if (content.type === 'slideshow') {
                const slideInfo = content.slideshow_state ?
                    `Slide ${content.slideshow_state.current_slide + 1}` : 'Unknown';
                container.innerHTML = `
                    <div class="slideshow-info">
                        <h2>Slideshow Active</h2>
                        <p>Content: ${content.content?.name || 'Unknown'}</p>
                        <p>Current: ${slideInfo}</p>
                    </div>
                `;
            } else {
                container.innerHTML = '<p style="text-align: center; color: #666;">Display is in standby mode</p>';
            }

            timestampEl.textContent = `Last updated: ${new Date(timestamp * 1000).toLocaleTimeString()}`;
        }

        updateDisplay();
        // Auto-refresh every 30 seconds
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>"""

    def generate_mobile_html(self, current_content: Dict[str, Any], timestamp: Optional[float] = None) -> str:
        """
        Generate mobile HTML for current display content

        Args:
            current_content: Current display content data
            timestamp: Timestamp of content

        Returns:
            Mobile-optimized HTML string
        """
        if timestamp is None:
            timestamp = time.time()

        # Convert content to JSON-safe format
        content_json = json.dumps(current_content, default=str)
        timestamp_json = json.dumps(timestamp)

        # Replace template variables
        html = self.templates['mobile']
        html = html.replace('{{ content|tojson }}', content_json)
        html = html.replace('{{ timestamp|tojson }}', timestamp_json)

        return html

    def generate_qr_data(self, base_url: str, device_code: str) -> str:
        """
        Generate QR code data for mobile access

        Args:
            base_url: Base URL of the kiosk (e.g., "http://192.168.1.100:80")
            device_code: Device identifier

        Returns:
            URL for mobile access
        """
        return f"{base_url}/mobile?device={device_code}"

    def get_display_info(self, content_type: str, content_data: Any) -> Dict[str, Any]:
        """
        Extract display information for mobile view

        Args:
            content_type: Type of content ('lms', 'slideshow', 'standby')
            content_data: Content data

        Returns:
            Display info for mobile template
        """
        if content_type == 'lms':
            return {
                'type': 'lms',
                'name': getattr(content_data, 'name', 'Unknown LMS'),
                'version': getattr(content_data, 'version', 'Unknown'),
                'overlays': len(getattr(content_data, 'overlays', []))
            }
        elif content_type == 'slideshow':
            return {
                'type': 'slideshow',
                'name': getattr(content_data, 'name', 'Unknown Slideshow'),
                'slides': len(getattr(content_data, 'slides', [])),
                'current_slide': getattr(content_data, 'current_slide', 0) + 1
            }
        else:
            return {
                'type': 'standby',
                'message': 'Display is in standby mode'
            }


# Convenience functions
def generate_mobile_page(current_content: Dict[str, Any], base_url: str = "http://localhost:80") -> str:
    """Generate a complete mobile HTML page"""
    generator = MobileHTMLGenerator()
    return generator.generate_mobile_html(current_content)


def create_qr_url(base_url: str, device_code: str) -> str:
    """Create QR code URL for mobile access"""
    generator = MobileHTMLGenerator()
    return generator.generate_qr_data(base_url, device_code)


# Example usage
if __name__ == "__main__":
    # Example content data
    sample_content = {
        'type': 'lms',
        'content': {
            'name': 'restaurant-menu',
            'version': '1.0',
            'overlays': [
                {'type': 'text', 'content': 'Daily Specials'},
                {'type': 'text', 'content': '$24.95'}
            ]
        },
        'slideshow_state': None
    }

    generator = MobileHTMLGenerator()
    html = generator.generate_mobile_html(sample_content)

    # Save to file for testing
    with open('/tmp/mobile_test.html', 'w') as f:
        f.write(html)

    print("Mobile HTML generated and saved to /tmp/mobile_test.html")
    print(f"QR URL: {generator.generate_qr_data('http://192.168.1.100:80', 'MAIN_KIOSK')}")