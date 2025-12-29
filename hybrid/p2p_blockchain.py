#!/usr/bin/env python3
"""
314Sign Peer-to-Peer Blockchain Network
Distributed blockchain with security event sharing across trusted kiosks
"""

import socket
import threading
import json
import time
import hashlib
import secrets
import ssl
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from queue import Queue
import logging
from datetime import datetime, timedelta

class P2PBlockchainNetwork:
    """
    Peer-to-peer blockchain network for 314Sign kiosks
    Enables distributed security event sharing and blockchain synchronization
    """

    def __init__(self, local_blockchain, network_config: Dict[str, Any]):
        self.local_blockchain = local_blockchain
        self.network_config = network_config
        self.peers: Dict[str, Dict] = {}  # peer_id -> peer_info
        self.peer_connections: Dict[str, socket.socket] = {}
        self.message_queue = Queue()
        self.running = False

        # Network configuration
        self.listen_port = network_config.get('listen_port', 31450)
        self.max_peers = network_config.get('max_peers', 10)
        self.heartbeat_interval = network_config.get('heartbeat_interval', 30)
        self.sync_interval = network_config.get('sync_interval', 300)  # 5 minutes

        # Decentralized bootstrap configuration
        self.peer_registry_file = network_config.get('peer_registry_file', "/var/lib/314sign/peer_registry.json")
        self.peer_cache_file = network_config.get('peer_cache_file', "peer_cache.json")
        self.bootstrap_election_interval = network_config.get('bootstrap_election_interval', 3600)  # 1 hour

        # Load peer registry and cache
        self.peer_registry = self._load_peer_registry()
        self.peer_cache = self._load_peer_cache()

        # Legacy bootstrap nodes (for backwards compatibility during transition)
        self.legacy_bootstrap_nodes = network_config.get('legacy_bootstrap_nodes', [])

        # Security
        self.trusted_peers = set(network_config.get('trusted_peers', []))
        self.network_secret = network_config.get('network_secret', '')
        self.enable_nat_traversal = network_config.get('nat_traversal', True)

        # Threads
        self.listener_thread = None
        self.processor_thread = None
        self.heartbeat_thread = None
        self.sync_thread = None

        # Setup logging
        self.logger = logging.getLogger('P2PNetwork')

        # Track start time for uptime calculations
        self.start_time = time.time()

    def start(self):
        """Start the P2P network"""
        if self.running:
            return

        self.running = True
        self.logger.info("Starting P2P blockchain network")

        # Start network threads
        self.listener_thread = threading.Thread(target=self._listen_for_peers, daemon=True)
        self.processor_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        self.sync_thread = threading.Thread(target=self._blockchain_sync, daemon=True)

        self.listener_thread.start()
        self.processor_thread.start()
        self.heartbeat_thread.start()
        self.sync_thread.start()

        # Discover initial peers
        self._discover_peers()

    def stop(self):
        """Stop the P2P network"""
        if not self.running:
            return

        self.running = False
        self.logger.info("Stopping P2P blockchain network")

        # Close all connections
        for peer_id, conn in self.peer_connections.items():
            try:
                conn.close()
            except:
                pass

        self.peer_connections.clear()
        self.peers.clear()

    def _listen_for_peers(self):
        """Listen for incoming peer connections"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', self.listen_port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Non-blocking accept

            self.logger.info(f"Listening for P2P connections on port {self.listen_port}")

            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    self.logger.info(f"Accepted connection from {address}")

                    # Handle connection in separate thread
                    threading.Thread(
                        target=self._handle_peer_connection,
                        args=(client_socket, address),
                        daemon=True
                    ).start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")

            server_socket.close()

        except Exception as e:
            self.logger.error(f"P2P listener error: {e}")

    def _handle_peer_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle incoming peer connection"""
        try:
            # Perform handshake
            peer_info = self._perform_handshake(client_socket, address)
            if not peer_info:
                client_socket.close()
                return

            peer_id = peer_info['peer_id']

            # Check if we want to connect to this peer
            if not self._should_accept_peer(peer_info):
                self._send_message(client_socket, {'type': 'reject', 'reason': 'not_trusted'})
                client_socket.close()
                return

            # Accept connection
            self._send_message(client_socket, {'type': 'accept', 'local_info': self._get_local_info()})

            # Add to connected peers
            self.peers[peer_id] = peer_info
            self.peer_connections[peer_id] = client_socket

            self.logger.info(f"Connected to peer {peer_id} at {address}")

            # Start message handling for this peer
            self._handle_peer_messages(peer_id, client_socket)

        except Exception as e:
            self.logger.error(f"Error handling peer connection from {address}: {e}")
            try:
                client_socket.close()
            except:
                pass

    def _perform_handshake(self, sock: socket.socket, address: Tuple[str, int]) -> Optional[Dict]:
        """Perform secure handshake with potential peer"""
        try:
            # Send our identity
            local_info = self._get_local_info()
            self._send_message(sock, {'type': 'handshake', 'info': local_info})

            # Receive peer identity
            response = self._receive_message(sock, timeout=10)
            if not response or response.get('type') != 'handshake':
                return None

            peer_info = response['info']
            peer_info['address'] = address
            peer_info['connected_at'] = time.time()
            peer_info['last_seen'] = time.time()

            # Verify peer identity
            if not self._verify_peer_identity(peer_info):
                return None

            return peer_info

        except Exception as e:
            self.logger.error(f"Handshake failed with {address}: {e}")
            return None

    def _verify_peer_identity(self, peer_info: Dict) -> bool:
        """Verify that the peer is legitimate and trusted"""
        peer_id = peer_info.get('peer_id')
        if not peer_id:
            return False

        # Check if peer is in trusted list
        if peer_id not in self.trusted_peers:
            self.logger.warning(f"Rejected connection from untrusted peer: {peer_id}")
            return False

        # Verify network secret
        network_secret = peer_info.get('network_secret')
        if network_secret != self.network_secret:
            self.logger.warning(f"Peer {peer_id} provided incorrect network secret")
            return False

        # Verify blockchain compatibility
        peer_version = peer_info.get('version', '1.0.0')
        if not self._is_version_compatible(peer_version):
            self.logger.warning(f"Peer {peer_id} has incompatible version: {peer_version}")
            return False

        return True

    def _should_accept_peer(self, peer_info: Dict) -> bool:
        """Determine if we should accept this peer connection"""
        peer_id = peer_info['peer_id']

        # Check connection limits
        if len(self.peer_connections) >= self.max_peers:
            return False

        # Check if already connected
        if peer_id in self.peer_connections:
            return False

        # Additional checks can be added here
        return True

    def _get_local_info(self) -> Dict[str, Any]:
        """Get local kiosk information for peer handshake"""
        return {
            'peer_id': self._generate_peer_id(),
            'hostname': socket.gethostname(),
            'version': '1.0.2.77',
            'blockchain_height': len(self.local_blockchain.chain) if hasattr(self.local_blockchain, 'chain') else 0,
            'last_block_hash': self.local_blockchain.chain[-1].hash if hasattr(self.local_blockchain, 'chain') and self.local_blockchain.chain else None,
            'capabilities': ['blockchain_sync', 'security_events', 'bundle_sharing'],
            'network_secret': self.network_secret,
            'timestamp': time.time()
        }

    def _generate_peer_id(self) -> str:
        """Generate unique peer identifier"""
        # Use hostname + CPU serial for uniqueness
        try:
            hostname = socket.gethostname()
            # In real implementation, would use CPU serial
            unique_id = f"{hostname}-{secrets.token_hex(4)}"
            return hashlib.sha256(unique_id.encode()).hexdigest()[:16]
        except:
            return secrets.token_hex(8)

    def _discover_peers(self):
        """Discover potential peers using multiple discovery methods"""
        self.logger.info("Starting comprehensive peer discovery")

        # Method 1: Local mDNS discovery
        self._discover_peers_mdns()

        # Method 2: Bootstrap node connections
        self._discover_peers_bootstrap()

        # Method 3: DNS seed resolution
        self._discover_peers_dns_seeds()

        # Method 4: Peer exchange from connected peers
        self._request_peer_exchange()

    def _discover_peers_mdns(self):
        """Discover peers using local mDNS/Bonjour"""
        try:
            from mdns_discovery import MDNSDiscovery

            # Look for other 314Sign kiosks on local network
            discovery = MDNSDiscovery("_314sign-kiosk._tcp.local.", timeout=5)
            devices = discovery.discover_devices()

            discovered_count = 0
            for device_info in devices.values():
                if device_info.get('mode') in ['main', 'remote']:
                    peer_address = device_info.get('address')
                    peer_port = device_info.get('port', self.listen_port)

                    if peer_address and peer_address != self._get_local_ip():
                        # Attempt to connect to discovered peer
                        threading.Thread(
                            target=self._connect_to_peer,
                            args=(peer_address, peer_port, 'mdns'),
                            daemon=True
                        ).start()
                        discovered_count += 1

            self.logger.info(f"mDNS discovery found {discovered_count} local peers")

        except Exception as e:
            self.logger.error(f"mDNS peer discovery failed: {e}")

    def _discover_peers_bootstrap(self):
        """Connect to dynamically elected bootstrap nodes from blockchain"""
        bootstrap_peers = self._get_bootstrap_peers_from_blockchain()

        connected_count = 0

        for bootstrap_addr in bootstrap_peers[:5]:  # Try top 5 elected bootstrap peers
            try:
                if ':' in bootstrap_addr:
                    host, port_str = bootstrap_addr.split(':', 1)
                    port = int(port_str)
                else:
                    host = bootstrap_addr
                    port = self.listen_port

                self.logger.debug(f"Attempting decentralized bootstrap connection to {host}:{port}")

                # Attempt connection
                threading.Thread(
                    target=self._connect_to_peer,
                    args=(host, port, 'decentralized_bootstrap'),
                    daemon=True
                ).start()

                connected_count += 1

            except Exception as e:
                self.logger.debug(f"Decentralized bootstrap connection to {bootstrap_addr} failed: {e}")

        # Fallback to legacy bootstrap nodes if no blockchain peers found
        if connected_count == 0 and self.legacy_bootstrap_nodes:
            self.logger.info("No blockchain bootstrap peers found, using legacy fallback")
            for bootstrap_node in self.legacy_bootstrap_nodes[:3]:  # Try first 3 legacy nodes
                try:
                    if ':' in bootstrap_node:
                        host, port_str = bootstrap_node.split(':', 1)
                        port = int(port_str)
                    else:
                        host = bootstrap_node
                        port = self.listen_port

                    threading.Thread(
                        target=self._connect_to_peer,
                        args=(host, port, 'legacy_bootstrap'),
                        daemon=True
                    ).start()

                    connected_count += 1

                except Exception as e:
                    self.logger.debug(f"Legacy bootstrap connection to {bootstrap_node} failed: {e}")

        self.logger.info(f"Initiated {connected_count} bootstrap connections")

    def _discover_peers_dns_seeds(self):
        """Resolve peers from DNS seed servers (placeholder for future)"""
        # For now, this is a placeholder for DNS seed functionality
        # In a full implementation, this would resolve domain names to peer IPs
        # Since we have decentralized bootstrap, this is less critical

        self.logger.debug("DNS seed discovery not implemented - using decentralized bootstrap")

        # Could implement DNS seed resolution here in the future
        # For now, rely on decentralized bootstrap and peer exchange

    def _request_peer_exchange(self):
        """Request peer lists from connected peers"""
        if not self.peer_connections:
            return

        # Request peer exchange from a few random peers
        peer_ids = list(self.peer_connections.keys())
        exchange_count = min(3, len(peer_ids))  # Ask up to 3 peers

        for i in range(exchange_count):
            peer_id = peer_ids[i % len(peer_ids)]
            try:
                self._send_to_peer(peer_id, {
                    'type': 'peer_exchange_request',
                    'timestamp': time.time()
                })
                self.logger.debug(f"Requested peer exchange from {peer_id}")
            except Exception as e:
                self.logger.debug(f"Peer exchange request failed for {peer_id}: {e}")

    def _connect_to_peer(self, address: str, port: int, discovery_method: str = 'manual'):
        """Attempt to connect to a discovered peer"""
        try:
            # Skip if already connected
            for peer_info in self.peers.values():
                if peer_info.get('address') == (address, port):
                    return

            # Skip local addresses
            if address in ['127.0.0.1', 'localhost', '::1'] or address == self._get_local_ip():
                return

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)

            self.logger.debug(f"Connecting to peer {address}:{port} via {discovery_method}")
            sock.connect((address, port))

            # Store discovery method in peer info
            peer_info = {'discovery_method': discovery_method}
            self._handle_peer_connection(sock, (address, port), peer_info)

        except Exception as e:
            self.logger.debug(f"Failed to connect to peer {address}:{port} ({discovery_method}): {e}")

    def _handle_peer_connection(self, client_socket: socket.socket, address: Tuple[str, int],
                               peer_info: Dict = None):
        """Handle incoming peer connection"""
        if peer_info is None:
            peer_info = {}

        try:
            # Perform handshake
            peer_info.update(self._perform_handshake(client_socket, address))
            if not peer_info:
                client_socket.close()
                return

            peer_id = peer_info['peer_id']

            # Check if we want to connect to this peer
            if not self._should_accept_peer(peer_info):
                self._send_message(client_socket, {'type': 'reject', 'reason': 'not_trusted'})
                client_socket.close()
                return

            # Accept connection
            self._send_message(client_socket, {'type': 'accept', 'local_info': self._get_local_info()})

            # Add to connected peers
            self.peers[peer_id] = peer_info
            self.peer_connections[peer_id] = client_socket

            self.logger.info(f"Connected to peer {peer_id} at {address} ({peer_info.get('discovery_method', 'unknown')})")

            # Register self as potential bootstrap peer
            self._register_self_as_bootstrap()

            # Start message handling for this peer
            self._handle_peer_messages(peer_id, client_socket)

        except Exception as e:
            self.logger.error(f"Error handling peer connection from {address}: {e}")
            try:
                client_socket.close()
            except:
                pass

    def _load_peer_registry(self) -> Dict[str, Dict]:
        """Load peer registry from blockchain and file"""
        registry = {}

        try:
            # Load from file first
            if os.path.exists(self.peer_registry_file):
                with open(self.peer_registry_file, 'r') as f:
                    registry = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load peer registry: {e}")

        # Update from blockchain (more recent registrations)
        if hasattr(self.local_blockchain, 'chain'):
            for block in reversed(self.local_blockchain.chain[-50:]):  # Last 50 blocks
                for tx in block.transactions:
                    if tx.get('type') == 'peer_registration':
                        peer_id = tx.get('peer_id')
                        if peer_id:
                            registry[peer_id] = {
                                'registration': tx,
                                'block_height': block.index,
                                'last_updated': block.timestamp
                            }

        self.logger.info(f"Loaded peer registry with {len(registry)} entries")
        return registry

    def _load_peer_cache(self) -> List[str]:
        """Load recently connected peer cache"""
        cache = []

        try:
            if os.path.exists(self.peer_cache_file):
                with open(self.peer_cache_file, 'r') as f:
                    cache_data = json.load(f)

                    # Check if cache is recent (24 hours)
                    if time.time() - cache_data.get('timestamp', 0) < 86400:
                        cache = cache_data.get('peers', [])
                        self.logger.info(f"Loaded peer cache with {len(cache)} entries")
        except Exception as e:
            self.logger.error(f"Failed to load peer cache: {e}")

        return cache

    def _save_peer_cache(self):
        """Save current peer connections to cache"""
        try:
            cache_data = {
                'timestamp': time.time(),
                'peers': list(self.peers.keys()),
                'version': '1.0'
            }

            with open(self.peer_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save peer cache: {e}")

    def _register_self_as_bootstrap(self):
        """Register this node as a potential bootstrap peer"""
        try:
            # Calculate uptime score (how long we've been running)
            uptime_score = min(1.0, (time.time() - self.start_time) / 86400)  # Max 1.0 for 24h+

            # Get geographic region (simplified)
            geo_region = self._get_geographic_region()

            # Get public IP (if available)
            public_ip = self._get_public_ip()

            if not public_ip:
                return  # Can't register without public IP

            # Create registration transaction
            registration = {
                'type': 'peer_registration',
                'peer_id': self._generate_peer_id(),
                'public_ip': public_ip,
                'port': self.listen_port,
                'uptime_score': uptime_score,
                'geographic_region': geo_region,
                'capabilities': ['bootstrap', 'mining', 'storage'],
                'registration_timestamp': time.time(),
                'version': '1.0.2.77'
            }

            # Add to blockchain
            if hasattr(self.local_blockchain, 'add_transaction'):
                tx_hash = self.local_blockchain.add_transaction(registration)
                self.logger.info(f"Registered as bootstrap peer: {registration['peer_id'][:12]}...")

                # Update local registry
                self.peer_registry[self._generate_peer_id()] = {
                    'registration': registration,
                    'block_height': len(self.local_blockchain.chain) if hasattr(self.local_blockchain, 'chain') else 0,
                    'last_updated': time.time()
                }

        except Exception as e:
            self.logger.error(f"Failed to register as bootstrap peer: {e}")

    def _get_bootstrap_peers_from_blockchain(self) -> List[str]:
        """Elect bootstrap peers from blockchain registry"""
        candidates = []

        # Collect all peer registrations from recent blocks
        if hasattr(self.local_blockchain, 'chain'):
            for block in self.local_blockchain.chain[-100:]:  # Last 100 blocks
                for tx in block.transactions:
                    if tx.get('type') == 'peer_registration':
                        candidates.append(tx)

        if not candidates:
            # Fallback to legacy bootstrap nodes
            return self.legacy_bootstrap_nodes

        # Score and rank candidates
        scored_candidates = []
        current_time = time.time()

        for candidate in candidates:
            score = self._calculate_bootstrap_score(candidate, current_time)
            scored_candidates.append((score, candidate))

        # Sort by score (highest first)
        scored_candidates.sort(reverse=True)

        # Select top candidates, ensuring geographic diversity
        selected_peers = []
        regions_used = set()

        for score, candidate in scored_candidates[:20]:  # Consider top 20
            region = candidate.get('geographic_region', 'unknown')

            # Allow max 3 peers per region for diversity
            if region not in regions_used or list(regions_used).count(region) < 3:
                ip = candidate.get('public_ip')
                port = candidate.get('port', self.listen_port)

                if ip and ip != self._get_local_ip():
                    selected_peers.append(f"{ip}:{port}")
                    regions_used.add(region)

                    if len(selected_peers) >= 10:  # Max 10 bootstrap peers
                        break

        self.logger.info(f"Elected {len(selected_peers)} bootstrap peers from {len(candidates)} candidates")
        return selected_peers

    def _calculate_bootstrap_score(self, candidate: Dict, current_time: float) -> float:
        """Calculate bootstrap peer score based on stability and reliability"""
        score = 0.0

        # Uptime score (0-40 points)
        uptime_score = candidate.get('uptime_score', 0)
        score += uptime_score * 40

        # Age of registration (0-20 points) - prefer established peers
        registration_age = current_time - candidate.get('registration_timestamp', current_time)
        age_score = min(1.0, registration_age / (30 * 24 * 3600))  # Max at 30 days
        score += age_score * 20

        # Version compatibility (0-20 points)
        version = candidate.get('version', '0.0.0')
        if self._is_version_compatible(version):
            score += 20

        # Capabilities bonus (0-10 points)
        capabilities = candidate.get('capabilities', [])
        if 'bootstrap' in capabilities:
            score += 5
        if 'mining' in capabilities:
            score += 3
        if 'storage' in capabilities:
            score += 2

        # Geographic diversity bonus (0-10 points)
        # Prefer peers in different regions for global distribution
        region = candidate.get('geographic_region', 'unknown')
        if region != 'unknown':
            score += 10

        return score

    def _get_geographic_region(self) -> str:
        """Determine geographic region (simplified)"""
        try:
            # Use IP geolocation API (would need real implementation)
            # For demo, return placeholder
            return "us-east"  # Would be determined by IP
        except:
            return "unknown"

    def _get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        try:
            # Query external service for public IP
            import urllib.request
            with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                return response.read().decode('utf-8').strip()
        except:
            # Fallback methods
            try:
                # Try different services
                services = ['https://icanhazip.com', 'https://checkip.amazonaws.com']
                for service in services:
                    try:
                        with urllib.request.urlopen(service, timeout=3) as response:
                            return response.read().decode('utf-8').strip()
                    except:
                        continue
            except:
                pass

        return None

    def _discover_peers_bootstrap(self):
        """Connect to dynamically elected bootstrap nodes"""
        bootstrap_peers = self._get_bootstrap_peers_from_blockchain()

        connected_count = 0

        for bootstrap_addr in bootstrap_peers[:5]:  # Try top 5
            try:
                if ':' in bootstrap_addr:
                    host, port_str = bootstrap_addr.split(':', 1)
                    port = int(port_str)
                else:
                    host = bootstrap_addr
                    port = self.listen_port

                self.logger.debug(f"Attempting decentralized bootstrap connection to {host}:{port}")

                # Attempt connection
                threading.Thread(
                    target=self._connect_to_peer,
                    args=(host, port, 'decentralized_bootstrap'),
                    daemon=True
                ).start()

                connected_count += 1

            except Exception as e:
                self.logger.debug(f"Decentralized bootstrap connection to {bootstrap_addr} failed: {e}")

        self.logger.info(f"Initiated {connected_count} decentralized bootstrap connections")

    def _handle_peer_exchange_request(self, peer_id: str, message: Dict):
        """Handle peer exchange request from another peer"""
        try:
            # Send list of known peers (excluding the requesting peer and local addresses)
            known_peers = []
            for pid, peer_info in self.peers.items():
                if pid != peer_id:  # Don't send requester back to themselves
                    address = peer_info.get('address')
                    if address and isinstance(address, tuple) and len(address) >= 2:
                        ip, port = address
                        # Don't share local/private addresses
                        if not (ip.startswith('127.') or ip.startswith('192.168.') or
                               ip.startswith('10.') or ip.startswith('172.')):
                            known_peers.append({
                                'address': ip,
                                'port': port,
                                'peer_id': pid,
                                'last_seen': peer_info.get('last_seen', 0)
                            })

            # Limit to 10 peers to avoid message size issues
            known_peers = known_peers[:10]

            response = {
                'type': 'peer_exchange_response',
                'peers': known_peers,
                'timestamp': time.time()
            }

            self._send_to_peer(peer_id, response)
            self.logger.debug(f"Sent {len(known_peers)} peers to {peer_id}")

        except Exception as e:
            self.logger.error(f"Peer exchange request handling failed for {peer_id}: {e}")

    def _handle_peer_exchange_response(self, peer_id: str, message: Dict):
        """Handle peer exchange response with list of peers"""
        try:
            peers_list = message.get('peers', [])

            discovered_count = 0
            for peer_data in peers_list:
                address = peer_data.get('address')
                port = peer_data.get('port', self.listen_port)
                remote_peer_id = peer_data.get('peer_id')

                # Skip if we already know this peer
                if remote_peer_id in self.peers:
                    continue

                # Attempt to connect to the new peer
                if address and address != self._get_local_ip():
                    threading.Thread(
                        target=self._connect_to_peer,
                        args=(address, port, 'peer_exchange'),
                        daemon=True
                    ).start()
                    discovered_count += 1

            self.logger.info(f"Peer exchange from {peer_id} yielded {discovered_count} new connection attempts")

        except Exception as e:
            self.logger.error(f"Peer exchange response handling failed for {peer_id}: {e}")

    def _handle_peer_messages(self, peer_id: str, sock: socket.socket):
        """Handle messages from connected peer"""
        while self.running and peer_id in self.peer_connections:
            try:
                message = self._receive_message(sock, timeout=1.0)
                if message:
                    self._process_peer_message(peer_id, message)
                else:
                    # Connection closed
                    break

            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Error handling messages from {peer_id}: {e}")
                break

        # Clean up connection
        if peer_id in self.peer_connections:
            del self.peer_connections[peer_id]
        if peer_id in self.peers:
            del self.peers[peer_id]

        try:
            sock.close()
        except:
            pass

        self.logger.info(f"Disconnected from peer {peer_id}")

    def _process_peer_message(self, peer_id: str, message: Dict[str, Any]):
        """Process message from peer"""
        msg_type = message.get('type')

        if msg_type == 'blockchain_sync_request':
            self._handle_blockchain_sync_request(peer_id, message)
        elif msg_type == 'blockchain_sync_response':
            self._handle_blockchain_sync_response(peer_id, message)
        elif msg_type == 'security_event':
            self._handle_security_event(peer_id, message)
        elif msg_type == 'new_block':
            self._handle_new_block(peer_id, message)
        elif msg_type == 'token_transfer_request':
            self._handle_token_transfer_request(peer_id, message)
        elif msg_type == 'token_transfer_response':
            self._handle_token_transfer_response(peer_id, message)
        elif msg_type == 'ping':
            self._handle_ping(peer_id, message)
        elif msg_type == 'peer_exchange_request':
            self._handle_peer_exchange_request(peer_id, message)
        elif msg_type == 'peer_exchange_response':
            self._handle_peer_exchange_response(peer_id, message)
        else:
            self.logger.debug(f"Unknown message type from {peer_id}: {msg_type}")

    def _handle_blockchain_sync_request(self, peer_id: str, message: Dict):
        """Handle blockchain synchronization request"""
        try:
            requested_height = message.get('from_height', 0)

            # Send blockchain data from requested height
            if hasattr(self.local_blockchain, 'chain'):
                blocks_to_send = []
                for i in range(requested_height, len(self.local_blockchain.chain)):
                    blocks_to_send.append(self.local_blockchain.chain[i].to_dict())

                # Send in chunks to avoid message size limits
                chunk_size = 10
                for i in range(0, len(blocks_to_send), chunk_size):
                    chunk = blocks_to_send[i:i + chunk_size]
                    response = {
                        'type': 'blockchain_sync_response',
                        'blocks': chunk,
                        'chunk_index': i // chunk_size,
                        'total_chunks': (len(blocks_to_send) + chunk_size - 1) // chunk_size,
                        'total_blocks': len(blocks_to_send)
                    }
                    self._send_to_peer(peer_id, response)

        except Exception as e:
            self.logger.error(f"Error handling sync request from {peer_id}: {e}")

    def _handle_blockchain_sync_response(self, peer_id: str, message: Dict):
        """Handle blockchain synchronization response"""
        try:
            blocks = message.get('blocks', [])
            chunk_index = message.get('chunk_index', 0)
            total_chunks = message.get('total_chunks', 1)

            # Store chunk for later assembly
            # In a full implementation, this would reassemble chunks
            # and validate/apply the blockchain data

            self.logger.info(f"Received blockchain chunk {chunk_index + 1}/{total_chunks} "
                           f"with {len(blocks)} blocks from {peer_id}")

            if chunk_index == total_chunks - 1:
                self.logger.info(f"Blockchain sync completed from {peer_id}")

        except Exception as e:
            self.logger.error(f"Error handling sync response from {peer_id}: {e}")

    def _handle_security_event(self, peer_id: str, message: Dict):
        """Handle security event from peer"""
        try:
            event = message.get('event', {})
            signature = message.get('signature')

            # Verify event signature
            if not self._verify_event_signature(event, signature, peer_id):
                self.logger.warning(f"Invalid security event signature from {peer_id}")
                return

            # Process security event
            event_type = event.get('type')

            # Add to local security awareness
            self._process_shared_security_event(peer_id, event)

            # Optionally add to local blockchain
            if event_type in ['critical_alert', 'attack_detected', 'system_compromise']:
                self.local_blockchain.add_transaction({
                    'type': 'shared_security_event',
                    'source_peer': peer_id,
                    'event': event,
                    'received_at': time.time(),
                    'verification_status': 'verified'
                })

            self.logger.info(f"Processed security event from {peer_id}: {event_type}")

        except Exception as e:
            self.logger.error(f"Error handling security event from {peer_id}: {e}")

    def _handle_new_block(self, peer_id: str, message: Dict):
        """Handle new block announcement from peer"""
        try:
            block_data = message.get('block')

            # Validate block
            if self._validate_received_block(block_data):
                # Check if we should accept this block
                # (In a real implementation, this would be more complex)
                self.logger.info(f"Received valid block from {peer_id}")
            else:
                self.logger.warning(f"Received invalid block from {peer_id}")

        except Exception as e:
            self.logger.error(f"Error handling new block from {peer_id}: {e}")

    def _handle_ping(self, peer_id: str, message: Dict):
        """Handle ping message from peer"""
        # Update peer last seen time
        if peer_id in self.peers:
            self.peers[peer_id]['last_seen'] = time.time()

        # Send pong response
        self._send_to_peer(peer_id, {'type': 'pong', 'timestamp': time.time()})

    def _process_shared_security_event(self, peer_id: str, event: Dict):
        """Process security event shared by peer"""
        event_type = event.get('type')

        # Update local security awareness based on event type
        if event_type == 'attack_detected':
            self._handle_attack_intelligence(peer_id, event)
        elif event_type == 'system_compromise':
            self._handle_compromise_alert(peer_id, event)
        elif event_type == 'critical_alert':
            self._handle_critical_alert(peer_id, event)

        # Log shared event
        self.logger.info(f"Security event from {peer_id}: {event_type} - {event.get('description', '')}")

    def _handle_attack_intelligence(self, peer_id: str, event: Dict):
        """Handle attack intelligence from peer"""
        attack_pattern = event.get('attack_pattern')
        affected_systems = event.get('affected_systems', [])

        # Update local threat intelligence
        # In a real implementation, this would update local security rules
        self.logger.warning(f"Attack pattern shared by {peer_id}: {attack_pattern}")

    def _handle_compromise_alert(self, peer_id: str, event: Dict):
        """Handle system compromise alert from peer"""
        compromised_system = event.get('compromised_system')

        # Increase local security monitoring
        self.logger.critical(f"System compromise alert from {peer_id}: {compromised_system}")

        # Could trigger local security responses
        self._trigger_security_response('peer_compromise_detected', {
            'source_peer': peer_id,
            'compromised_system': compromised_system
        })

    def _handle_critical_alert(self, peer_id: str, event: Dict):
        """Handle critical security alert from peer"""
        alert_details = event.get('details')

        self.logger.critical(f"Critical alert from {peer_id}: {alert_details}")

    def _handle_token_transfer_request(self, peer_id: str, message: Dict):
        """Handle token transfer request from peer"""
        try:
            transfer_data = message.get('transfer_data', {})
            transfer_id = transfer_data.get('transfer_id')

            # Validate transfer request
            if not self._validate_transfer_request(transfer_data):
                self._send_to_peer(peer_id, {
                    'type': 'token_transfer_response',
                    'transfer_id': transfer_id,
                    'accepted': False,
                    'reason': 'validation_failed'
                })
                return

            # Check if we're the intended recipient
            recipient_wallet = transfer_data.get('recipient_wallet')
            if recipient_wallet != self._get_local_wallet_id():
                self._send_to_peer(peer_id, {
                    'type': 'token_transfer_response',
                    'transfer_id': transfer_id,
                    'accepted': False,
                    'reason': 'wrong_recipient'
                })
                return

            # Accept the transfer
            if self._process_incoming_transfer(transfer_data):
                self._send_to_peer(peer_id, {
                    'type': 'token_transfer_response',
                    'transfer_id': transfer_id,
                    'accepted': True,
                    'recipient_wallet': recipient_wallet
                })
                self.logger.info(f"Accepted token transfer {transfer_id} from {peer_id}")
            else:
                self._send_to_peer(peer_id, {
                    'type': 'token_transfer_response',
                    'transfer_id': transfer_id,
                    'accepted': False,
                    'reason': 'processing_failed'
                })

        except Exception as e:
            self.logger.error(f"Error handling token transfer request from {peer_id}: {e}")

    def _handle_token_transfer_response(self, peer_id: str, message: Dict):
        """Handle token transfer response from peer"""
        try:
            transfer_id = message.get('transfer_id')
            accepted = message.get('accepted', False)

            if accepted:
                self.logger.info(f"Token transfer {transfer_id} accepted by {peer_id}")
                # Update local transfer status
                self._update_transfer_status(transfer_id, 'completed')
            else:
                reason = message.get('reason', 'unknown')
                self.logger.warning(f"Token transfer {transfer_id} rejected by {peer_id}: {reason}")
                # Update local transfer status
                self._update_transfer_status(transfer_id, 'failed', reason)

        except Exception as e:
            self.logger.error(f"Error handling token transfer response from {peer_id}: {e}")

    def _validate_transfer_request(self, transfer_data: Dict) -> bool:
        """Validate incoming token transfer request"""
        try:
            required_fields = ['transfer_id', 'sender_wallet', 'recipient_wallet',
                             'tokens', 'timestamp', 'signature']
            for field in required_fields:
                if field not in transfer_data:
                    return False

            # Check timestamp (not too old)
            if time.time() - transfer_data['timestamp'] > 3600:  # 1 hour
                return False

            # Validate signature
            expected_signature = self._sign_transfer_data(transfer_data)
            if transfer_data['signature'] != expected_signature:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Transfer validation error: {e}")
            return False

    def _process_incoming_transfer(self, transfer_data: Dict) -> bool:
        """Process and accept an incoming token transfer"""
        try:
            # Use local wallet to receive the transfer
            from bc_security.blockchain_security import SignWallet
            local_blockchain = self.local_blockchain  # This should be passed in constructor
            wallet = SignWallet(blockchain=local_blockchain)

            return wallet.receive_transfer(transfer_data, local_blockchain)

        except Exception as e:
            self.logger.error(f"Failed to process incoming transfer: {e}")
            return False

    def _get_local_wallet_id(self) -> str:
        """Get local wallet ID"""
        try:
            from blockchain_security import SignWallet
            wallet = SignWallet()
            return wallet.wallet_data['wallet_id']
        except:
            return 'unknown'

    def _sign_transfer_data(self, transfer_data: Dict) -> str:
        """Sign transfer data (simplified)"""
        transfer_string = json.dumps({
            'transfer_id': transfer_data['transfer_id'],
            'sender_wallet': transfer_data['sender_wallet'],
            'recipient_wallet': transfer_data['recipient_wallet'],
            'token_ids': [t['token_id'] for t in transfer_data['tokens']],
            'timestamp': transfer_data['timestamp']
        }, sort_keys=True)

        return hashlib.sha256(transfer_string.encode()).hexdigest()

    def _update_transfer_status(self, transfer_id: str, status: str, reason: str = None):
        """Update local transfer status"""
        try:
            from blockchain_security import SignWallet
            wallet = SignWallet()

            transfers = wallet.get_transfer_history()
            for transfer in transfers:
                if transfer.get('transfer_id') == transfer_id:
                    transfer['status'] = status
                    if reason:
                        transfer['failure_reason'] = reason
                    wallet.save_wallet()
                    break

        except Exception as e:
            self.logger.error(f"Failed to update transfer status: {e}")

    def request_token_transfer(self, recipient_wallet_id: str, token_ids: List[str]) -> Dict[str, Any]:
        """Request token transfer to a peer"""
        try:
            # Get local wallet
            from blockchain_security import SignWallet
            local_blockchain = self.local_blockchain
            wallet = SignWallet(blockchain=local_blockchain)

            # Find peer that has the recipient wallet
            recipient_peer = None
            for peer_id, peer_info in self.peers.items():
                if peer_info.get('wallet_id') == recipient_wallet_id:
                    recipient_peer = peer_id
                    break

            if not recipient_peer:
                return {
                    'success': False,
                    'error': 'Recipient peer not found in network'
                }

            # Initiate transfer through wallet
            transfer_result = wallet.transfer_tokens(recipient_wallet_id, token_ids, local_blockchain)

            if transfer_result['success']:
                # Send transfer request to peer
                transfer_request = {
                    'type': 'token_transfer_request',
                    'transfer_data': {
                        'transfer_id': transfer_result['transfer_id'],
                        'sender_wallet': wallet.wallet_data['wallet_id'],
                        'recipient_wallet': recipient_wallet_id,
                        'tokens': transfer_result.get('tokens_data', []),
                        'timestamp': time.time(),
                        'signature': transfer_result.get('signature', '')
                    }
                }

                self._send_to_peer(recipient_peer, transfer_request)
                self.logger.info(f"Token transfer request sent to {recipient_peer}")

            return transfer_result

        except Exception as e:
            self.logger.error(f"Token transfer request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def share_security_event(self, event: Dict[str, Any]):
        """Share security event with all connected peers"""
        # Determine if event should be shared
        if not self._should_share_event(event):
            return

        # Sign the event
        event_signature = self._sign_event(event)

        message = {
            'type': 'security_event',
            'event': event,
            'signature': event_signature,
            'sender_peer_id': self._generate_peer_id(),
            'timestamp': time.time()
        }

        # Send to all connected peers
        for peer_id in list(self.peer_connections.keys()):
            try:
                self._send_to_peer(peer_id, message)
            except Exception as e:
                self.logger.error(f"Failed to share event with {peer_id}: {e}")

    def request_blockchain_sync(self, peer_id: str, from_height: int = 0):
        """Request blockchain synchronization from peer"""
        message = {
            'type': 'blockchain_sync_request',
            'from_height': from_height,
            'timestamp': time.time()
        }

        self._send_to_peer(peer_id, message)
        self.logger.info(f"Requested blockchain sync from {peer_id} starting at height {from_height}")

    def broadcast_new_block(self, block_data: Dict):
        """Broadcast new block to all connected peers"""
        message = {
            'type': 'new_block',
            'block': block_data,
            'timestamp': time.time()
        }

        for peer_id in list(self.peer_connections.keys()):
            try:
                self._send_to_peer(peer_id, message)
            except Exception as e:
                self.logger.error(f"Failed to broadcast block to {peer_id}: {e}")

    def _heartbeat_monitor(self):
        """Monitor peer heartbeats and connection health"""
        while self.running:
            try:
                current_time = time.time()

                # Check each peer
                peers_to_remove = []
                for peer_id, peer_info in self.peers.items():
                    last_seen = peer_info.get('last_seen', 0)

                    # Send ping if we haven't heard from peer recently
                    if current_time - last_seen > self.heartbeat_interval:
                        try:
                            self._send_to_peer(peer_id, {'type': 'ping', 'timestamp': current_time})
                        except Exception as e:
                            self.logger.debug(f"Failed to ping {peer_id}: {e}")
                            peers_to_remove.append(peer_id)

                    # Remove peers we haven't heard from in too long
                    if current_time - last_seen > self.heartbeat_interval * 3:
                        peers_to_remove.append(peer_id)

                # Clean up dead connections
                for peer_id in peers_to_remove:
                    if peer_id in self.peer_connections:
                        try:
                            self.peer_connections[peer_id].close()
                        except:
                            pass
                        del self.peer_connections[peer_id]
                    if peer_id in self.peers:
                        del self.peers[peer_id]
                    self.logger.info(f"Removed unresponsive peer: {peer_id}")

            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {e}")

            time.sleep(self.heartbeat_interval)

    def _blockchain_sync(self):
        """Periodic blockchain synchronization with peers"""
        while self.running:
            try:
                # Sync with a random peer
                if self.peer_connections:
                    peer_ids = list(self.peer_connections.keys())
                    random_peer = secrets.choice(peer_ids)

                    # Request sync from current height
                    local_height = len(self.local_blockchain.chain) if hasattr(self.local_blockchain, 'chain') else 0
                    self.request_blockchain_sync(random_peer, local_height)

            except Exception as e:
                self.logger.error(f"Blockchain sync error: {e}")

            time.sleep(self.sync_interval)

    def _send_to_peer(self, peer_id: str, message: Dict[str, Any]):
        """Send message to specific peer"""
        if peer_id in self.peer_connections:
            self._send_message(self.peer_connections[peer_id], message)

    def _send_message(self, sock: socket.socket, message: Dict[str, Any]):
        """Send JSON message over socket"""
        try:
            data = json.dumps(message).encode('utf-8')
            # Send message length first (4 bytes)
            length = len(data).to_bytes(4, byteorder='big')
            sock.send(length + data)
        except Exception as e:
            raise e

    def _receive_message(self, sock: socket.socket, timeout: float = 1.0) -> Optional[Dict]:
        """Receive JSON message from socket"""
        try:
            sock.settimeout(timeout)

            # Read message length (4 bytes)
            length_bytes = sock.recv(4)
            if len(length_bytes) != 4:
                return None

            length = int.from_bytes(length_bytes, byteorder='big')

            # Read message data
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    return None
                data += chunk

            return json.loads(data.decode('utf-8'))

        except socket.timeout:
            return None
        except Exception as e:
            raise e

    def _verify_event_signature(self, event: Dict, signature: str, peer_id: str) -> bool:
        """Verify security event signature"""
        try:
            # Get peer's public key (would be stored in trusted peer registry)
            peer_public_key = self._get_peer_public_key(peer_id)
            if not peer_public_key:
                return False

            # Create signature verification (simplified)
            # In real implementation, would use proper cryptographic verification
            event_string = json.dumps(event, sort_keys=True)
            expected_hash = hashlib.sha256(event_string.encode()).hexdigest()

            return signature == expected_hash  # Simplified for demo

        except Exception as e:
            self.logger.error(f"Event signature verification failed: {e}")
            return False

    def _validate_received_block(self, block_data: Dict) -> bool:
        """Validate received block from peer"""
        try:
            # Basic validation checks
            required_fields = ['index', 'hash', 'previous_hash', 'transactions']
            for field in required_fields:
                if field not in block_data:
                    return False

            # Validate hash
            # (In real implementation, would recalculate and verify)

            # Validate transactions
            transactions = block_data.get('transactions', [])
            if not isinstance(transactions, list):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Block validation error: {e}")
            return False

    def _get_peer_public_key(self, peer_id: str) -> Optional[str]:
        """Get peer's public key for signature verification"""
        # In real implementation, this would retrieve from trusted peer registry
        # For demo, return a placeholder
        return "placeholder-public-key"

    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    def _is_version_compatible(self, version: str) -> bool:
        """Check if peer version is compatible"""
        # Simple version compatibility check
        try:
            peer_major, peer_minor = version.split('.')[:2]
            local_major, local_minor = "1.0.2.77".split('.')[:2]

            return peer_major == local_major
        except:
            return False

    def _should_share_event(self, event: Dict) -> bool:
        """Determine if security event should be shared"""
        event_type = event.get('type', '')

        # Share critical security events
        shareable_events = [
            'attack_detected',
            'system_compromise',
            'critical_alert',
            'intrusion_attempt',
            'malware_detected'
        ]

        return event_type in shareable_events

    def _sign_event(self, event: Dict) -> str:
        """Sign security event (simplified)"""
        event_string = json.dumps(event, sort_keys=True)
        return hashlib.sha256(event_string.encode()).hexdigest()

    def _trigger_security_response(self, response_type: str, details: Dict):
        """Trigger local security response to shared events"""
        self.logger.warning(f"Security response triggered: {response_type} - {details}")

        # In real implementation, this could:
        # - Increase monitoring
        # - Block suspicious IPs
        # - Alert administrators
        # - Quarantine systems

    def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status"""
        return {
            'connected_peers': len(self.peer_connections),
            'total_known_peers': len(self.peers),
            'trusted_peers': list(self.trusted_peers),
            'listening_port': self.listen_port,
            'running': self.running,
            'peer_details': {
                peer_id: {
                    'address': info.get('address'),
                    'connected_at': info.get('connected_at'),
                    'last_seen': info.get('last_seen'),
                    'version': info.get('version')
                }
                for peer_id, info in self.peers.items()
            }
        }

def main():
    """CLI interface for P2P blockchain network"""
    import argparse

    parser = argparse.ArgumentParser(description='314Sign P2P Blockchain Network')
    parser.add_argument('--status', action='store_true', help='Show network status')
    parser.add_argument('--start', action='store_true', help='Start P2P network')
    parser.add_argument('--stop', action='store_true', help='Stop P2P network')
    parser.add_argument('--discover-peers', action='store_true', help='Discover available peers')
    parser.add_argument('--share-event', metavar='EVENT_TYPE', help='Share security event')
    parser.add_argument('--connect-peer', nargs=2, metavar=('HOST', 'PORT'), help='Connect to specific peer')
    parser.add_argument('--trusted-peers', nargs='+', help='Set trusted peer IDs')

    args = parser.parse_args()

    # Create mock blockchain for demo
    class MockBlockchain:
        def __init__(self):
            self.chain = []
        def add_transaction(self, tx):
            return f"tx_{len(self.chain)}"

    blockchain = MockBlockchain()

    # Network configuration
    network_config = {
        'listen_port': 31450,
        'max_peers': 5,
        'heartbeat_interval': 30,
        'sync_interval': 60,
        'trusted_peers': args.trusted_peers or [],
        'network_secret': '314sign-p2p-secret'
    }

    # Create P2P network
    network = P2PBlockchainNetwork(blockchain, network_config)

    if args.status:
        status = network.get_network_status()
        print("314Sign P2P Network Status:")
        print(f"  Running: {status['running']}")
        print(f"  Connected Peers: {status['connected_peers']}")
        print(f"  Known Peers: {status['total_known_peers']}")
        print(f"  Trusted Peers: {status['trusted_peers']}")
        print(f"  Listening Port: {status['listening_port']}")

        if status['peer_details']:
            print("\nConnected Peers:")
            for peer_id, details in status['peer_details'].items():
                print(f"  {peer_id[:12]}...: {details['address']} (v{details['version']})")

    elif args.start:
        network.start()
        print("P2P network started. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping P2P network...")
            network.stop()

    elif args.stop:
        network.stop()
        print("P2P network stopped.")

    elif args.discover_peers:
        network._discover_peers()
        print("Peer discovery initiated.")

    elif args.share_event:
        event = {
            'type': args.share_event,
            'description': f'Shared {args.share_event} event',
            'timestamp': time.time(),
            'source': 'local-kiosk'
        }
        network.share_security_event(event)
        print(f"Shared security event: {args.share_event}")

    elif args.connect_peer:
        host, port = args.connect_peer
        network._connect_to_peer(host, int(port))
        print(f"Attempting to connect to peer at {host}:{port}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()