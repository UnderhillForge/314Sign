#!/usr/bin/env python3
"""
Dynamic Content Engine
Handles real-time content generation for LMS overlays
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
import subprocess
import re

class DynamicContentEngine:
    """
    Generates dynamic content for LMS overlays (time, weather, counters, etc.)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}  # Simple cache for expensive operations
        self.cache_timeout = 300  # 5 minutes

    def get_dynamic_content(self, content_type: str, format_str: Optional[str] = None,
                           parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Get dynamic content based on type

        Args:
            content_type: Type of dynamic content
            format_str: Format string for the content
            parameters: Additional parameters

        Returns:
            Formatted content string
        """
        try:
            if content_type == 'current_time':
                return self._get_current_time(format_str)
            elif content_type == 'current_date':
                return self._get_current_date(format_str)
            elif content_type == 'weather_temp':
                return self._get_weather_temp(format_str, parameters)
            elif content_type == 'weather_condition':
                return self._get_weather_condition(format_str, parameters)
            elif content_type == 'uptime':
                return self._get_system_uptime(format_str)
            elif content_type == 'counter':
                return self._get_counter_value(format_str, parameters)
            elif content_type == 'custom_variable':
                return self._get_custom_variable(format_str, parameters)
            else:
                self.logger.warning(f"Unknown dynamic content type: {content_type}")
                return f"[{content_type}]"

        except Exception as e:
            self.logger.error(f"Failed to generate dynamic content {content_type}: {e}")
            return f"[{content_type}:error]"

    def _get_current_time(self, format_str: Optional[str]) -> str:
        """Get current time in specified format"""
        now = datetime.now()

        if not format_str:
            return now.strftime('%I:%M %p')  # Default 12-hour format

        # Common format mappings
        format_mappings = {
            'HH:MM': '%H:%M',
            'HH:MM:SS': '%H:%M:%S',
            '12H': '%I:%M %p',
            '24H': '%H:%M'
        }

        format_code = format_mappings.get(format_str, format_str)
        return now.strftime(format_code)

    def _get_current_date(self, format_str: Optional[str]) -> str:
        """Get current date in specified format"""
        now = datetime.now()

        if not format_str:
            return now.strftime('%B %d, %Y')  # Default format

        # Common format mappings
        format_mappings = {
            'MM/DD/YYYY': '%m/%d/%Y',
            'DD/MM/YYYY': '%d/%m/%Y',
            'YYYY-MM-DD': '%Y-%m-%d',
            'Day, Month DD, YYYY': '%A, %B %d, %Y',
            'Mon DD': '%b %d'
        }

        format_code = format_mappings.get(format_str, format_str)
        return now.strftime(format_code)

    def _get_weather_temp(self, format_str: Optional[str], parameters: Optional[Dict[str, Any]]) -> str:
        """Get current weather temperature"""
        cache_key = 'weather_temp'

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Default location (would be configurable)
            location = parameters.get('location', 'New York') if parameters else 'New York'

            # Use wttr.in for weather data (simple API)
            url = f"http://wttr.in/{location}?format=%t"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            temp = response.text.strip()

            # Cache for 15 minutes
            self._set_cached(cache_key, temp, 900)

            # Apply format if specified
            if format_str == 'fahrenheit':
                # wttr.in returns Celsius by default, convert if needed
                # This is a simplified implementation
                pass

            return temp

        except Exception as e:
            self.logger.warning(f"Failed to get weather temp: {e}")
            return "--°C"

    def _get_weather_condition(self, format_str: Optional[str], parameters: Optional[Dict[str, Any]]) -> str:
        """Get current weather condition"""
        cache_key = 'weather_condition'

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            location = parameters.get('location', 'New York') if parameters else 'New York'

            # Use wttr.in for weather data
            url = f"http://wttr.in/{location}?format=%C"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            condition = response.text.strip()

            # Cache for 30 minutes (weather changes slower than temp)
            self._set_cached(cache_key, condition, 1800)

            return condition

        except Exception as e:
            self.logger.warning(f"Failed to get weather condition: {e}")
            return "Unknown"

    def _get_system_uptime(self, format_str: Optional[str]) -> str:
        """Get system uptime"""
        try:
            # Read from /proc/uptime
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])

            uptime_td = timedelta(seconds=uptime_seconds)

            if format_str == 'short':
                # Format as "2d 14h 32m"
                days = uptime_td.days
                hours, remainder = divmod(uptime_td.seconds, 3600)
                minutes, _ = divmod(remainder, 60)

                parts = []
                if days > 0:
                    parts.append(f"{days}d")
                if hours > 0 or days > 0:
                    parts.append(f"{hours}h")
                parts.append(f"{minutes}m")

                return " ".join(parts)
            else:
                # Default format
                days = uptime_td.days
                hours, remainder = divmod(uptime_td.seconds, 3600)
                minutes, _ = divmod(remainder, 60)

                if days > 0:
                    return f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"

        except Exception as e:
            self.logger.error(f"Failed to get uptime: {e}")
            return "Unknown"

    def _get_counter_value(self, format_str: Optional[str], parameters: Optional[Dict[str, Any]]) -> str:
        """Get counter value (persistent or session-based)"""
        counter_name = parameters.get('name', 'default') if parameters else 'default'
        cache_key = f"counter_{counter_name}"

        # Get current value
        current_value = self._get_cached(cache_key) or 0

        # Increment counter
        new_value = current_value + 1
        self._set_cached(cache_key, new_value, 86400)  # Persist for 24 hours

        # Format output
        if format_str:
            return format_str.format(count=new_value)
        else:
            return str(new_value)

    def _get_custom_variable(self, format_str: Optional[str], parameters: Optional[Dict[str, Any]]) -> str:
        """Get custom variable value"""
        var_name = parameters.get('name', 'unknown') if parameters else 'unknown'
        cache_key = f"custom_var_{var_name}"

        # Try to get from cache first
        cached_value = self._get_cached(cache_key)
        if cached_value:
            return cached_value

        # Try to get from external source
        try:
            # This could be extended to read from files, APIs, databases, etc.
            # For now, just return a placeholder
            return f"[{var_name}:not_set]"
        except Exception as e:
            self.logger.error(f"Failed to get custom variable {var_name}: {e}")
            return f"[{var_name}:error]"

    def _get_cached(self, key: str) -> Any:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_timeout:
                return value
            else:
                # Expired, remove from cache
                del self.cache[key]

        return None

    def _set_cached(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache with timestamp"""
        timeout = timeout or self.cache_timeout
        self.cache[key] = (value, time.time())

        # Clean up expired entries occasionally
        if len(self.cache) > 100:  # Arbitrary cleanup trigger
            self._cleanup_cache()

    def _cleanup_cache(self) -> None:
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []

        for key, (value, timestamp) in self.cache.items():
            if current_time - timestamp > self.cache_timeout:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_weather_data(self, location: str = "New York") -> Dict[str, Any]:
        """
        Get comprehensive weather data for a location
        Returns dict with temperature, condition, humidity, etc.
        """
        cache_key = f"weather_full_{location}"

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Get multiple weather data points
            base_url = f"http://wttr.in/{location}"

            # Temperature
            temp_response = requests.get(f"{base_url}?format=%t", timeout=5)
            temp = temp_response.text.strip() if temp_response.status_code == 200 else "N/A"

            # Condition
            cond_response = requests.get(f"{base_url}?format=%C", timeout=5)
            condition = cond_response.text.strip() if cond_response.status_code == 200 else "Unknown"

            # Humidity
            humid_response = requests.get(f"{base_url}?format=%h", timeout=5)
            humidity = humid_response.text.strip() if humid_response.status_code == 200 else "N/A"

            # Wind speed
            wind_response = requests.get(f"{base_url}?format=%w", timeout=5)
            wind = wind_response.text.strip() if wind_response.status_code == 200 else "N/A"

            weather_data = {
                'temperature': temp,
                'condition': condition,
                'humidity': humidity,
                'wind_speed': wind,
                'location': location,
                'updated': time.time()
            }

            # Cache for 15 minutes
            self._set_cached(cache_key, weather_data, 900)

            return weather_data

        except Exception as e:
            self.logger.warning(f"Failed to get weather data for {location}: {e}")
            return {
                'temperature': '--°C',
                'condition': 'Unknown',
                'humidity': 'N/A',
                'wind_speed': 'N/A',
                'location': location,
                'error': str(e)
            }

    def update_custom_variables(self, variables: Dict[str, Any]) -> None:
        """
        Update custom variables from external source
        This could be called by the main kiosk to update variables from a database or API
        """
        for name, value in variables.items():
            cache_key = f"custom_var_{name}"
            self._set_cached(cache_key, str(value), 3600)  # Cache for 1 hour

    def get_system_info(self) -> Dict[str, str]:
        """Get system information for dynamic display"""
        try:
            # CPU temperature
            cpu_temp = "Unknown"
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp_raw = int(f.read().strip())
                    cpu_temp = f"{temp_raw / 1000:.1f}°C"
            except:
                # Try vcgencmd for Raspberry Pi
                try:
                    result = subprocess.run(['vcgencmd', 'measure_temp'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Extract temperature from "temp=45.6'C"
                        temp_match = re.search(r'temp=([0-9.]+)', result.stdout)
                        if temp_match:
                            cpu_temp = f"{temp_match.group(1)}°C"
                except:
                    pass

            # Memory usage
            mem_info = {}
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith(('MemTotal:', 'MemAvailable:')):
                            key, value = line.split(':')
                            mem_info[key.strip()] = value.strip()
            except:
                pass

            memory_usage = "Unknown"
            if 'MemTotal' in mem_info and 'MemAvailable' in mem_info:
                total_kb = int(mem_info['MemTotal'].split()[0])
                available_kb = int(mem_info['MemAvailable'].split()[0])
                used_kb = total_kb - available_kb
                used_percent = (used_kb / total_kb) * 100
                memory_usage = f"{used_percent:.1f}%"

            return {
                'cpu_temperature': cpu_temp,
                'memory_usage': memory_usage,
                'hostname': subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip(),
                'uptime': self._get_system_uptime('short')
            }

        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {
                'cpu_temperature': 'Unknown',
                'memory_usage': 'Unknown',
                'hostname': 'Unknown',
                'uptime': 'Unknown'
            }

# Global instance for easy access
_dynamic_engine = None

def get_dynamic_content(content_type: str, format_str: Optional[str] = None,
                       parameters: Optional[Dict[str, Any]] = None) -> str:
    """Global function to get dynamic content"""
    global _dynamic_engine
    if _dynamic_engine is None:
        _dynamic_engine = DynamicContentEngine()
    return _dynamic_engine.get_dynamic_content(content_type, format_str, parameters)

def get_weather_data(location: str = "New York") -> Dict[str, Any]:
    """Global function to get weather data"""
    global _dynamic_engine
    if _dynamic_engine is None:
        _dynamic_engine = DynamicContentEngine()
    return _dynamic_engine.get_weather_data(location)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Dynamic Content Engine Test')
    parser.add_argument('--type', help='Dynamic content type')
    parser.add_argument('--format', help='Format string')
    parser.add_argument('--weather', help='Get weather for location')
    parser.add_argument('--system-info', action='store_true', help='Show system information')

    args = parser.parse_args()

    engine = DynamicContentEngine()

    if args.type:
        result = engine.get_dynamic_content(args.type, args.format)
        print(f"{args.type}: {result}")

    elif args.weather:
        weather = engine.get_weather_data(args.weather)
        print(f"Weather for {args.weather}:")
        for key, value in weather.items():
            print(f"  {key}: {value}")

    elif args.system_info:
        info = engine.get_system_info()
        print("System Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    else:
        # Demo all content types
        print("Dynamic Content Engine Demo:")
        print("=" * 40)

        content_types = [
            ('current_time', 'HH:MM'),
            ('current_date', 'Day, Month DD, YYYY'),
            ('uptime', 'short'),
            ('counter', None),
            ('counter', None),  # Should increment
        ]

        for content_type, format_str in content_types:
            result = engine.get_dynamic_content(content_type, format_str)
            print(f"{content_type}: {result}")

        print("\nWeather demo:")
        weather = engine.get_weather_data()
        print(f"Temperature: {weather['temperature']}")
        print(f"Condition: {weather['condition']}")

        print("\nSystem info:")
        info = engine.get_system_info()
        print(f"CPU Temp: {info['cpu_temperature']}")
        print(f"Memory: {info['memory_usage']}")
        print(f"Uptime: {info['uptime']}")