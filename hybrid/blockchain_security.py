#!/usr/bin/env python3
"""
314Sign Blockchain Security System
Implements blockchain-based security with custom 314ST tokens
"""

import hashlib
import json
import time
import threading
import secrets
import base64
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import logging

class SignBlock:
    """Individual block in the 314Sign blockchain"""

    def __init__(self, index: int, transactions: List[Dict], timestamp: float,
                 previous_hash: str, nonce: int = 0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of the block"""
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)

        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int = 4) -> bool:
        """Mine the block with proof-of-work"""
        target = "0" * difficulty

        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

            # Prevent infinite loop in testing
            if self.nonce > 1000000:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class SignToken:
    """314Sign Security Token (314ST)"""

    def __init__(self, token_id: str, token_type: str, issued_by: str,
                 permissions: List[str], validity_period: int = 31536000):  # 1 year
        self.token_id = token_id
        self.token_type = token_type
        self.issued_by = issued_by
        self.permissions = permissions
        self.issued_at = time.time()
        self.expires_at = self.issued_at + validity_period
        self.device_fingerprint = self._generate_device_fingerprint()
        self.blockchain_tx = None
        self.signature = None

    def _generate_device_fingerprint(self) -> str:
        """Generate unique device fingerprint"""
        try:
            # Use CPU serial for device identification
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        serial = line.split(':')[1].strip()
                        return hashlib.sha256(serial.encode()).hexdigest()
        except:
            # Fallback to random fingerprint
            return secrets.token_hex(32)

    def sign_token(self, private_key_pem: str) -> str:
        """Sign the token with RSA private key"""
        token_data = self.to_dict()
        token_json = json.dumps(token_data, sort_keys=True)

        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )

        # Sign the token
        signature = private_key.sign(
            token_json.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        self.signature = base64.b64encode(signature).decode()
        return self.signature

    def verify_token(self, public_key_pem: str) -> bool:
        """Verify token signature"""
        if not self.signature:
            return False

        token_data = self.to_dict()
        token_json = json.dumps(token_data, sort_keys=True)

        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )

            # Verify signature
            signature_bytes = base64.b64decode(self.signature)

            public_key.verify(
                signature_bytes,
                token_json.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Check expiration
            if time.time() > self.expires_at:
                return False

            return True

        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert token to dictionary"""
        return {
            "token_id": self.token_id,
            "token_type": self.token_type,
            "issued_by": self.issued_by,
            "permissions": self.permissions,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "device_fingerprint": self.device_fingerprint,
            "blockchain_tx": self.blockchain_tx
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignToken':
        """Create token from dictionary"""
        token = cls(
            token_id=data["token_id"],
            token_type=data["token_type"],
            issued_by=data["issued_by"],
            permissions=data["permissions"],
            validity_period=int(data["expires_at"] - data["issued_at"])
        )
        token.issued_at = data["issued_at"]
        token.expires_at = data["expires_at"]
        token.device_fingerprint = data["device_fingerprint"]
        token.blockchain_tx = data.get("blockchain_tx")
        return token

class SignChain:
    """314Sign Private Blockchain"""

    def __init__(self, chain_file: str = "/var/lib/314sign/blockchain.json",
                 difficulty: int = 4):
        self.chain_file = Path(chain_file)
        self.difficulty = difficulty
        self.chain: List[SignBlock] = []
        self.pending_transactions: List[Dict] = []
        self.lock = threading.Lock()

        # Load existing chain or create genesis
        self.load_chain()

    def create_genesis_block(self) -> SignBlock:
        """Create the genesis block"""
        genesis_transactions = [{
            "type": "genesis",
            "data": {
                "message": "314Sign Security Blockchain Initialized",
                "timestamp": time.time(),
                "version": "1.0.2.73"
            },
            "signature": "314sign-genesis-signature",
            "timestamp": time.time()
        }]

        genesis = SignBlock(
            index=0,
            transactions=genesis_transactions,
            timestamp=time.time(),
            previous_hash="0"
        )

        return genesis

    def load_chain(self):
        """Load blockchain from file"""
        if self.chain_file.exists():
            try:
                with open(self.chain_file, 'r') as f:
                    chain_data = json.load(f)

                self.chain = []
                for block_data in chain_data:
                    block = SignBlock(
                        index=block_data["index"],
                        transactions=block_data["transactions"],
                        timestamp=block_data["timestamp"],
                        previous_hash=block_data["previous_hash"],
                        nonce=block_data["nonce"]
                    )
                    block.hash = block_data["hash"]
                    self.chain.append(block)

                logging.info(f"Loaded blockchain with {len(self.chain)} blocks")

            except Exception as e:
                logging.error(f"Failed to load blockchain: {e}")
                self.chain = [self.create_genesis_block()]
                self.save_chain()
        else:
            # Create new blockchain
            self.chain = [self.create_genesis_block()]
            self.save_chain()

    def save_chain(self):
        """Save blockchain to file"""
        try:
            chain_data = [block.to_dict() for block in self.chain]

            # Ensure directory exists
            self.chain_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.chain_file, 'w') as f:
                json.dump(chain_data, f, indent=2)

        except Exception as e:
            logging.error(f"Failed to save blockchain: {e}")

    def add_transaction(self, transaction: Dict[str, Any]) -> str:
        """Add transaction to pending transactions"""
        with self.lock:
            # Add timestamp if not present
            if "timestamp" not in transaction:
                transaction["timestamp"] = time.time()

            self.pending_transactions.append(transaction)

            # Return transaction hash for tracking
            tx_string = json.dumps(transaction, sort_keys=True)
            return hashlib.sha256(tx_string.encode()).hexdigest()

    def mine_pending_transactions(self) -> Optional[SignBlock]:
        """Mine a new block with pending transactions"""
        if not self.pending_transactions:
            return None

        with self.lock:
            # Create new block
            last_block = self.chain[-1]
            new_block = SignBlock(
                index=last_block.index + 1,
                transactions=self.pending_transactions.copy(),
                timestamp=time.time(),
                previous_hash=last_block.hash
            )

            # Mine the block
            if new_block.mine_block(self.difficulty):
                # Add to chain
                self.chain.append(new_block)
                self.save_chain()

                # Clear pending transactions
                self.pending_transactions.clear()

                logging.info(f"Mined new block: {new_block.index} with {len(new_block.transactions)} transactions")
                return new_block
            else:
                logging.error("Failed to mine block")
                return None

    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction by hash"""
        for block in self.chain:
            for transaction in block.transactions:
                tx_string = json.dumps(transaction, sort_keys=True)
                if hashlib.sha256(tx_string.encode()).hexdigest() == tx_hash:
                    return transaction
        return None

    def validate_chain(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            # Check hash consistency
            if current.hash != current.calculate_hash():
                logging.error(f"Block {current.index} has invalid hash")
                return False

            # Check chain linkage
            if current.previous_hash != previous.hash:
                logging.error(f"Block {current.index} has invalid previous hash")
                return False

            # Check proof-of-work
            if not current.hash.startswith("0" * self.difficulty):
                logging.error(f"Block {current.index} has invalid proof-of-work")
                return False

        return True

    def get_chain_info(self) -> Dict[str, Any]:
        """Get blockchain information"""
        return {
            "blocks": len(self.chain),
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "latest_block": self.chain[-1].to_dict() if self.chain else None,
            "is_valid": self.validate_chain(),
            "network_health": self._calculate_network_health()
        }

    def _calculate_network_health(self) -> Dict[str, Any]:
        """Calculate network health metrics for adaptive systems"""
        if not self.chain:
            return {"participation": 0, "avg_block_time": 0, "health_score": 0}

        # Calculate average block time (last 10 blocks)
        recent_blocks = self.chain[-10:] if len(self.chain) > 1 else self.chain
        if len(recent_blocks) > 1:
            block_times = []
            for i in range(1, len(recent_blocks)):
                time_diff = recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
                block_times.append(time_diff)
            avg_block_time = sum(block_times) / len(block_times)
        else:
            avg_block_time = 600  # 10 minutes default

        # Participation score based on transaction volume
        total_txs = sum(len(block.transactions) for block in recent_blocks)
        participation = min(1.0, total_txs / 50)  # Scale to 0-1

        # Health score combines multiple factors
        health_score = (participation * 0.6) + ((1 - min(1, avg_block_time / 1200)) * 0.4)

        return {
            "participation": participation,
            "avg_block_time": avg_block_time,
            "health_score": health_score
        }

    def adapt_difficulty(self) -> int:
        """Adapt difficulty based on network health"""
        health = self._calculate_network_health()
        current_difficulty = self.difficulty

        # Target: 10 minute average block time
        target_block_time = 600
        actual_block_time = health["avg_block_time"]

        if actual_block_time < target_block_time * 0.8:
            # Blocks too fast - increase difficulty slightly
            new_difficulty = min(current_difficulty + 1, 8)  # Cap at 8
        elif actual_block_time > target_block_time * 1.2:
            # Blocks too slow - decrease difficulty
            new_difficulty = max(current_difficulty - 1, 2)  # Floor at 2
        else:
            # Optimal range - maintain current difficulty
            new_difficulty = current_difficulty

        if new_difficulty != current_difficulty:
            self.difficulty = new_difficulty
            logging.info(f"Difficulty adapted: {current_difficulty} → {new_difficulty}")

        return new_difficulty

    def calculate_mining_reward(self, block: SignBlock, miner_stats: Dict = None) -> int:
        """Calculate sustainable mining reward based on work performed"""
        if miner_stats is None:
            miner_stats = {}

        base_reward = 10  # Stable base reward

        # Transaction volume bonus (0.5 tokens per tx)
        tx_bonus = len(block.transactions) * 0.5

        # Security work bonus
        security_bonus = 0
        for tx in block.transactions:
            tx_type = tx.get('type', '')
            if tx_type in ['security_alert', 'threat_detected', 'system_compromise']:
                security_bonus += 3  # High value security work
            elif tx_type in ['device_auth', 'bundle_verify', 'token_validate']:
                security_bonus += 1  # Standard security work

        # Participation bonus based on network health
        health = self._calculate_network_health()
        participation_bonus = base_reward * (1 - health["participation"]) * 0.5

        # Uptime/reliability bonus
        uptime_bonus = miner_stats.get('uptime_percentage', 100) / 100 * 2

        # P2P contribution bonus
        p2p_bonus = miner_stats.get('p2p_contributions', 0) * 0.1

        total_reward = base_reward + tx_bonus + security_bonus + participation_bonus + uptime_bonus + p2p_bonus

        # Cap reward to prevent inflation
        return min(int(total_reward), 30)

class SignTokenMiner:
    """314Sign Token Mining System"""

    def __init__(self, blockchain: SignChain, tokens_file: str = "/var/lib/314sign/tokens.json"):
        self.blockchain = blockchain
        self.tokens_file = Path(tokens_file)
        self.tokens: Dict[str, SignToken] = {}
        self.mining_active = False
        self.mining_thread = None

        self.load_tokens()

    def load_tokens(self):
        """Load tokens from file"""
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, 'r') as f:
                    tokens_data = json.load(f)

                self.tokens = {}
                for token_data in tokens_data:
                    token = SignToken.from_dict(token_data)
                    self.tokens[token.token_id] = token

                logging.info(f"Loaded {len(self.tokens)} tokens")

            except Exception as e:
                logging.error(f"Failed to load tokens: {e}")
        else:
            self.tokens = {}

    def save_tokens(self):
        """Save tokens to file"""
        try:
            tokens_data = [token.to_dict() for token in self.tokens.values()]

            self.tokens_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.tokens_file, 'w') as f:
                json.dump(tokens_data, f, indent=2)

        except Exception as e:
            logging.error(f"Failed to save tokens: {e}")

    def generate_token(self, token_type: str, device_id: str,
                      permissions: List[str] = None) -> SignToken:
        """Generate a new 314ST token"""
        if permissions is None:
            permissions = ["read"]

        # Generate unique token ID
        token_id = f"314ST-{secrets.token_hex(4).upper()}-{int(time.time())}"

        # Create token
        token = SignToken(
            token_id=token_id,
            token_type=token_type,
            issued_by=device_id,
            permissions=permissions
        )

        # Sign token with system keys
        from security_keys import SecurityKeyManager
        key_manager = SecurityKeyManager()
        token.sign_token(key_manager.system_keys["rsa_private_key"])

        # Register token on blockchain
        blockchain_tx = self.blockchain.add_transaction({
            "type": "token_issuance",
            "token_id": token_id,
            "token_type": token_type,
            "issued_by": device_id,
            "permissions": permissions,
            "device_fingerprint": token.device_fingerprint,
            "signature": token.signature
        })

        token.blockchain_tx = blockchain_tx

        # Store token
        self.tokens[token_id] = token
        self.save_tokens()

        logging.info(f"Generated token: {token_id} for device: {device_id}")
        return token

    def validate_token(self, token_id: str) -> bool:
        """Validate token against blockchain"""
        if token_id not in self.tokens:
            return False

        token = self.tokens[token_id]

        # Check blockchain registration
        if token.blockchain_tx:
            blockchain_record = self.blockchain.get_transaction(token.blockchain_tx)
            if not blockchain_record:
                return False

            # Verify blockchain record matches token
            if (blockchain_record.get("token_id") != token_id or
                blockchain_record.get("signature") != token.signature):
                return False

        # Validate cryptographic signature
        from security_keys import SecurityKeyManager
        key_manager = SecurityKeyManager()
        return token.verify_token(key_manager.system_keys["rsa_public_key"])

    def start_mining(self):
        """Start background token mining"""
        if self.mining_thread and self.mining_thread.is_alive():
            return

        self.mining_active = True
        self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        self.mining_thread.start()

        logging.info("Started token mining")

    def stop_mining(self):
        """Stop token mining"""
        self.mining_active = False
        if self.mining_thread and self.mining_thread.is_alive():
            self.mining_thread.join(timeout=5)

        logging.info("Stopped token mining")

    def _mining_loop(self):
        """Background mining loop with adaptive difficulty and rewards"""
        mining_stats = {
            'blocks_mined': 0,
            'total_rewards': 0,
            'uptime_percentage': 100,
            'p2p_contributions': 0,
            'start_time': time.time()
        }

        while self.mining_active:
            try:
                # Adapt difficulty based on network health
                self.blockchain.adapt_difficulty()

                # Mine pending blockchain transactions
                block = self.blockchain.mine_pending_transactions()
                if block:
                    mining_stats['blocks_mined'] += 1

                    # Calculate sustainable mining reward
                    reward_amount = self.blockchain.calculate_mining_reward(block, mining_stats)
                    mining_stats['total_rewards'] += reward_amount

                    # Issue mining reward tokens
                    self._issue_mining_reward(reward_amount, block)

                    logging.info(f"⛏️ Mined block {block.index} with {len(block.transactions)} transactions")
                    logging.info(f"💰 Mining reward: {reward_amount} 314ST tokens")

                # Update uptime statistics
                uptime = (time.time() - mining_stats['start_time']) / 3600  # Hours
                if uptime > 0:
                    mining_stats['uptime_percentage'] = 95 + (mining_stats['blocks_mined'] / uptime)  # Base 95% + performance bonus

                # Adaptive sleep based on mining activity
                sleep_time = 30 if not block else 10  # Mine more frequently if recently successful
                time.sleep(sleep_time)

            except Exception as e:
                logging.error(f"Mining error: {e}")
                time.sleep(10)

    def _issue_mining_reward(self, reward_amount: int, block: SignBlock):
        """Issue mining reward tokens to the local wallet"""
        try:
            # Generate mining reward token
            reward_token = self.generate_token(
                token_type="mining_reward",
                device_id=f"miner-{self._get_device_id()}",
                permissions=["mining", "validation"]
            )

            # Add reward metadata
            reward_token.reward_amount = reward_amount
            reward_token.block_index = block.index
            reward_token.mining_timestamp = time.time()

            # Save updated token
            self.save_tokens()

            # Add to local wallet if available
            try:
                from sign_wallet import SignWallet
                wallet = SignWallet()
                wallet.add_token(reward_token)
                logging.info(f"💰 Mining reward added to wallet: {reward_amount} 314ST tokens")
            except:
                logging.debug("Local wallet not available for reward storage")

        except Exception as e:
            logging.error(f"Failed to issue mining reward: {e}")

    def _get_device_id(self) -> str:
        """Get unique device identifier for mining rewards"""
        try:
            # Use hostname or CPU serial for device identification
            hostname = subprocess.run(['hostname'], capture_output=True, text=True, timeout=2)
            if hostname.returncode == 0:
                return hostname.stdout.strip()
            return f"device-{secrets.token_hex(4)}"
        except:
            return f"unknown-{secrets.token_hex(4)}"

class SignWallet:
    """314Sign Blockchain Wallet for Backup and Recovery"""

    def __init__(self, wallet_file: str = "/var/lib/314sign/wallet.json",
                 blockchain: SignChain = None):
        self.wallet_file = Path(wallet_file)
        self.blockchain = blockchain
        self.wallet_data = self.load_wallet()

    def load_wallet(self) -> Dict[str, Any]:
        """Load wallet data"""
        if self.wallet_file.exists():
            try:
                with open(self.wallet_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load wallet: {e}")

        # Create new wallet
        return {
            "wallet_id": secrets.token_hex(16),
            "created_at": time.time(),
            "tokens": [],
            "transactions": [],
            "backup_chains": []
        }

    def save_wallet(self):
        """Save wallet data"""
        try:
            self.wallet_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.wallet_file, 'w') as f:
                json.dump(self.wallet_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save wallet: {e}")

    def add_token(self, token: SignToken):
        """Add token to wallet"""
        if token.token_id not in [t["token_id"] for t in self.wallet_data["tokens"]]:
            self.wallet_data["tokens"].append(token.to_dict())
            self.save_wallet()
            logging.info(f"Added token {token.token_id} to wallet")

    def backup_blockchain(self, blockchain: SignChain):
        """Backup blockchain state"""
        backup = {
            "timestamp": time.time(),
            "chain_length": len(blockchain.chain),
            "latest_hash": blockchain.chain[-1].hash if blockchain.chain else None,
            "chain_data": [block.to_dict() for block in blockchain.chain[-10:]]  # Last 10 blocks
        }

        self.wallet_data["backup_chains"].append(backup)
        self.save_wallet()

        logging.info(f"Backed up blockchain state (length: {len(blockchain.chain)})")

    def restore_blockchain(self, target_chain: SignChain) -> bool:
        """Restore blockchain from wallet backup"""
        if not self.wallet_data["backup_chains"]:
            return False

        # Get latest backup
        latest_backup = max(self.wallet_data["backup_chains"],
                          key=lambda x: x["timestamp"])

        try:
            # Restore chain data
            restored_chain = []
            for block_data in latest_backup["chain_data"]:
                block = SignBlock(
                    index=block_data["index"],
                    transactions=block_data["transactions"],
                    timestamp=block_data["timestamp"],
                    previous_hash=block_data["previous_hash"],
                    nonce=block_data["nonce"]
                )
                block.hash = block_data["hash"]
                restored_chain.append(block)

            target_chain.chain = restored_chain
            target_chain.save_chain()

            logging.info(f"Restored blockchain from backup (length: {len(restored_chain)})")
            return True

        except Exception as e:
            logging.error(f"Blockchain restoration failed: {e}")
            return False

    def export_wallet(self, export_path: str):
        """Export wallet for backup on other hardware"""
        export_data = {
            "wallet_id": self.wallet_data["wallet_id"],
            "export_timestamp": time.time(),
            "tokens": self.wallet_data["tokens"],
            "backup_chains": self.wallet_data["backup_chains"][-5:]  # Last 5 backups
        }

        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logging.info(f"Wallet exported to {export_path}")

    def import_wallet(self, import_path: str):
        """Import wallet from backup"""
        import_file = Path(import_path)

        if not import_file.exists():
            logging.error(f"Import file not found: {import_path}")
            return False

        try:
            with open(import_file, 'r') as f:
                import_data = json.load(f)

            # Merge tokens (avoid duplicates)
            existing_token_ids = {t["token_id"] for t in self.wallet_data["tokens"]}
            for token in import_data["tokens"]:
                if token["token_id"] not in existing_token_ids:
                    self.wallet_data["tokens"].append(token)

            # Merge backup chains
            self.wallet_data["backup_chains"].extend(import_data["backup_chains"])

            self.save_wallet()

            logging.info(f"Wallet imported from {import_path}")
            return True

        except Exception as e:
            logging.error(f"Wallet import failed: {e}")
            return False

def main():
    """CLI interface for blockchain operations"""
    import argparse

    parser = argparse.ArgumentParser(description='314Sign Blockchain System')
    parser.add_argument('--status', action='store_true', help='Show blockchain status')
    parser.add_argument('--generate-token', metavar='DEVICE_ID', help='Generate token for device')
    parser.add_argument('--validate-token', metavar='TOKEN_ID', help='Validate token')
    parser.add_argument('--mine-block', action='store_true', help='Mine pending transactions')
    parser.add_argument('--start-mining', action='store_true', help='Start background mining')
    parser.add_argument('--stop-mining', action='store_true', help='Stop background mining')
    parser.add_argument('--wallet-status', action='store_true', help='Show wallet status')
    parser.add_argument('--backup-chain', action='store_true', help='Backup blockchain to wallet')
    parser.add_argument('--export-wallet', metavar='PATH', help='Export wallet to file')
    parser.add_argument('--import-wallet', metavar='PATH', help='Import wallet from file')

    args = parser.parse_args()

    # Initialize components
    blockchain = SignChain()
    token_miner = SignTokenMiner(blockchain)
    wallet = SignWallet(blockchain=blockchain)

    if args.status:
        chain_info = blockchain.get_chain_info()
        print("314Sign Blockchain Status:")
        print(f"  Blocks: {chain_info['blocks']}")
        print(f"  Pending TX: {chain_info['pending_transactions']}")
        print(f"  Difficulty: {chain_info['difficulty']}")
        print(f"  Valid Chain: {'✓' if chain_info['is_valid'] else '✗'}")

        if chain_info['latest_block']:
            block = chain_info['latest_block']
            print(f"  Latest Block: {block['index']} ({len(block['transactions'])} TX)")

    elif args.generate_token:
        token = token_miner.generate_token("security", args.generate_token)
        wallet.add_token(token)
        print(f"✅ Generated token: {token.token_id}")
        print(f"   Type: {token.token_type}")
        print(f"   Permissions: {token.permissions}")
        print(f"   Blockchain TX: {token.blockchain_tx}")

    elif args.validate_token:
        if token_miner.validate_token(args.validate_token):
            print(f"✅ Token {args.validate_token} is valid")
        else:
            print(f"❌ Token {args.validate_token} is invalid")

    elif args.mine_block:
        block = blockchain.mine_pending_transactions()
        if block:
            print(f"⛏️ Mined block {block.index} with {len(block.transactions)} transactions")
            print(f"   Hash: {block.hash}")
        else:
            print("❌ No blocks to mine or mining failed")

    elif args.start_mining:
        token_miner.start_mining()
        print("⛏️ Started background mining")

    elif args.stop_mining:
        token_miner.stop_mining()
        print("⛏️ Stopped background mining")

    elif args.wallet_status:
        print("314Sign Wallet Status:")
        print(f"  Wallet ID: {wallet.wallet_data['wallet_id']}")
        print(f"  Tokens: {len(wallet.wallet_data['tokens'])}")
        print(f"  Backups: {len(wallet.wallet_data['backup_chains'])}")
        print(f"  Created: {time.ctime(wallet.wallet_data['created_at'])}")

    elif args.backup_chain:
        wallet.backup_blockchain(blockchain)
        print("✅ Blockchain backed up to wallet")

    elif args.export_wallet:
        wallet.export_wallet(args.export_wallet)
        print(f"✅ Wallet exported to {args.export_wallet}")

    elif args.import_wallet:
        if wallet.import_wallet(args.import_wallet):
            print(f"✅ Wallet imported from {args.import_wallet}")
        else:
            print(f"❌ Wallet import failed")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()