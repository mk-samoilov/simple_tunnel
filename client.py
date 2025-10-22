#!/usr/bin/env python3
"""
Easy Tunnel Client
A TCP tunnel client that connects to the tunnel server and forwards local traffic.
"""

import argparse
import socket
import threading
import sys
from typing import Optional


class TunnelClient:
    def __init__(self, remote_ip: str, remote_port: int, local_port: int):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.local_port = local_port
        self.running = False
        
    def forward_data(self, source: socket.socket, destination: socket.socket):
        """Forward data between two sockets."""
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
    
    def handle_local_connection(self, local_socket: socket.socket, local_address):
        """Handle connection from local application."""
        print(f"[INFO] Local connection from {local_address}")
        
        try:
            # Connect to tunnel server
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((self.remote_ip, self.remote_port))
            
            # Create bidirectional forwarding
            local_to_remote = threading.Thread(
                target=self.forward_data,
                args=(local_socket, remote_socket),
                daemon=True
            )
            remote_to_local = threading.Thread(
                target=self.forward_data,
                args=(remote_socket, local_socket),
                daemon=True
            )
            
            local_to_remote.start()
            remote_to_local.start()
            
            # Wait for either thread to finish
            local_to_remote.join()
            remote_to_local.join()
            
        except Exception as e:
            print(f"[ERROR] Error handling local connection {local_address}: {e}")
        finally:
            try:
                local_socket.close()
            except:
                pass
            print(f"[INFO] Local connection {local_address} closed")
    
    def start(self):
        """Start the tunnel client."""
        # Create local server socket
        try:
            local_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            local_server.bind(('127.0.0.1', self.local_port))
            local_server.listen(5)
        except OSError as e:
            print(f"[ERROR] Failed to bind to local port {self.local_port}: {e}")
            return False
        
        self.running = True
        print(f"[INFO] Tunnel client started")
        print(f"[INFO] Local port: {self.local_port}")
        print(f"[INFO] Remote server: {self.remote_ip}:{self.remote_port}")
        print(f"[INFO] Client listening on 127.0.0.1:{self.local_port}")
        
        try:
            while self.running:
                try:
                    local_socket, local_address = local_server.accept()
                    # Handle each local connection in a separate thread
                    connection_thread = threading.Thread(
                        target=self.handle_local_connection,
                        args=(local_socket, local_address),
                        daemon=True
                    )
                    connection_thread.start()
                except OSError:
                    if self.running:
                        print("[ERROR] Error accepting local connection")
                    break
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down client...")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the tunnel client."""
        self.running = False
        print("[INFO] Client stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Easy Tunnel Client - TCP tunnel client for connecting to tunnel server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --remote-ip 192.168.1.100 --remote-port 5432 --local-port 8080
  %(prog)s -ri 127.0.0.1 -rp 5432 -lp 3000

The client will:
1. Listen on the specified local-port for incoming connections
2. Forward all traffic to the tunnel server on remote-port
3. Forward responses back to the local application
        """
    )
    
    parser.add_argument(
        '--remote-ip', '-ri',
        type=str,
        default='127.0.0.1',
        help='IP address of the tunnel server (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--remote-port', '-rp',
        type=int,
        required=True,
        help='Port number of the tunnel server (required)'
    )
    
    parser.add_argument(
        '--local-port', '-lp',
        type=int,
        required=True,
        help='Local port to listen on for incoming connections (required)'
    )
    
    args = parser.parse_args()
    
    # Validate ports
    if args.remote_port < 1 or args.remote_port > 65535:
        print("[ERROR] Remote port must be between 1 and 65535")
        sys.exit(1)
    
    if args.local_port < 1 or args.local_port > 65535:
        print("[ERROR] Local port must be between 1 and 65535")
        sys.exit(1)
    
    # Create and start client
    client = TunnelClient(args.remote_ip, args.remote_port, args.local_port)
    
    try:
        success = client.start()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Client interrupted by user")
        client.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
