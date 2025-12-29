#!/usr/bin/env python3
"""
314Sign LMS Bundle Manager
Creates and manages self-contained content bundles for distribution
to remote displays with 99.9% bandwidth reduction
"""

import json
import os
import hashlib
import tarfile
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import time
import shutil
import subprocess

class LMSBundleManager:
    """
    Manages creation, distribution, and installation of LMS content bundles
    """

    def __init__(self, lms_dir: str = "/home/pi/lms",
                 bundles_dir: str = "/var/lib/314sign/bundles",
                 assets_dir: str = "/var/lib/314sign/assets"):
        self.lms_dir = Path(lms_dir)
        self.bundles_dir = Path(bundles_dir)
        self.assets_dir = Path(assets_dir)

        # Create directories
        self.bundles_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def create_bundle(self, lms_file: str, bundle_name: Optional[str] = None,
                     version: str = "1.0", priority: str = "normal") -> str:
        """
        Create a self-contained bundle from LMS file

        Args:
            lms_file: Path to LMS JSON file
            bundle_name: Optional custom bundle name
            version: Bundle version
            priority: Distribution priority (critical, high, normal, low)

        Returns:
            Path to created bundle file
        """
        lms_path = Path(lms_file)
        if not lms_path.exists():
            raise FileNotFoundError(f"LMS file not found: {lms_file}")

        # Load LMS content
        with open(lms_path, 'r') as f:
            lms_data = json.load(f)

        # Generate bundle metadata
        timestamp = int(time.time())
        if bundle_name:
            safe_name = "".join(c for c in bundle_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
        else:
            safe_name = lms_path.stem

        bundle_id = "02d"

        # Collect all referenced assets
        assets = self._collect_assets(lms_data)

        # Create bundle metadata
        metadata = {
            "bundle_id": bundle_id,
            "content_type": self._detect_content_type(lms_data),
            "version": version,
            "priority": priority,
            "created_at": timestamp,
            "created_by": self._get_system_info(),
            "lms_filename": lms_path.name,
            "assets": list(assets.keys()),
            "display_size": lms_data.get("display_size", [1080, 1920]),
            "orientation": lms_data.get("orientation", "portrait"),
            "expires_at": None,
            "target_displays": [],
            "dependencies": [],
            "rollback_to": None
        }

        # Calculate checksums
        checksums = self._calculate_checksums(lms_path, assets)

        # Create temporary bundle directory
        with tempfile.TemporaryDirectory(prefix="314sign-bundle-") as temp_dir:
            bundle_temp = Path(temp_dir) / bundle_id
            bundle_temp.mkdir()

            # Copy LMS file
            shutil.copy2(lms_path, bundle_temp / "content.lms")

            # Copy assets
            if assets:
                assets_dir = bundle_temp / "assets"
                assets_dir.mkdir()
                for asset_name, asset_path in assets.items():
                    if asset_path.exists():
                        shutil.copy2(asset_path, assets_dir / asset_name)

            # Create metadata files
            with open(bundle_temp / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)

            with open(bundle_temp / "checksums.sha256", 'w') as f:
                for file_path, checksum in checksums.items():
                    f.write(f"{checksum}  {file_path}\n")

            # Create bundle archive
            bundle_path = self.bundles_dir / f"{bundle_id}.bundle"
            self._create_archive(bundle_temp, bundle_path)

        print(f"✅ Created bundle: {bundle_path}")
        print(f"   Bundle ID: {bundle_id}")
        print(f"   Assets: {len(assets)} files")
        print(f"   Size: {self._get_file_size(bundle_path)}")

        return str(bundle_path)

    def _collect_assets(self, lms_data: Dict[str, Any]) -> Dict[str, Path]:
        """Collect all assets referenced in LMS content"""
        assets = {}

        # Check overlays for asset references
        for overlay in lms_data.get("overlays", []):
            overlay_type = overlay.get("type", "")

            if overlay_type == "image":
                src = overlay.get("src", "")
                if src:
                    assets[src] = self._resolve_asset_path(src)

            # Check for font references
            font = overlay.get("font", "")
            if font and not font in ["Arial", "Times", "Courier"]:  # Skip system fonts
                assets[font] = self._resolve_asset_path(font, "fonts")

        # Check for background references
        if "background" in lms_data:
            bg_data = lms_data["background"]
            if isinstance(bg_data, dict) and "image" in bg_data:
                bg_image = bg_data["image"]
                assets[bg_image] = self._resolve_asset_path(bg_image, "backgrounds")

        return assets

    def _resolve_asset_path(self, asset_name: str, asset_type: str = "images") -> Path:
        """Resolve asset path based on type"""
        # Try different asset locations
        search_paths = [
            self.assets_dir / asset_type / asset_name,
            self.assets_dir / asset_name,
            Path("/var/lib/314sign") / asset_type / asset_name,
            Path("/home/pi") / asset_type / asset_name,
        ]

        for path in search_paths:
            if path.exists():
                return path

        # Return expected path even if it doesn't exist
        return self.assets_dir / asset_type / asset_name

    def _detect_content_type(self, lms_data: Dict[str, Any]) -> str:
        """Detect content type from LMS data"""
        overlays = lms_data.get("overlays", [])

        # Check for common content patterns
        has_time = any(o.get("type") == "time" for o in overlays)
        has_date = any(o.get("type") == "date" for o in overlays)

        if has_time and len(overlays) < 5:
            return "clock"
        elif any("menu" in str(o.get("content", "")).lower() for o in overlays):
            return "menu"
        elif any("schedule" in str(o.get("content", "")).lower() for o in overlays):
            return "schedule"
        elif len(overlays) > 10:
            return "complex"
        else:
            return "general"

    def _get_system_info(self) -> str:
        """Get system information for bundle metadata"""
        try:
            hostname = subprocess.run(['hostname'], capture_output=True, text=True, timeout=2)
            return hostname.stdout.strip()
        except:
            return "unknown"

    def _calculate_checksums(self, lms_path: Path, assets: Dict[str, Path]) -> Dict[str, str]:
        """Calculate SHA256 checksums for all files"""
        checksums = {}

        # Checksum LMS file
        checksums[lms_path.name] = self._calculate_file_checksum(lms_path)

        # Checksum assets
        for asset_name, asset_path in assets.items():
            if asset_path.exists():
                checksums[asset_name] = self._calculate_file_checksum(asset_path)

        return checksums

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _create_archive(self, source_dir: Path, archive_path: Path):
        """Create compressed archive from directory"""
        with tarfile.open(archive_path, "w:gz") as tar:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    tar.add(file_path, arcname=file_path.relative_to(source_dir))

    def _get_file_size(self, file_path: Path) -> str:
        """Get human-readable file size"""
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return ".1f"
            size /= 1024.0
        return ".1f"

    def list_bundles(self) -> List[Dict[str, Any]]:
        """List all available bundles with metadata"""
        bundles = []

        for bundle_file in self.bundles_dir.glob("*.bundle"):
            try:
                # Extract metadata from bundle
                with tarfile.open(bundle_file, "r:gz") as tar:
                    metadata_file = tar.extractfile("metadata.json")
                    if metadata_file:
                        metadata = json.load(metadata_file)
                        metadata["bundle_path"] = str(bundle_file)
                        metadata["size"] = self._get_file_size(bundle_file)
                        bundles.append(metadata)
            except:
                # Skip corrupted bundles
                continue

        return sorted(bundles, key=lambda x: x.get("created_at", 0), reverse=True)

    def install_bundle(self, bundle_path: str, target_dir: Optional[str] = None) -> bool:
        """
        Install bundle to target directory

        Args:
            bundle_path: Path to bundle file
            target_dir: Optional target directory (default: lms_dir)

        Returns:
            True if installation successful
        """
        bundle_path = Path(bundle_path)
        target_dir = Path(target_dir) if target_dir else self.lms_dir

        if not bundle_path.exists():
            print(f"❌ Bundle not found: {bundle_path}")
            return False

        try:
            # Extract bundle
            with tempfile.TemporaryDirectory(prefix="314sign-install-") as temp_dir:
                extract_dir = Path(temp_dir)
                with tarfile.open(bundle_path, "r:gz") as tar:
                    tar.extractall(extract_dir)

                # Verify checksums
                if not self._verify_checksums(extract_dir):
                    print("❌ Checksum verification failed")
                    return False

                # Install LMS file
                lms_file = extract_dir / "content.lms"
                if lms_file.exists():
                    # Load metadata to get original filename
                    metadata_file = extract_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        original_name = metadata.get("lms_filename", "content.lms")
                        target_lms = target_dir / original_name
                    else:
                        target_lms = target_dir / f"{bundle_path.stem}.lms"

                    shutil.copy2(lms_file, target_lms)

                # Install assets
                assets_dir = extract_dir / "assets"
                if assets_dir.exists():
                    for asset_file in assets_dir.glob("*"):
                        # Determine asset type and copy to appropriate location
                        if asset_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.avif']:
                            target_asset_dir = self.assets_dir / "images"
                        elif asset_file.suffix.lower() in ['.ttf', '.woff', '.woff2']:
                            target_asset_dir = self.assets_dir / "fonts"
                        else:
                            target_asset_dir = self.assets_dir / "misc"

                        target_asset_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(asset_file, target_asset_dir / asset_file.name)

            print(f"✅ Bundle installed successfully: {bundle_path.name}")
            return True

        except Exception as e:
            print(f"❌ Bundle installation failed: {e}")
            return False

    def _verify_checksums(self, bundle_dir: Path) -> bool:
        """Verify checksums of extracted bundle"""
        checksums_file = bundle_dir / "checksums.sha256"

        if not checksums_file.exists():
            return True  # No checksums to verify

        expected_checksums = {}
        with open(checksums_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    expected_checksums[parts[1]] = parts[0]

        # Verify each file
        for filename, expected_checksum in expected_checksums.items():
            file_path = bundle_dir / filename
            if not file_path.exists():
                file_path = bundle_dir / "assets" / filename  # Check in assets subdir

            if file_path.exists():
                actual_checksum = self._calculate_file_checksum(file_path)
                if actual_checksum != expected_checksum:
                    print(f"❌ Checksum mismatch for {filename}")
                    return False
            else:
                print(f"❌ File missing: {filename}")
                return False

        return True

    def distribute_bundle(self, bundle_path: str, remote_hosts: List[str],
                         ssh_key: Optional[str] = None) -> Dict[str, bool]:
        """
        Distribute bundle to remote hosts

        Args:
            bundle_path: Path to bundle file
            remote_hosts: List of remote host addresses
            ssh_key: Optional SSH key path

        Returns:
            Dict mapping host to success status
        """
        results = {}

        for host in remote_hosts:
            try:
                print(f"📤 Distributing to {host}...")

                # Create SSH command
                ssh_cmd = ["ssh"]
                if ssh_key:
                    ssh_cmd.extend(["-i", ssh_key])
                ssh_cmd.append(host)

                # Copy bundle using scp
                scp_cmd = ["scp"]
                if ssh_key:
                    scp_cmd.extend(["-i", ssh_key])
                scp_cmd.extend([bundle_path, f"{host}:/tmp/"])

                result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    # Install bundle on remote
                    install_cmd = ssh_cmd + [
                        "python3 /opt/314sign/bundle_manager.py --install",
                        f"/tmp/{Path(bundle_path).name}"
                    ]

                    install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=30)

                    if install_result.returncode == 0:
                        results[host] = True
                        print(f"✅ Successfully distributed to {host}")
                    else:
                        results[host] = False
                        print(f"❌ Installation failed on {host}: {install_result.stderr}")
                else:
                    results[host] = False
                    print(f"❌ Transfer failed to {host}: {result.stderr}")

            except subprocess.TimeoutExpired:
                results[host] = False
                print(f"❌ Timeout distributing to {host}")
            except Exception as e:
                results[host] = False
                print(f"❌ Error distributing to {host}: {e}")

        return results

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='314Sign LMS Bundle Manager')
    parser.add_argument('--create', '-c', help='Create bundle from LMS file')
    parser.add_argument('--install', '-i', help='Install bundle')
    parser.add_argument('--list', '-l', action='store_true', help='List available bundles')
    parser.add_argument('--distribute', '-d', nargs='+', help='Distribute bundle to remote hosts')
    parser.add_argument('--ssh-key', '-k', help='SSH key for remote access')
    parser.add_argument('--lms-dir', default='/home/pi/lms', help='LMS directory')
    parser.add_argument('--bundles-dir', default='/var/lib/314sign/bundles', help='Bundles directory')

    args = parser.parse_args()

    manager = LMSBundleManager(
        lms_dir=args.lms_dir,
        bundles_dir=args.bundles_dir
    )

    if args.create:
        try:
            bundle_path = manager.create_bundle(args.create)
            print(f"Bundle created: {bundle_path}")
        except Exception as e:
            print(f"Error creating bundle: {e}")
            exit(1)

    elif args.install:
        if manager.install_bundle(args.install):
            print("Bundle installed successfully")
        else:
            print("Bundle installation failed")
            exit(1)

    elif args.list:
        bundles = manager.list_bundles()
        if bundles:
            print("Available Bundles:")
            print("-" * 80)
            for bundle in bundles:
                print("15"                print(f"  Type: {bundle.get('content_type', 'unknown')}")
                print(f"  Priority: {bundle.get('priority', 'normal')}")
                print(f"  Size: {bundle.get('size', 'unknown')}")
                print(f"  Created: {time.ctime(bundle.get('created_at', 0))}")
                print("-" * 80)
        else:
            print("No bundles found")

    elif args.distribute:
        if len(args.distribute) < 2:
            print("Usage: --distribute <bundle_path> <host1> [host2] ...")
            exit(1)

        bundle_path = args.distribute[0]
        remote_hosts = args.distribute[1:]

        results = manager.distribute_bundle(bundle_path, remote_hosts, args.ssh_key)

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        print(f"\nDistribution complete: {success_count}/{total_count} successful")

        if success_count < total_count:
            print("Failed hosts:")
            for host, success in results.items():
                if not success:
                    print(f"  - {host}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()