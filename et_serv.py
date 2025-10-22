#!/usr/bin/env python3
"""
ET Server - TCP tunnel server
Provides port sharing functionality with client port assignment
"""

import argparse
import socket
import threading
import random
import sys
import time
from typing import Optional


class ETServer:
    def __init__(self, share_port: int):
        self.share_port = share_port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.assigned_client_port = None
        
    def check_port_availability(self, port: int) -> bool:
        """Check if port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_socket.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def generate_random_port(self) -> int:
        """Generate random port number up to 10000"""
        max_attempts = 100
        for _ in range(max_attempts):
            port = random.randint(1024, 10000)
            if self.check_port_availability(port):
                return port
        raise RuntimeError("Could not find available port after 100 attempts")
    
    def start_server(self):
        """Start the TCP server on share_port"""
        if not self.check_port_availability(self.share_port):
            print(f"Error: Port {self.share_port} is already in use")
            sys.exit(1)
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.share_port))
            self.server_socket.listen(5)
            
            # Generate random port for client
            self.assigned_client_port = self.generate_random_port()
            
            print(f"Server started on port {self.share_port}")
            print(f"Client should connect to port: {self.assigned_client_port}")
            print("Waiting for connections...")
            print("Press Ctrl+C to stop the server")
            
            self.running = True
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"Connection established with {address}")
                    
                    # Handle client connection in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        print(f"Socket error: {e}")
                    break
                    
        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        try:
            # Simple echo server for demonstration
            # In real implementation, this would handle port forwarding
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received from {address}: {data.decode('utf-8', errors='ignore')}")
                client_socket.send(data)  # Echo back
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection with {address} closed")
    
    def stop_server(self):
        """Stop the server and cleanup"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("Server stopped")


def main():
    parser = argparse.ArgumentParser(
        description="ET Server - TCP tunnel server with port sharing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python et_serv.py --share-port 8080
  python et_serv.py -sp 3000
        """
    )
    
    parser.add_argument(
        '--share-port', '-sp',
        type=int,
        required=True,
        help='Port to share (server will listen on this port)'
    )
    
    args = parser.parse_args()
    
    # Validate ports
    if args.share_port < 1 or args.share_port > 65535:
        print("Error: share-port must be between 1 and 65535")
        sys.exit(1)
    
    # Create and start server
    server = ETServer(args.share_port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
