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
                test_socket.bind(('0.0.0.0', port))
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
            # Generate random port for client
            self.assigned_client_port = self.generate_random_port()
            
            # Create server socket for client connections
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.assigned_client_port))
            self.server_socket.listen(5)
            
            print(f"Server started on port {self.share_port}")
            print(f"Client should connect to port: {self.assigned_client_port}")
            print(f"Server listening on 0.0.0.0:{self.assigned_client_port} for tunnel client")
            print("Waiting for client connections...")
            print("Press Ctrl+C to stop the server")
            
            self.running = True
            
            # Wait for tunnel client connection first
            tunnel_client_socket, tunnel_client_address = self.server_socket.accept()
            print(f"Tunnel client connected from {tunnel_client_address}")
            
            # Now start listening on share_port for user connections
            share_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            share_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            share_socket.bind(('0.0.0.0', self.share_port))
            share_socket.listen(5)
            
            print(f"Now accepting user connections on port {self.share_port}")
            
            while self.running:
                try:
                    user_socket, user_address = share_socket.accept()
                    print(f"User connected from {user_address}")
                    
                    # Forward traffic between user and tunnel client
                    self.forward_traffic(user_socket, tunnel_client_socket)
                    
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
    
    def forward_traffic(self, user_socket: socket.socket, client_socket: socket.socket):
        """Forward traffic between user and client"""
        def forward_data(source: socket.socket, destination: socket.socket, direction: str):
            try:
                while self.running:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
                    print(f"Forwarded {len(data)} bytes {direction}")
            except Exception as e:
                print(f"Error forwarding {direction}: {e}")
            finally:
                try:
                    source.close()
                    destination.close()
                except:
                    pass
        
        # Start bidirectional forwarding threads
        user_to_client = threading.Thread(
            target=forward_data,
            args=(user_socket, client_socket, "user->client")
        )
        client_to_user = threading.Thread(
            target=forward_data,
            args=(client_socket, user_socket, "client->user")
        )
        
        user_to_client.daemon = True
        client_to_user.daemon = True
        
        user_to_client.start()
        client_to_user.start()
        
        # Wait for threads to complete
        user_to_client.join()
        client_to_user.join()
        
        print("Traffic forwarding stopped")
    
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
