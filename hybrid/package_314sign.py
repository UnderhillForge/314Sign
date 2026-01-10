#!/usr/bin/env python3
"""
314Sign Package System (.314 files)
Creates and manages self-contained content packages for easy distribution
Bundles LMS data with all required assets into single distributable files
"""

import json
import base64
import hashlib
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import mimetypes
import logging
from dataclasses import dataclass, asdict

@dataclass
class PackageAsset:
    """Represents an asset within a .314 package"""
    filename: str
    data: str  # base64 encoded
    mime_type: str
    original_size: int
    compressed_size: int
    sha256_hash: str

@dataclass
class PackageManifest:
    """Package manifest with metadata"""
    format_version: str = "1.0"
    created_timestamp: float = None
    author: str = "314Sign System"
    description: str = ""
    tags: List[str] = None
    total_size: int = 0
    asset_count: int = 0
    lms_version: str = "1.0"
    checksum: str = ""

    def __post_init__(self):
        if self.created_timestamp is None:
            self.created_timestamp = time.time()
        if self.tags is None:
            self.tags = []

class PackageError(Exception):
    """Custom exception for package operations"""
    pass

class SignPackage:
    """
    314Sign Package (.314) creator and parser
    Handles bundling LMS content with assets into self-contained packages
    """

    def __init__(self):
        self.logger = logging.getLogger('314sign_package')
        self.supported_formats = ['1.0']

    def create_package(self, lms_path: Path, output_path: Optional[Path] = None,
                      author: str = "314Sign System", description: str = "",
                      tags: List[str] = None) -> Path:
        """
        Create a .314 package from LMS file and referenced assets

        Args:
            lms_path: Path to .lms file
            output_path: Output path for .314 file (auto-generated if None)
            author: Package author
            description: Package description
            tags: List of tags for categorization

        Returns:
            Path to created .314 file
        """
        if not lms_path.exists():
            raise PackageError(f"LMS file not found: {lms_path}")

        # Generate output path if not provided
        if output_path is None:
            stem = lms_path.stem
            output_path = lms_path.parent / f"{stem}.314"

        self.logger.info(f"Creating package: {lms_path} -> {output_path}")

        # Parse LMS file
        lms_data = self._parse_lms_file(lms_path)

        # Find and collect all referenced assets
        assets = self._collect_assets(lms_path, lms_data)

        # Create package manifest
        manifest = PackageManifest(
            author=author,
            description=description,
            tags=tags or [],
            asset_count=len(assets),
            lms_version=lms_data.get('version', '1.0')
        )

        # Calculate total size
        lms_size = len(json.dumps(lms_data, indent=2).encode('utf-8'))
        assets_size = sum(asset.compressed_size for asset in assets)
        manifest.total_size = lms_size + assets_size

        # Create package structure
        package_data = {
            'format': f'314Sign Package v{manifest.format_version}',
            'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(manifest.created_timestamp)),
            'manifest': asdict(manifest),
            'lms_data': lms_data,
            'assets': {asset.filename: {
                'data': asset.data,
                'mime_type': asset.mime_type,
                'original_size': asset.original_size,
                'compressed_size': asset.compressed_size,
                'sha256_hash': asset.sha256_hash
            } for asset in assets}
        }

        # Generate package checksum
        package_json = json.dumps(package_data, sort_keys=True, separators=(',', ':'))
        manifest.checksum = hashlib.sha256(package_json.encode('utf-8')).hexdigest()
        package_data['manifest']['checksum'] = manifest.checksum

        # Write package file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(package_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Package created: {output_path}")
        self.logger.info(f"Total size: {manifest.total_size:,} bytes")
        self.logger.info(f"Assets: {len(assets)}")

        return output_path

    def load_package(self, package_path: Path) -> Dict[str, Any]:
        """
        Load and validate a .314 package

        Args:
            package_path: Path to .314 package file

        Returns:
            Dict containing package data with extracted LMS and assets
        """
        if not package_path.exists():
            raise PackageError(f"Package file not found: {package_path}")

        self.logger.info(f"Loading package: {package_path}")

        try:
            with open(package_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
        except json.JSONDecodeError as e:
            raise PackageError(f"Invalid JSON in package: {e}")

        # Validate package format
        self._validate_package(package_data)

        # Extract and return processed data
        result = {
            'manifest': package_data['manifest'],
            'lms_data': package_data['lms_data'],
            'assets': {},
            'metadata': {
                'package_file': str(package_path),
                'loaded_at': time.time(),
                'format_version': package_data['manifest']['format_version']
            }
        }

        # Process assets (decode from base64)
        for filename, asset_data in package_data.get('assets', {}).items():
            try:
                # Decode base64 data
                asset_bytes = base64.b64decode(asset_data['data'])

                result['assets'][filename] = {
                    'data': asset_bytes,
                    'mime_type': asset_data['mime_type'],
                    'original_size': asset_data['original_size'],
                    'compressed_size': asset_data['compressed_size'],
                    'sha256_hash': asset_data['sha256_hash']
                }

                # Verify hash
                actual_hash = hashlib.sha256(asset_bytes).hexdigest()
                if actual_hash != asset_data['sha256_hash']:
                    self.logger.warning(f"Hash mismatch for asset {filename}")

            except Exception as e:
                self.logger.error(f"Failed to process asset {filename}: {e}")

        self.logger.info(f"Package loaded: {len(result['assets'])} assets")
        return result

    def extract_package(self, package_path: Path, output_dir: Path,
                       extract_assets: bool = True) -> Path:
        """
        Extract .314 package contents to directory

        Args:
            package_path: Path to .314 package
            output_dir: Directory to extract to
            extract_assets: Whether to extract asset files

        Returns:
            Path to extracted LMS file
        """
        package_data = self.load_package(package_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract LMS data
        lms_filename = f"{Path(package_path).stem}.lms"
        lms_path = output_dir / lms_filename

        with open(lms_path, 'w', encoding='utf-8') as f:
            json.dump(package_data['lms_data'], f, indent=2, ensure_ascii=False)

        # Extract assets if requested
        if extract_assets:
            assets_dir = output_dir / "assets"
            assets_dir.mkdir(exist_ok=True)

            for filename, asset_data in package_data['assets'].items():
                asset_path = assets_dir / filename
                asset_path.parent.mkdir(parents=True, exist_ok=True)

                with open(asset_path, 'wb') as f:
                    f.write(asset_data['data'])

        # Create manifest file
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(package_data['manifest'], f, indent=2)

        self.logger.info(f"Package extracted to: {output_dir}")
        return lms_path

    def validate_package(self, package_path: Path) -> Dict[str, Any]:
        """
        Validate .314 package integrity

        Args:
            package_path: Path to package file

        Returns:
            Validation results
        """
        try:
            package_data = self.load_package(package_path)
            manifest = package_data['manifest']

            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'manifest': manifest
            }

            # Validate format version
            if manifest['format_version'] not in self.supported_formats:
                results['errors'].append(f"Unsupported format version: {manifest['format_version']}")

            # Validate checksum
            package_json = json.dumps(package_data, sort_keys=True, separators=(',', ':'))
            # Remove the checksum from manifest for calculation
            manifest_no_checksum = dict(manifest)
            manifest_no_checksum.pop('checksum', None)
            package_data_no_checksum = dict(package_data)
            package_data_no_checksum['manifest'] = manifest_no_checksum

            calculated_checksum = hashlib.sha256(
                json.dumps(package_data_no_checksum, sort_keys=True, separators=(',', ':')).encode('utf-8')
            ).hexdigest()

            if calculated_checksum != manifest['checksum']:
                results['errors'].append("Package checksum mismatch")

            # Validate LMS data
            lms_data = package_data['lms_data']
            if not isinstance(lms_data, dict):
                results['errors'].append("Invalid LMS data structure")

            if 'version' not in lms_data:
                results['errors'].append("Missing LMS version")

            # Validate assets
            for filename, asset_data in package_data['assets'].items():
                if 'data' not in asset_data:
                    results['errors'].append(f"Missing data for asset: {filename}")

                if 'sha256_hash' not in asset_data:
                    results['errors'].append(f"Missing hash for asset: {filename}")

            # Check asset count matches manifest
            if len(package_data['assets']) != manifest['asset_count']:
                results['warnings'].append("Asset count mismatch with manifest")

            results['valid'] = len(results['errors']) == 0

            return results

        except Exception as e:
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            }

    def _parse_lms_file(self, lms_path: Path) -> Dict[str, Any]:
        """Parse LMS file for package creation"""
        try:
            from lms.parser import LMSParser
            parser = LMSParser()
            return parser.parse_file(lms_path)
        except ImportError:
            # Fallback if LMS parser not available
            with open(lms_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _collect_assets(self, lms_path: Path, lms_data: Dict[str, Any]) -> List[PackageAsset]:
        """Collect all assets referenced in LMS data"""
        assets = []
        lms_dir = lms_path.parent

        # Collect background image
        if 'background' in lms_data and 'image' in lms_data['background']:
            bg_image = lms_data['background']['image']
            if not bg_image.startswith('http'):  # Skip remote URLs
                asset_path = lms_dir / bg_image
                if asset_path.exists():
                    asset = self._create_asset(asset_path)
                    if asset:
                        assets.append(asset)

        # Collect overlay images
        for overlay in lms_data.get('overlays', []):
            if overlay.get('type') == 'image' and 'src' in overlay:
                img_src = overlay['src']
                if not img_src.startswith('http'):  # Skip remote URLs
                    asset_path = lms_dir / img_src
                    if asset_path.exists():
                        asset = self._create_asset(asset_path)
                        if asset:
                            assets.append(asset)

        return assets

    def _create_asset(self, asset_path: Path) -> Optional[PackageAsset]:
        """Create PackageAsset from file"""
        try:
            # Read file data
            with open(asset_path, 'rb') as f:
                file_data = f.read()

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(asset_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Calculate hashes
            sha256_hash = hashlib.sha256(file_data).hexdigest()

            # Base64 encode (consider compression for large files)
            encoded_data = base64.b64encode(file_data).decode('ascii')

            return PackageAsset(
                filename=asset_path.name,
                data=encoded_data,
                mime_type=mime_type,
                original_size=len(file_data),
                compressed_size=len(encoded_data),  # Base64 is ~33% larger
                sha256_hash=sha256_hash
            )

        except Exception as e:
            self.logger.error(f"Failed to create asset from {asset_path}: {e}")
            return None

    def _validate_package(self, package_data: Dict[str, Any]) -> None:
        """Validate package data structure"""
        required_fields = ['format', 'manifest', 'lms_data']
        for field in required_fields:
            if field not in package_data:
                raise PackageError(f"Missing required field: {field}")

        # Validate format
        if not package_data['format'].startswith('314Sign Package v'):
            raise PackageError("Invalid package format")

        # Validate manifest
        manifest = package_data['manifest']
        if 'format_version' not in manifest:
            raise PackageError("Missing format version in manifest")

        if manifest['format_version'] not in self.supported_formats:
            raise PackageError(f"Unsupported format version: {manifest['format_version']}")


def create_command(args):
    """Command: create package"""
    package_tool = SignPackage()

    lms_path = Path(args.lms_file)
    output_path = Path(args.output) if args.output else None

    try:
        package_file = package_tool.create_package(
            lms_path=lms_path,
            output_path=output_path,
            author=args.author,
            description=args.description,
            tags=args.tags
        )
        print(f"✅ Package created: {package_file}")
        print(f"   Size: {package_file.stat().st_size:,} bytes")

    except PackageError as e:
        print(f"❌ Package creation failed: {e}")
        return 1

    return 0

def extract_command(args):
    """Command: extract package"""
    package_tool = SignPackage()

    package_path = Path(args.package)
    output_dir = Path(args.output_dir)

    try:
        lms_file = package_tool.extract_package(
            package_path=package_path,
            output_dir=output_dir,
            extract_assets=not args.no_assets
        )
        print(f"✅ Package extracted to: {output_dir}")
        print(f"   LMS file: {lms_file}")

    except PackageError as e:
        print(f"❌ Package extraction failed: {e}")
        return 1

    return 0

def validate_command(args):
    """Command: validate package"""
    package_tool = SignPackage()

    package_path = Path(args.package)

    try:
        results = package_tool.validate_package(package_path)

        if results['valid']:
            print(f"✅ Package is valid: {package_path}")
            print(f"   Format: 314Sign Package v{results['manifest']['format_version']}")
            print(f"   Assets: {results['manifest']['asset_count']}")
            print(f"   Size: {results['manifest']['total_size']:,} bytes")
        else:
            print(f"❌ Package validation failed: {package_path}")
            for error in results['errors']:
                print(f"   Error: {error}")

        if results['warnings']:
            print("⚠️  Warnings:")
            for warning in results['warnings']:
                print(f"   Warning: {warning}")

    except PackageError as e:
        print(f"❌ Validation failed: {e}")
        return 1

    return 0

def info_command(args):
    """Command: show package info"""
    package_tool = SignPackage()

    package_path = Path(args.package)

    try:
        package_data = package_tool.load_package(package_path)
        manifest = package_data['manifest']

        print(f"314Sign Package Information")
        print(f"===========================")
        print(f"File: {package_path}")
        print(f"Format: 314Sign Package v{manifest['format_version']}")
        print(f"Created: {manifest['created_timestamp']}")
        print(f"Author: {manifest['author']}")
        print(f"Description: {manifest['description']}")
        print(f"LMS Version: {manifest['lms_version']}")
        print(f"Total Size: {manifest['total_size']:,} bytes")
        print(f"Assets: {manifest['asset_count']}")
        print(f"Tags: {', '.join(manifest['tags'])}")
        print(f"Checksum: {manifest['checksum'][:16]}...")

        print(f"\nLMS Content:")
        lms_data = package_data['lms_data']
        print(f"  Version: {lms_data.get('version')}")
        print(f"  Background: {lms_data.get('background', {}).get('image', 'None')}")
        print(f"  Overlays: {len(lms_data.get('overlays', []))}")
        print(f"  Animations: {len(lms_data.get('animations', []))}")

        if package_data['assets']:
            print(f"\nEmbedded Assets:")
            for filename, asset_info in package_data['assets'].items():
                print(f"  {filename}: {asset_info['original_size']:,} bytes ({asset_info['mime_type']})")

    except PackageError as e:
        print(f"❌ Failed to read package: {e}")
        return 1

    return 0

def main():
    """CLI interface for 314Sign package tools"""
    parser = argparse.ArgumentParser(
        description='314Sign Package Manager (.314 files)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create package from LMS file
  %(prog)s create restaurant-menu.lms -o restaurant-menu.314

  # Extract package contents
  %(prog)s extract restaurant-menu.314 -d ./extracted/

  # Validate package integrity
  %(prog)s validate restaurant-menu.314

  # Show package information
  %(prog)s info restaurant-menu.314
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create .314 package from LMS file')
    create_parser.add_argument('lms_file', help='Path to .lms file')
    create_parser.add_argument('-o', '--output', help='Output package file path')
    create_parser.add_argument('--author', default='314Sign System', help='Package author')
    create_parser.add_argument('--description', default='', help='Package description')
    create_parser.add_argument('--tags', nargs='*', default=[], help='Package tags')
    create_parser.set_defaults(func=create_command)

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract .314 package contents')
    extract_parser.add_argument('package', help='Path to .314 package file')
    extract_parser.add_argument('-d', '--output-dir', required=True, help='Output directory')
    extract_parser.add_argument('--no-assets', action='store_true', help='Skip extracting asset files')
    extract_parser.set_defaults(func=extract_command)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate .314 package integrity')
    validate_parser.add_argument('package', help='Path to .314 package file')
    validate_parser.set_defaults(func=validate_command)

    # Info command
    info_parser = subparsers.add_parser('info', help='Show .314 package information')
    info_parser.add_argument('package', help='Path to .314 package file')
    info_parser.set_defaults(func=info_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)

if __name__ == "__main__":
    exit(main())