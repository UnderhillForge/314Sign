#!/usr/bin/env python3
"""
314Sign Standalone Mining Node
Dedicated mining client for 314ST tokens - Pi hardware only
Can run independently of the full kiosk system
"""

import time
import threading
import argparse
import logging
from pathlib import Path
import sys

# Import 314Sign components
from bc_security.blockchain_security import SignChain, SignTokenMiner, SignWallet, HardwareVerifier

class StandaloneMiningNode:
    """
    Standalone mining node for 314ST token mining
    Optimized for continuous operation on Raspberry Pi hardware
    """

    def __init__(self, wallet_path: str = "./314sign-wallet", log_level: str = "INFO"):
        self.wallet_path = Path(wallet_path)
        self.running = False

        # Setup logging
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mining_node.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MiningNode')

        # Initialize components
        self.blockchain = SignChain()
        self.wallet = SignWallet(wallet_file=str(self.wallet_path / "wallet.json"))
        self.hardware_verifier = HardwareVerifier()

        # Mining components (initialized after hardware verification)
        self.token_miner = None

        # Mining statistics
        self.mining_stats = {
            'start_time': time.time(),
            'blocks_mined': 0,
            'tokens_earned': 0,
            'uptime_hours': 0,
            'hardware_verified': False,
            'verification_confidence': 0.0
        }

        self.logger.info("314Sign Standalone Mining Node initialized")

    def verify_hardware(self) -> bool:
        """Verify this is running on verified Pi hardware"""
        self.logger.info("🔍 Verifying Raspberry Pi hardware...")

        verification = self.hardware_verifier.verify_mining_eligibility()

        if verification['eligible']:
            self.mining_stats['hardware_verified'] = True
            self.mining_stats['verification_confidence'] = verification['confidence_score']

            self.logger.info("✅ Hardware verification PASSED")
            self.logger.info(f"   📱 Device: {verification['hardware_model']}")
            self.logger.info(".1%")
            self.logger.info(f"   🔒 Anti-spoofing: {'✓' if verification['anti_spoofing_passed'] else '✗'}")

            return True
        else:
            self.logger.error("❌ Hardware verification FAILED")
            self.logger.error("   This mining node requires Raspberry Pi hardware")
            self.logger.error(".1%")
            self.logger.error(f"   Device detected: {verification['hardware_model']}")

            return False

    def initialize_wallet(self) -> bool:
        """Initialize or verify wallet"""
        try:
            wallet_status = self.wallet.get_wallet_status()
            self.logger.info("💰 Wallet initialized")
            self.logger.info(f"   Wallet ID: {wallet_status['wallet_id'][:16]}...")
            self.logger.info(f"   Tokens: {wallet_status['tokens_count']}")

            # Check if wallet has tokens (for loan eligibility)
            token_count = wallet_status['tokens_count']
            if token_count == 0:
                self.logger.info("   💡 Empty wallet - eligible for trust loan when kiosk starts")
            else:
                self.logger.info("   ✅ Wallet has tokens - ready for mining rewards")

            return True

        except Exception as e:
            self.logger.error(f"Wallet initialization failed: {e}")
            return False

    def start_mining(self) -> bool:
        """Start the mining operation"""
        if not self.mining_stats['hardware_verified']:
            self.logger.error("Cannot start mining - hardware verification failed")
            return False

        self.logger.info("⛏️ Starting 314ST token mining...")

        try:
            # Initialize token miner
            self.token_miner = SignTokenMiner(self.blockchain)

            # Override the hardware verifier to use our verified one
            self.token_miner.hardware_verifier = self.hardware_verifier

            # Start mining
            mining_started = self.token_miner.start_mining()

            if mining_started:
                self.running = True
                self.logger.info("✅ Mining started successfully")
                self.logger.info("   📊 Mining rewards will be credited to wallet")
                self.logger.info("   💡 Press Ctrl+C to stop mining")

                # Start statistics monitoring
                stats_thread = threading.Thread(target=self._monitor_mining_stats, daemon=True)
                stats_thread.start()

                return True
            else:
                self.logger.error("❌ Failed to start mining")
                return False

        except Exception as e:
            self.logger.error(f"Mining startup failed: {e}")
            return False

    def stop_mining(self):
        """Stop the mining operation"""
        self.logger.info("⛏️ Stopping mining...")

        if self.token_miner:
            self.token_miner.stop_mining()

        self.running = False
        self.logger.info("✅ Mining stopped")

        # Show final statistics
        self._show_mining_stats()

    def _monitor_mining_stats(self):
        """Monitor and display mining statistics"""
        last_stats_time = time.time()

        while self.running:
            try:
                current_time = time.time()

                # Update uptime
                self.mining_stats['uptime_hours'] = (current_time - self.mining_stats['start_time']) / 3600

                # Show stats every 5 minutes
                if current_time - last_stats_time >= 300:
                    self._show_mining_stats()
                    last_stats_time = current_time

                time.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Stats monitoring error: {e}")
                time.sleep(10)

    def _show_mining_stats(self):
        """Display current mining statistics"""
        stats = self.mining_stats

        self.logger.info("📊 Mining Statistics:")
        self.logger.info(f"   ⏱️  Uptime: {stats['uptime_hours']:.1f} hours")
        self.logger.info(f"   ⛏️  Blocks mined: {stats['blocks_mined']}")
        self.logger.info(f"   💰 Tokens earned: {stats['tokens_earned']}")
        self.logger.info(f"   🔒 Hardware verified: {'✓' if stats['hardware_verified'] else '✗'}")
        self.logger.info(".1%")

        # Show mining rate if we've been running for a while
        if stats['uptime_hours'] > 0.1:  # More than 6 minutes
            blocks_per_hour = stats['blocks_mined'] / stats['uptime_hours']
            tokens_per_hour = stats['tokens_earned'] / stats['uptime_hours']
            self.logger.info(".2f")
            self.logger.info(".2f")

    def run(self):
        """Main mining node operation"""
        self.logger.info("🚀 Starting 314Sign Standalone Mining Node")
        self.logger.info("=" * 50)

        # Step 1: Hardware verification
        if not self.verify_hardware():
            self.logger.error("❌ Mining node cannot start on non-Pi hardware")
            return False

        # Step 2: Wallet initialization
        if not self.initialize_wallet():
            self.logger.error("❌ Wallet initialization failed")
            return False

        # Step 3: Start mining
        if not self.start_mining():
            self.logger.error("❌ Mining startup failed")
            return False

        self.logger.info("✅ Mining node is now running!")
        self.logger.info("   📝 Check mining_node.log for detailed logs")
        self.logger.info("   💡 Mining rewards automatically credit to wallet")
        self.logger.info("   🔄 Statistics update every 5 minutes")

        try:
            # Keep running until interrupted
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("⏹️  Received shutdown signal")

        finally:
            self.stop_mining()

        return True

def main():
    """CLI interface for standalone mining node"""
    parser = argparse.ArgumentParser(description='314Sign Standalone Mining Node')
    parser.add_argument('--wallet-dir', default='./314sign-wallet',
                       help='Wallet directory path')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--version', action='version', version='314Sign Mining Node v1.0.2.77')

    args = parser.parse_args()

    # Create mining node
    mining_node = StandaloneMiningNode(
        wallet_path=args.wallet_dir,
        log_level=args.log_level
    )

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n⏹️  Shutting down mining node...")
        mining_node.stop_mining()
        sys.exit(0)

    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the mining node
    success = mining_node.run()

    if success:
        print("✅ Mining node completed successfully")
        sys.exit(0)
    else:
        print("❌ Mining node failed to start")
        sys.exit(1)

if __name__ == "__main__":
    main()