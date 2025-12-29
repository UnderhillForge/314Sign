#!/usr/bin/env python3
"""
314Sign Backup Wallet
Standalone blockchain wallet for backup and recovery operations
Can run on separate hardware from the main kiosk system
"""

import json
import time
import hashlib
import secrets
import base64
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

class BackupWallet:
    """
    Standalone wallet for 314Sign blockchain backup and recovery
    Designed to run on separate hardware from main kiosk
    """

    def __init__(self, wallet_dir: str = "./314sign-wallet"):
        self.wallet_dir = Path(wallet_dir)
        self.wallet_dir.mkdir(parents=True, exist_ok=True)

        # Wallet files
        self.wallet_file = self.wallet_dir / "wallet.json"
        self.keys_file = self.wallet_dir / "keys.json"
        self.backups_dir = self.wallet_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)

        # Load or create wallet
        self.wallet_data = self._load_wallet()
        self.keys_data = self._load_keys()

        # Setup logging
        logging.basicConfig(
            filename=self.wallet_dir / "wallet.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _load_wallet(self) -> Dict[str, Any]:
        """Load wallet data"""
        if self.wallet_file.exists():
            try:
                with open(self.wallet_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load wallet: {e}")
                return self._create_wallet()
        else:
            return self._create_wallet()

    def _create_wallet(self) -> Dict[str, Any]:
        """Create new wallet"""
        wallet = {
            "wallet_id": secrets.token_hex(16),
            "created_at": time.time(),
            "version": "1.0.2.73",
            "tokens": [],
            "backup_chains": [],
            "recovery_codes": [],
            "metadata": {
                "description": "314Sign Backup Wallet",
                "hardware": "backup-system"
            }
        }
        self._save_wallet(wallet)
        logging.info(f"Created new backup wallet: {wallet['wallet_id']}")
        return wallet

    def _save_wallet(self, wallet_data: Dict[str, Any]):
        """Save wallet data"""
        with open(self.wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=2)

    def _load_keys(self) -> Dict[str, Any]:
        """Load cryptographic keys"""
        if self.keys_file.exists():
            try:
                with open(self.keys_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load keys: {e}")
                return self._create_keys()
        else:
            return self._create_keys()

    def _create_keys(self) -> Dict[str, Any]:
        """Create cryptographic keys for wallet"""
        # Generate RSA key pair for wallet operations
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

        keys_data = {
            "created_at": time.time(),
            "private_key": private_pem.decode(),
            "public_key": public_pem.decode(),
            "key_id": secrets.token_hex(8)
        }

        self._save_keys(keys_data)
        return keys_data

    def _save_keys(self, keys_data: Dict[str, Any]):
        """Save cryptographic keys"""
        with open(self.keys_file, 'w') as f:
            json.dump(keys_data, f, indent=2)

    def import_wallet_backup(self, backup_file: str) -> bool:
        """Import wallet backup from main kiosk"""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            logging.error(f"Backup file not found: {backup_file}")
            print(f"❌ Backup file not found: {backup_file}")
            return False

        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            # Validate backup data
            if not self._validate_backup(backup_data):
                print("❌ Backup validation failed")
                return False

            # Import tokens
            imported_tokens = 0
            existing_token_ids = {t["token_id"] for t in self.wallet_data["tokens"]}

            for token in backup_data.get("tokens", []):
                if token["token_id"] not in existing_token_ids:
                    # Verify token before importing
                    if self._verify_token_signature(token):
                        self.wallet_data["tokens"].append(token)
                        imported_tokens += 1
                    else:
                        logging.warning(f"Token {token['token_id']} failed verification")

            # Import backup chains
            imported_chains = 0
            for chain_backup in backup_data.get("backup_chains", []):
                if self._validate_chain_backup(chain_backup):
                    self.wallet_data["backup_chains"].append(chain_backup)
                    imported_chains += 1

            self._save_wallet(self.wallet_data)

            print("✅ Wallet backup imported successfully")
            print(f"   Tokens imported: {imported_tokens}")
            print(f"   Chain backups: {imported_chains}")
            print(f"   From wallet: {backup_data.get('wallet_id', 'unknown')}")

            logging.info(f"Imported wallet backup: {imported_tokens} tokens, {imported_chains} chains")
            return True

        except Exception as e:
            logging.error(f"Wallet import failed: {e}")
            print(f"❌ Import failed: {e}")
            return False

    def _validate_backup(self, backup_data: Dict[str, Any]) -> bool:
        """Validate backup data integrity"""
        required_fields = ["wallet_id", "export_timestamp", "tokens"]
        for field in required_fields:
            if field not in backup_data:
                logging.error(f"Backup missing required field: {field}")
                return False

        # Check export timestamp is reasonable (not in future, not too old)
        export_time = backup_data.get("export_timestamp", 0)
        current_time = time.time()

        if export_time > current_time + 3600:  # 1 hour in future
            logging.error("Backup timestamp is in the future")
            return False

        if export_time < current_time - (365 * 24 * 3600):  # 1 year old
            logging.warning("Backup is over 1 year old")

        return True

    def _verify_token_signature(self, token_data: Dict[str, Any]) -> bool:
        """Verify token cryptographic signature"""
        try:
            # Get public key from backup metadata or use our key
            public_key_pem = token_data.get("public_key") or self.keys_data["public_key"]

            # Create token object for verification
            from blockchain_security import SignToken
            token = SignToken.from_dict(token_data)

            return token.verify_token(public_key_pem)

        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return False

    def _validate_chain_backup(self, chain_backup: Dict[str, Any]) -> bool:
        """Validate blockchain backup data"""
        required_fields = ["timestamp", "chain_length", "chain_data"]
        for field in required_fields:
            if field not in chain_backup:
                return False

        # Basic validation of chain data
        chain_data = chain_backup.get("chain_data", [])
        if not isinstance(chain_data, list) or len(chain_data) == 0:
            return False

        # Validate each block has required fields
        for block in chain_data:
            if not all(key in block for key in ["index", "hash", "previous_hash"]):
                return False

        return True

    def list_tokens(self) -> List[Dict[str, Any]]:
        """List all tokens in wallet"""
        return self.wallet_data["tokens"]

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all blockchain backups"""
        return self.wallet_data["backup_chains"]

    def find_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Find specific token by ID"""
        for token in self.wallet_data["tokens"]:
            if token["token_id"] == token_id:
                return token
        return None

    def validate_token(self, token_id: str) -> bool:
        """Validate a token in the wallet"""
        token = self.find_token(token_id)
        if not token:
            return False

        return self._verify_token_signature(token)

    def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """Generate recovery codes for wallet access"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)

        # Hash codes for storage (never store plain text)
        hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in codes]

        self.wallet_data["recovery_codes"] = hashed_codes
        self._save_wallet(self.wallet_data)

        logging.info(f"Generated {count} recovery codes")
        return codes  # Return plain codes to user

    def validate_recovery_code(self, code: str) -> bool:
        """Validate a recovery code"""
        code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
        return code_hash in self.wallet_data.get("recovery_codes", [])

    def export_wallet(self, export_path: str):
        """Export wallet for backup"""
        export_data = {
            "wallet_id": self.wallet_data["wallet_id"],
            "export_timestamp": time.time(),
            "version": self.wallet_data["version"],
            "tokens": self.wallet_data["tokens"],
            "backup_chains": self.wallet_data["backup_chains"][-10:],  # Last 10 backups
            "metadata": self.wallet_data["metadata"]
        }

        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ Wallet exported to {export_path}")
        logging.info(f"Wallet exported to {export_path}")

    def create_chain_backup(self, chain_data: List[Dict]) -> str:
        """Create a blockchain backup from chain data"""
        backup_id = secrets.token_hex(8)

        backup = {
            "backup_id": backup_id,
            "timestamp": time.time(),
            "chain_length": len(chain_data),
            "latest_hash": chain_data[-1]["hash"] if chain_data else None,
            "chain_data": chain_data[-50:]  # Last 50 blocks
        }

        # Save backup file
        backup_file = self.backups_dir / f"backup_{backup_id}.json"
        with open(backup_file, 'w') as f:
            json.dump(backup, f, indent=2)

        # Add to wallet
        self.wallet_data["backup_chains"].append(backup)
        self._save_wallet(self.wallet_data)

        logging.info(f"Created chain backup: {backup_id}")
        return backup_id

    def restore_chain_backup(self, backup_id: str) -> Optional[Dict]:
        """Restore blockchain from backup"""
        for backup in self.wallet_data["backup_chains"]:
            if backup["backup_id"] == backup_id:
                return backup

        # Check backup files
        backup_file = self.backups_dir / f"backup_{backup_id}.json"
        if backup_file.exists():
            try:
                with open(backup_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load backup file: {e}")

        return None

    def get_wallet_status(self) -> Dict[str, Any]:
        """Get comprehensive wallet status"""
        return {
            "wallet_id": self.wallet_data["wallet_id"],
            "created_at": self.wallet_data["created_at"],
            "version": self.wallet_data["version"],
            "tokens_count": len(self.wallet_data["tokens"]),
            "backups_count": len(self.wallet_data["backup_chains"]),
            "recovery_codes_count": len(self.wallet_data.get("recovery_codes", [])),
            "last_backup": max([b["timestamp"] for b in self.wallet_data["backup_chains"]] or [0]),
            "wallet_dir": str(self.wallet_dir)
        }

def main():
    """CLI interface for backup wallet operations"""
    parser = argparse.ArgumentParser(description='314Sign Backup Wallet')
    parser.add_argument('--status', action='store_true', help='Show wallet status')
    parser.add_argument('--import-backup', metavar='FILE', help='Import wallet backup')
    parser.add_argument('--list-tokens', action='store_true', help='List tokens in wallet')
    parser.add_argument('--list-backups', action='store_true', help='List blockchain backups')
    parser.add_argument('--validate-token', metavar='TOKEN_ID', help='Validate specific token')
    parser.add_argument('--generate-recovery-codes', type=int, nargs='?', const=10, metavar='COUNT', help='Generate recovery codes')
    parser.add_argument('--validate-recovery-code', metavar='CODE', help='Validate recovery code')
    parser.add_argument('--export-wallet', metavar='PATH', help='Export wallet to file')
    parser.add_argument('--create-chain-backup', metavar='CHAIN_FILE', help='Create blockchain backup')
    parser.add_argument('--restore-chain-backup', metavar='BACKUP_ID', help='Restore blockchain backup')
    parser.add_argument('--wallet-dir', default='./314sign-wallet', help='Wallet directory')

    args = parser.parse_args()

    # Initialize wallet
    wallet = BackupWallet(args.wallet_dir)

    if args.status:
        status = wallet.get_wallet_status()
        print("314Sign Backup Wallet Status:")
        print(f"  Wallet ID: {status['wallet_id']}")
        print(f"  Version: {status['version']}")
        print(f"  Created: {time.ctime(status['created_at'])}")
        print(f"  Tokens: {status['tokens_count']}")
        print(f"  Backups: {status['backups_count']}")
        print(f"  Recovery Codes: {status['recovery_codes_count']}")
        if status['last_backup'] > 0:
            print(f"  Last Backup: {time.ctime(status['last_backup'])}")
        print(f"  Directory: {status['wallet_dir']}")

    elif args.import_backup:
        wallet.import_wallet_backup(args.import_backup)

    elif args.list_tokens:
        tokens = wallet.list_tokens()
        if tokens:
            print("Tokens in Wallet:")
            print("-" * 80)
            for token in tokens:
                print(f"  Token ID: {token['token_id']}")
                print(f"  Issued: {time.ctime(token['issued_at'])}")
                print(f"  Expires: {time.ctime(token['expires_at'])}")
                print(f"  Permissions: {token['permissions']}")
                print("-" * 80)
        else:
            print("No tokens in wallet")

    elif args.list_backups:
        backups = wallet.list_backups()
        if backups:
            print("Blockchain Backups:")
            print("-" * 80)
            for backup in backups:
                print(f"  ID: {backup.get('backup_id', 'unknown')}")
                print(f"  Timestamp: {time.ctime(backup['timestamp'])}")
                print(f"  Chain Length: {backup.get('chain_length', 0)}")
                print(f"  Latest Hash: {backup.get('latest_hash', 'N/A')[:16]}...")
                print("-" * 80)
        else:
            print("No backups in wallet")

    elif args.validate_token:
        if wallet.validate_token(args.validate_token):
            print(f"✅ Token {args.validate_token} is valid")
        else:
            print(f"❌ Token {args.validate_token} is invalid")

    elif args.generate_recovery_codes:
        codes = wallet.generate_recovery_codes(args.generate_recovery_codes)
        print("Generated Recovery Codes (save these securely!):")
        print("=" * 50)
        for i, code in enumerate(codes, 1):
            print(f"{i:2d}: {code}")
        print("=" * 50)
        print("⚠️  WARNING: Save these codes in a secure location!")
        print("   They cannot be recovered if lost.")

    elif args.validate_recovery_code:
        if wallet.validate_recovery_code(args.validate_recovery_code):
            print("✅ Recovery code is valid")
        else:
            print("❌ Recovery code is invalid")

    elif args.export_wallet:
        wallet.export_wallet(args.export_wallet)

    elif args.create_chain_backup:
        # Load chain data from file
        chain_file = Path(args.create_chain_backup)
        if chain_file.exists():
            try:
                with open(chain_file, 'r') as f:
                    chain_data = json.load(f)

                backup_id = wallet.create_chain_backup(chain_data)
                print(f"✅ Created chain backup: {backup_id}")

            except Exception as e:
                print(f"❌ Failed to create backup: {e}")
        else:
            print(f"❌ Chain file not found: {args.create_chain_backup}")

    elif args.restore_chain_backup:
        backup_data = wallet.restore_chain_backup(args.restore_chain_backup)
        if backup_data:
            print(f"✅ Restored backup {args.restore_chain_backup}:")
            print(f"   Chain Length: {backup_data.get('chain_length', 0)}")
            print(f"   Timestamp: {time.ctime(backup_data['timestamp'])}")

            # Export restored chain
            export_path = f"restored_chain_{args.restore_chain_backup}.json"
            with open(export_path, 'w') as f:
                json.dump(backup_data["chain_data"], f, indent=2)
            print(f"   Exported to: {export_path}")
        else:
            print(f"❌ Backup {args.restore_chain_backup} not found")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()