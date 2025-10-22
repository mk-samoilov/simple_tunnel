#!/usr/bin/env python3
"""
Easy Tunnel Server
A TCP tunnel server that forwards traffic between clients and target services.
"""

import argparse
import socket
import threading
import random
import sys
import time
from typing import Optional, Tuple


class TunnelServer:
    def __init__(self, share_port: int):
        self.share_port = share_port
        self.client_port = None
        self.server_socket = None
        self.running = False
        
    def find_free_port(self, start_port: int = 1000, max_port: int = 10000) -> int:
        """Find a free port in the specified range."""
        for _ in range(100):  # Try up to 100 times
            port = random.randint(start_port, max_port)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                    test_sock.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("Could not find a free port in the specified range")
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                test_sock.bind(('0.0.0.0', port))
                return True
        except OSError:
            return False
    
    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle individual client connection."""
        print(f"[INFO] Client connected from {client_address}")
        
        try:
            # Connect to the target service on share_port
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect(('127.0.0.1', self.share_port))
            
            # Create bidirectional forwarding
            def forward_data(source: socket.socket, destination: socket.socket):
                try:
                    while True:
                        data = source.recv(4096)
                        if not data:
                            break
                        destination.send(data)
                except (ConnectionResetError, ConnectionAbortedError, OSError):
                    pass
                finally:
                    try:
                        source.close()
                        destination.close()
                    except:
                        pass
            
            # Start forwarding threads
            client_to_target = threading.Thread(
                target=forward_data, 
                args=(client_socket, target_socket),
                daemon=True
            )
            target_to_client = threading.Thread(
                target=forward_data, 
                args=(target_socket, client_socket),
                daemon=True
            )
            
            client_to_target.start()
            target_to_client.start()
            
            # Wait for either thread to finish
            client_to_target.join()
            target_to_client.join()
            
        except Exception as e:
            print(f"[ERROR] Error handling client {client_address}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            print(f"[INFO] Client {client_address} disconnected")
    
    def start(self):
        """Start the tunnel server."""
        # Check if share_port is available
        if not self.is_port_available(self.share_port):
            print(f"[ERROR] Port {self.share_port} is already in use or not available")
            return False
        
        # Find a free port for client connections
        try:
            self.client_port = self.find_free_port()
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            return False
        
        # Create server socket for client connections
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.client_port))
            self.server_socket.listen(5)
        except OSError as e:
            print(f"[ERROR] Failed to bind to port {self.client_port}: {e}")
            return False
        
        self.running = True
        print(f"[INFO] Tunnel server started")
        print(f"[INFO] Share port: {self.share_port}")
        print(f"[INFO] Client connection port: {self.client_port}")
        print(f"[INFO] Server listening on 0.0.0.0:{self.client_port}")
        print(f"[INFO] Use: client.py --remote-port {self.client_port} --local-port <your_local_port>")
        
        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                except OSError:
                    if self.running:
                        print("[ERROR] Error accepting client connection")
                    break
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down server...")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the tunnel server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("[INFO] Server stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Easy Tunnel Server - TCP tunnel server for forwarding traffic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --share-port 8080
  %(prog)s -sp 3000

The server will:
1. Check if the specified share-port is available
2. Start listening for client connections on a random free port
3. Forward traffic between clients and the service on share-port
        """
    )
    
    parser.add_argument(
        '--share-port', '-sp',
        type=int,
        required=True,
        help='Port number of the target service to tunnel to (required)'
    )
    
    args = parser.parse_args()
    
    # Validate share port
    if args.share_port < 1 or args.share_port > 65535:
        print("[ERROR] Share port must be between 1 and 65535")
        sys.exit(1)
    
    # Create and start server
    server = TunnelServer(args.share_port)
    
    try:
        success = server.start()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Server interrupted by user")
        server.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
