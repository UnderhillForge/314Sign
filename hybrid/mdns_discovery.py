#!/usr/bin/env python3
"""
314Sign mDNS/Bonjour Device Discovery
Finds and manages 314Sign devices on the local network
"""

import socket
import time
import json
import threading
import subprocess
from typing import Dict, List, Optional, Callable
from pathlib import Path
import logging

class MDNSDiscovery:
    """
    mDNS/Bonjour service discovery for 314Sign devices
    """

    def __init__(self, service_type: str = "_314sign-main._tcp.local.",
                 timeout: int = 5):
        self.service_type = service_type
        self.timeout = timeout
        self.devices = {}  # device_id -> device_info
        self.callbacks = []  # Callbacks for device discovery
        self.running = False
        self.thread = None

    def add_callback(self, callback: Callable):
        """Add callback for device discovery events"""
        self.callbacks.append(callback)

    def _notify_callbacks(self, event: str, device_info: Dict):
        """Notify all callbacks of device events"""
        for callback in self.callbacks:
            try:
                callback(event, device_info)
            except Exception as e:
                logging.error(f"Callback error: {e}")

    def discover_devices(self) -> Dict[str, Dict]:
        """
        Discover 314Sign devices on the network using avahi-browse

        Returns:
            Dict mapping device_id to device information
        """
        devices = {}

        try:
            # Use avahi-browse to discover services
            cmd = [
                'avahi-browse',
                '-r',  # Resolve addresses
                '-t',  # Terminate after timeout
                '-p',  # Parseable output
                self.service_type
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('+ ') or line.startswith('= '):
                        parts = line.split(';')
                        if len(parts) >= 9:
                            # Parse avahi-browse output
                            interface, protocol, name, service_type, domain, hostname, address, port, txt = parts[:9]

                            # Extract device information from TXT records
                            device_info = self._parse_txt_records(txt)

                            if device_info and 'device_id' in device_info:
                                device_id = device_info['device_id']
                                device_info.update({
                                    'name': name,
                                    'hostname': hostname.rstrip('.'),
                                    'address': address,
                                    'port': int(port),
                                    'service_type': service_type,
                                    'discovered_at': time.time()
                                })

                                devices[device_id] = device_info
                                self._notify_callbacks('discovered', device_info)

        except subprocess.TimeoutExpired:
            logging.warning("mDNS discovery timed out")
        except Exception as e:
            logging.error(f"mDNS discovery error: {e}")

        # Update internal device list
        self.devices.update(devices)

        return devices

    def _parse_txt_records(self, txt_records: str) -> Dict[str, str]:
        """Parse TXT records from avahi-browse output"""
        records = {}

        # TXT records are space-separated key=value pairs
        if txt_records and txt_records != '(null)':
            pairs = txt_records.split('" "')
            for pair in pairs:
                pair = pair.strip('"')
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    records[key] = value

        return records

    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get information for a specific device"""
        return self.devices.get(device_id)

    def list_devices(self, service_filter: Optional[str] = None) -> List[Dict]:
        """List all discovered devices, optionally filtered by service type"""
        devices = list(self.devices.values())

        if service_filter:
            devices = [d for d in devices if d.get('service_type') == service_filter]

        return devices

    def monitor_devices(self):
        """Continuously monitor for device changes"""
        self.running = True

        while self.running:
            try:
                # Discover current devices
                current_devices = self.discover_devices()

                # Check for disappeared devices
                disappeared = set(self.devices.keys()) - set(current_devices.keys())
                for device_id in disappeared:
                    device_info = self.devices[device_id]
                    self._notify_callbacks('disappeared', device_info)
                    del self.devices[device_id]

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logging.error(f"Device monitoring error: {e}")
                time.sleep(10)  # Wait before retrying

    def start_monitoring(self):
        """Start background device monitoring"""
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.monitor_devices, daemon=True)
            self.thread.start()

    def stop_monitoring(self):
        """Stop device monitoring"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

class DeviceRegistration:
    """
    Device registration system for main kiosk to manage remote displays
    """

    def __init__(self, registration_file: str = "/home/pi/registered_devices.json"):
        self.registration_file = Path(registration_file)
        self.registrations = self._load_registrations()

    def _load_registrations(self) -> Dict[str, Dict]:
        """Load device registrations from file"""
        if self.registration_file.exists():
            try:
                with open(self.registration_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading registrations: {e}")

        return {}

    def _save_registrations(self):
        """Save device registrations to file"""
        try:
            self.registration_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registration_file, 'w') as f:
                json.dump(self.registrations, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving registrations: {e}")

    def register_device(self, device_code: str, device_info: Dict) -> bool:
        """
        Register a remote device

        Args:
            device_code: Device code from remote device
            device_info: Device information from discovery

        Returns:
            True if registration successful
        """
        if device_code not in self.registrations:
            registration = {
                'device_code': device_code,
                'device_id': device_info.get('device_id'),
                'hostname': device_info.get('hostname'),
                'address': device_info.get('address'),
                'registered_at': time.time(),
                'last_seen': time.time(),
                'status': 'active',
                'display_name': device_info.get('name', f"Remote {device_code}")
            }

            self.registrations[device_code] = registration
            self._save_registrations()

            logging.info(f"Registered device: {device_code}")
            return True

        return False

    def unregister_device(self, device_code: str) -> bool:
        """Unregister a device"""
        if device_code in self.registrations:
            del self.registrations[device_code]
            self._save_registrations()
            logging.info(f"Unregistered device: {device_code}")
            return True
        return False

    def update_device_status(self, device_code: str, status: str):
        """Update device status"""
        if device_code in self.registrations:
            self.registrations[device_code]['status'] = status
            self.registrations[device_code]['last_seen'] = time.time()
            self._save_registrations()

    def get_registered_devices(self) -> List[Dict]:
        """Get list of registered devices"""
        return list(self.registrations.values())

    def is_registered(self, device_code: str) -> bool:
        """Check if device is registered"""
        return device_code in self.registrations

def discover_main_kiosk(timeout: int = 10) -> Optional[Dict]:
    """
    Discover main kiosk on the network (for remote devices)

    Returns:
        Main kiosk information or None if not found
    """
    discovery = MDNSDiscovery("_314sign-main._tcp.local.", timeout)
    devices = discovery.discover_devices()

    # Return first main kiosk found
    for device_info in devices.values():
        if device_info.get('mode') == 'main':
            return device_info

    return None

def discover_remote_devices(timeout: int = 5) -> List[Dict]:
    """
    Discover remote devices on the network (for main kiosk)

    Returns:
        List of remote device information
    """
    discovery = MDNSDiscovery("_314sign-remote._tcp.local.", timeout)
    devices = discovery.discover_devices()

    return list(devices.values())

def main():
    """CLI interface for mDNS discovery"""
    import argparse

    parser = argparse.ArgumentParser(description='314Sign mDNS Device Discovery')
    parser.add_argument('--discover-main', action='store_true',
                       help='Discover main kiosk')
    parser.add_argument('--discover-remotes', action='store_true',
                       help='Discover remote devices')
    parser.add_argument('--monitor', action='store_true',
                       help='Monitor for device changes')
    parser.add_argument('--service-type', default='_314sign-main._tcp.local.',
                       help='Service type to discover')
    parser.add_argument('--timeout', type=int, default=5,
                       help='Discovery timeout in seconds')

    args = parser.parse_args()

    if args.discover_main:
        print("🔍 Discovering main kiosk...")
        kiosk = discover_main_kiosk(args.timeout)
        if kiosk:
            print("✅ Found main kiosk:")
            print(f"   Hostname: {kiosk.get('hostname')}")
            print(f"   Address: {kiosk.get('address')}")
            print(f"   Device ID: {kiosk.get('device_id')}")
        else:
            print("❌ No main kiosk found")

    elif args.discover_remotes:
        print("🔍 Discovering remote devices...")
        devices = discover_remote_devices(args.timeout)
        if devices:
            print(f"✅ Found {len(devices)} remote device(s):")
            for device in devices:
                print(f"   • {device.get('name')} ({device.get('hostname')})")
                print(f"     Status: {device.get('status', 'unknown')}")
        else:
            print("❌ No remote devices found")

    elif args.monitor:
        print("🔍 Monitoring for device changes (Ctrl+C to stop)...")

        def device_callback(event, device_info):
            print(f"📡 {event.upper()}: {device_info.get('name')} ({device_info.get('hostname')})")

        discovery = MDNSDiscovery(args.service_type, args.timeout)
        discovery.add_callback(device_callback)
        discovery.start_monitoring()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            discovery.stop_monitoring()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()