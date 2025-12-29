#!/usr/bin/env python3
"""
314Sign Security Key System
Comprehensive cryptographic security for the hybrid digital signage platform
"""

import os
import json
import hashlib
import hmac
import secrets
import base64
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import logging

class SecurityKeyManager:
    """
    Comprehensive security key management for 314Sign hybrid system
    """

    def __init__(self, keys_dir: str = "/var/lib/314sign/keys",
                 master_key_file: str = "/var/lib/314sign/keys/master.key"):
        self.keys_dir = Path(keys_dir)
        self.master_key_file = Path(master_key_file)
        self.keys_dir.mkdir(parents=True, exist_ok=True)

        # Initialize master key if it doesn't exist
        self.master_key = self._load_or_create_master_key()

        # Load or create system keys
        self.system_keys = self._load_system_keys()

    def _load_or_create_master_key(self) -> bytes:
        """Load existing master key or create new one"""
        if self.master_key_file.exists():
            try:
                with open(self.master_key_file, 'rb') as f:
                    encrypted_key = f.read()
                # Master key is self-encrypted with a password
                return self._decrypt_master_key(encrypted_key)
            except Exception as e:
                logging.error(f"Failed to load master key: {e}")
                # Create new master key
                return self._create_master_key()
        else:
            return self._create_master_key()

    def _create_master_key(self) -> bytes:
        """Create and save new master key"""
        # Generate cryptographically secure master key
        master_key = secrets.token_bytes(32)

        # Save encrypted master key
        encrypted_key = self._encrypt_master_key(master_key)
        with open(self.master_key_file, 'wb') as f:
            f.write(encrypted_key)

        # Set proper permissions
        os.chmod(self.master_key_file, 0o600)

        return master_key

    def _encrypt_master_key(self, master_key: bytes) -> bytes:
        """Encrypt master key with system password"""
        # Use system hostname as password for master key encryption
        import socket
        password = socket.gethostname().encode()

        # Derive encryption key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'314sign_master_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))

        # Encrypt master key
        f = Fernet(key)
        return f.encrypt(master_key)

    def _decrypt_master_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt master key with system password"""
        import socket
        password = socket.gethostname().encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'314sign_master_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))

        f = Fernet(key)
        return f.decrypt(encrypted_key)

    def _load_system_keys(self) -> Dict[str, Any]:
        """Load or create system cryptographic keys"""
        keys_file = self.keys_dir / "system_keys.json"

        if keys_file.exists():
            try:
                with open(keys_file, 'r') as f:
                    encrypted_data = f.read()
                decrypted_data = self._decrypt_with_master_key(encrypted_data.encode())
                return json.loads(decrypted_data.decode())
            except Exception as e:
                logging.error(f"Failed to load system keys: {e}")

        # Create new system keys
        return self._create_system_keys()

    def _create_system_keys(self) -> Dict[str, Any]:
        """Create comprehensive system key set"""
        # Generate RSA key pair for signing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Generate symmetric keys
        api_key = secrets.token_urlsafe(32)
        bundle_key = secrets.token_bytes(32)
        device_key = secrets.token_bytes(32)

        system_keys = {
            "created_at": time.time(),
            "version": "1.0",
            "rsa_private_key": private_pem.decode(),
            "rsa_public_key": public_pem.decode(),
            "api_key": api_key,
            "bundle_key": base64.b64encode(bundle_key).decode(),
            "device_key": base64.b64encode(device_key).decode(),
            "key_id": secrets.token_hex(8)
        }

        # Save encrypted system keys
        self._save_system_keys(system_keys)

        return system_keys

    def _save_system_keys(self, keys: Dict[str, Any]):
        """Save system keys encrypted"""
        keys_file = self.keys_dir / "system_keys.json"
        keys_json = json.dumps(keys, indent=2)
        encrypted_data = self._encrypt_with_master_key(keys_json.encode())

        with open(keys_file, 'wb') as f:
            f.write(encrypted_data)

        os.chmod(keys_file, 0o600)

    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Encrypt data with master key"""
        key = base64.urlsafe_b64encode(self.master_key)
        f = Fernet(key)
        return f.encrypt(data)

    def _decrypt_with_master_key(self, data: bytes) -> bytes:
        """Decrypt data with master key"""
        key = base64.urlsafe_b64encode(self.master_key)
        f = Fernet(key)
        return f.decrypt(data)

    # Device Authentication
    def generate_device_token(self, device_id: str, device_info: Dict = None) -> str:
        """Generate authentication token for device"""
        if device_info is None:
            device_info = {}

        payload = {
            "device_id": device_id,
            "issued_at": time.time(),
            "expires_at": time.time() + (365 * 24 * 3600),  # 1 year
            "device_info": device_info
        }

        # Sign payload
        payload_json = json.dumps(payload, sort_keys=True)
        signature = self._sign_data(payload_json.encode())

        token_data = {
            "payload": payload,
            "signature": signature
        }

        token_json = json.dumps(token_data, sort_keys=True)
        return base64.urlsafe_b64encode(token_json.encode()).decode()

    def verify_device_token(self, token: str) -> Optional[Dict]:
        """Verify device authentication token"""
        try:
            token_data = json.loads(base64.urlsafe_b64decode(token.encode()))
            payload = token_data["payload"]
            signature = token_data["signature"]

            # Verify signature
            payload_json = json.dumps(payload, sort_keys=True)
            if not self._verify_signature(payload_json.encode(), signature):
                return None

            # Check expiration
            if time.time() > payload["expires_at"]:
                return None

            return payload

        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return None

    # Content Signing
    def sign_bundle(self, bundle_path: str) -> str:
        """Sign a content bundle for integrity verification"""
        bundle_path = Path(bundle_path)

        if not bundle_path.exists():
            raise FileNotFoundError(f"Bundle not found: {bundle_path}")

        # Calculate bundle hash
        bundle_hash = self._calculate_file_hash(bundle_path)

        # Create signature payload
        signature_payload = {
            "bundle_name": bundle_path.name,
            "bundle_hash": bundle_hash,
            "signed_at": time.time(),
            "signed_by": self.system_keys["key_id"]
        }

        # Sign payload
        payload_json = json.dumps(signature_payload, sort_keys=True)
        signature = self._sign_data(payload_json.encode())

        signature_data = {
            "payload": signature_payload,
            "signature": signature,
            "public_key": self.system_keys["rsa_public_key"]
        }

        return json.dumps(signature_data, indent=2)

    def verify_bundle_signature(self, bundle_path: str, signature_file: str) -> bool:
        """Verify bundle signature"""
        try:
            bundle_path = Path(bundle_path)
            signature_path = Path(signature_file)

            if not bundle_path.exists() or not signature_path.exists():
                return False

            # Load signature
            with open(signature_path, 'r') as f:
                signature_data = json.load(f)

            payload = signature_data["payload"]
            signature = signature_data["signature"]

            # Verify bundle hash
            current_hash = self._calculate_file_hash(bundle_path)
            if current_hash != payload["bundle_hash"]:
                logging.error("Bundle hash mismatch")
                return False

            # Verify signature
            payload_json = json.dumps(payload, sort_keys=True)
            return self._verify_signature(payload_json.encode(), signature)

        except Exception as e:
            logging.error(f"Bundle signature verification failed: {e}")
            return False

    # API Authentication
    def generate_api_token(self, client_id: str, permissions: List[str] = None) -> str:
        """Generate API authentication token"""
        if permissions is None:
            permissions = ["read"]

        payload = {
            "client_id": client_id,
            "permissions": permissions,
            "issued_at": time.time(),
            "expires_at": time.time() + (24 * 3600),  # 24 hours
            "token_type": "api"
        }

        # Create token with HMAC
        payload_json = json.dumps(payload, sort_keys=True)
        signature = self._create_hmac_signature(payload_json.encode())

        token_data = {
            "payload": payload,
            "signature": signature
        }

        token_json = json.dumps(token_data, sort_keys=True)
        return base64.urlsafe_b64encode(token_json.encode()).decode()

    def verify_api_token(self, token: str) -> Optional[Dict]:
        """Verify API authentication token"""
        try:
            token_data = json.loads(base64.urlsafe_b64decode(token.encode()))
            payload = token_data["payload"]
            signature = token_data["signature"]

            # Verify signature
            payload_json = json.dumps(payload, sort_keys=True)
            expected_signature = self._create_hmac_signature(payload_json.encode())

            if not hmac.compare_digest(signature, expected_signature):
                return None

            # Check expiration
            if time.time() > payload["expires_at"]:
                return None

            return payload

        except Exception as e:
            logging.error(f"API token verification failed: {e}")
            return None

    # Administrative Access
    def generate_admin_key(self, admin_id: str, role: str = "operator") -> str:
        """Generate administrative access key"""
        payload = {
            "admin_id": admin_id,
            "role": role,
            "issued_at": time.time(),
            "expires_at": time.time() + (8 * 3600),  # 8 hours
            "key_type": "admin"
        }

        # Encrypt payload
        payload_json = json.dumps(payload, sort_keys=True)
        encrypted_payload = self._encrypt_with_master_key(payload_json.encode())

        return base64.urlsafe_b64encode(encrypted_payload).decode()

    def verify_admin_key(self, admin_key: str) -> Optional[Dict]:
        """Verify administrative access key"""
        try:
            encrypted_payload = base64.urlsafe_b64decode(admin_key.encode())
            decrypted_payload = self._decrypt_with_master_key(encrypted_payload)
            payload = json.loads(decrypted_payload.decode())

            # Check expiration
            if time.time() > payload["expires_at"]:
                return None

            return payload

        except Exception as e:
            logging.error(f"Admin key verification failed: {e}")
            return None

    # Cryptographic Utilities
    def _sign_data(self, data: bytes) -> str:
        """Sign data with RSA private key"""
        from cryptography.hazmat.primitives import serialization

        private_key_pem = self.system_keys["rsa_private_key"]
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )

        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode()

    def _verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify RSA signature"""
        from cryptography.hazmat.primitives import serialization

        try:
            public_key_pem = self.system_keys["rsa_public_key"]
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )

            signature_bytes = base64.b64decode(signature)

            public_key.verify(
                signature_bytes,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            return True

        except Exception as e:
            logging.error(f"Signature verification failed: {e}")
            return False

    def _create_hmac_signature(self, data: bytes) -> str:
        """Create HMAC signature"""
        api_key = self.system_keys["api_key"]
        signature = hmac.new(
            api_key.encode(),
            data,
            hashlib.sha256
        )
        return signature.hexdigest()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    # Key Management
    def rotate_keys(self) -> bool:
        """Rotate system cryptographic keys"""
        try:
            logging.info("Starting key rotation...")

            # Create new keys
            new_keys = self._create_system_keys()

            # Update system keys
            self.system_keys = new_keys

            # Create rotation record
            rotation_record = {
                "rotated_at": time.time(),
                "old_key_id": self.system_keys.get("key_id", "unknown"),
                "new_key_id": new_keys["key_id"],
                "rotation_type": "full"
            }

            rotation_file = self.keys_dir / f"rotation_{int(time.time())}.json"
            with open(rotation_file, 'w') as f:
                json.dump(rotation_record, f, indent=2)

            logging.info("Key rotation completed successfully")
            return True

        except Exception as e:
            logging.error(f"Key rotation failed: {e}")
            return False

    def get_key_status(self) -> Dict[str, Any]:
        """Get current key system status"""
        return {
            "master_key_exists": self.master_key_file.exists(),
            "system_keys_loaded": bool(self.system_keys),
            "key_id": self.system_keys.get("key_id", "unknown"),
            "created_at": self.system_keys.get("created_at", 0),
            "keys_dir_secure": oct(os.stat(self.keys_dir).st_mode)[-3:] == "700" if self.keys_dir.exists() else False
        }

    def export_public_key(self) -> str:
        """Export public key for sharing with other systems"""
        return self.system_keys["rsa_public_key"]

def main():
    """CLI interface for security key management"""
    import argparse

    parser = argparse.ArgumentParser(description='314Sign Security Key Manager')
    parser.add_argument('--status', action='store_true', help='Show key system status')
    parser.add_argument('--rotate-keys', action='store_true', help='Rotate system keys')
    parser.add_argument('--generate-device-token', metavar='DEVICE_ID', help='Generate device token')
    parser.add_argument('--verify-device-token', metavar='TOKEN', help='Verify device token')
    parser.add_argument('--generate-api-token', metavar='CLIENT_ID', help='Generate API token')
    parser.add_argument('--verify-api-token', metavar='TOKEN', help='Verify API token')
    parser.add_argument('--generate-admin-key', metavar='ADMIN_ID', help='Generate admin key')
    parser.add_argument('--verify-admin-key', metavar='KEY', help='Verify admin key')
    parser.add_argument('--sign-bundle', metavar='BUNDLE_PATH', help='Sign content bundle')
    parser.add_argument('--verify-bundle', nargs=2, metavar=('BUNDLE_PATH', 'SIG_FILE'), help='Verify bundle signature')
    parser.add_argument('--export-public-key', action='store_true', help='Export public key')

    args = parser.parse_args()

    # Initialize key manager
    key_manager = SecurityKeyManager()

    if args.status:
        status = key_manager.get_key_status()
        print("314Sign Security Key System Status:")
        print(f"  Master Key: {'✓' if status['master_key_exists'] else '✗'}")
        print(f"  System Keys: {'✓' if status['system_keys_loaded'] else '✗'}")
        print(f"  Key ID: {status['key_id']}")
        print(f"  Created: {time.ctime(status['created_at'])}")
        print(f"  Keys Directory Secure: {'✓' if status['keys_dir_secure'] else '✗'}")

    elif args.rotate_keys:
        if key_manager.rotate_keys():
            print("✅ Key rotation completed successfully")
        else:
            print("❌ Key rotation failed")
            exit(1)

    elif args.generate_device_token:
        token = key_manager.generate_device_token(args.generate_device_token)
        print(f"Device Token: {token}")

    elif args.verify_device_token:
        payload = key_manager.verify_device_token(args.verify_device_token)
        if payload:
            print("✅ Token is valid:")
            print(f"  Device ID: {payload['device_id']}")
            print(f"  Issued: {time.ctime(payload['issued_at'])}")
            print(f"  Expires: {time.ctime(payload['expires_at'])}")
        else:
            print("❌ Token is invalid or expired")

    elif args.generate_api_token:
        token = key_manager.generate_api_token(args.generate_api_token)
        print(f"API Token: {token}")

    elif args.verify_api_token:
        payload = key_manager.verify_api_token(args.verify_api_token)
        if payload:
            print("✅ API token is valid:")
            print(f"  Client ID: {payload['client_id']}")
            print(f"  Permissions: {payload['permissions']}")
            print(f"  Expires: {time.ctime(payload['expires_at'])}")
        else:
            print("❌ API token is invalid or expired")

    elif args.generate_admin_key:
        key = key_manager.generate_admin_key(args.generate_admin_key)
        print(f"Admin Key: {key}")

    elif args.verify_admin_key:
        payload = key_manager.verify_admin_key(args.verify_admin_key)
        if payload:
            print("✅ Admin key is valid:")
            print(f"  Admin ID: {payload['admin_id']}")
            print(f"  Role: {payload['role']}")
            print(f"  Expires: {time.ctime(payload['expires_at'])}")
        else:
            print("❌ Admin key is invalid or expired")

    elif args.sign_bundle:
        try:
            signature = key_manager.sign_bundle(args.sign_bundle)
            sig_file = f"{args.sign_bundle}.sig"
            with open(sig_file, 'w') as f:
                f.write(signature)
            print(f"✅ Bundle signed: {sig_file}")
        except Exception as e:
            print(f"❌ Bundle signing failed: {e}")
            exit(1)

    elif args.verify_bundle:
        bundle_path, sig_file = args.verify_bundle
        if key_manager.verify_bundle_signature(bundle_path, sig_file):
            print("✅ Bundle signature is valid")
        else:
            print("❌ Bundle signature verification failed")
            exit(1)

    elif args.export_public_key:
        public_key = key_manager.export_public_key()
        print("RSA Public Key:")
        print(public_key)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()