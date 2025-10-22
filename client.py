#!/usr/bin/env python3
"""
CT Client - TCP tunnel client
Connects to server and forwards traffic between local and remote ports
"""

import argparse
import socket
import threading
import sys
import time
from typing import Optional


class CTClient:
    def __init__(self, serv_ip: str, serv_port: int, local_port: int):
        self.serv_ip = serv_ip
        self.serv_port = serv_port
        self.local_port = local_port
        self.running = False
        
    def start_client(self):
        """Start the client and establish persistent connection to server"""
        try:
            print(f"Client connecting to server {self.serv_ip}:{self.serv_port}")
            print(f"Will forward traffic to local port {self.local_port}")
            print("Press Ctrl+C to stop the client")
            
            self.running = True
            
            # Connect to server once
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.serv_ip, self.serv_port))
            print(f"Connected to server {self.serv_ip}:{self.serv_port}")
            
            while self.running:
                try:
                    # Connect to local application for each user request
                    local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    local_socket.connect(('localhost', self.local_port))
                    print(f"Connected to local application on port {self.local_port}")
                    
                    # Start bidirectional forwarding
                    self.forward_traffic(local_socket, server_socket)
                    
                except socket.error as e:
                    if self.running:
                        print(f"Local connection error: {e}")
                        time.sleep(1)  # Wait before retrying
                    break
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            print("\nShutting down client...")
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.stop_client()
    
    def forward_traffic(self, local_socket: socket.socket, remote_socket: socket.socket):
        """Forward traffic between local and remote sockets"""
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
        local_to_remote = threading.Thread(
            target=forward_data,
            args=(local_socket, remote_socket, "local->remote")
        )
        remote_to_local = threading.Thread(
            target=forward_data,
            args=(remote_socket, local_socket, "remote->local")
        )
        
        local_to_remote.daemon = True
        remote_to_local.daemon = True
        
        local_to_remote.start()
        remote_to_local.start()
        
        # Wait for threads to complete
        local_to_remote.join()
        remote_to_local.join()
        
        print("Traffic forwarding stopped")
    
    def stop_client(self):
        """Stop the client and cleanup"""
        self.running = False
        print("Client stopped")


def main():
    parser = argparse.ArgumentParser(
        description="CT Client - TCP tunnel client for port forwarding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python client.py --serv-ip 192.168.1.100 --serv-port 8080 --local-port 3000
  python client.py -si localhost -sp 9000 -lp 5000
        """
    )
    
    parser.add_argument(
        '--serv-ip', '-si',
        type=str,
        default='localhost',
        help='Server IP address to connect to (default: localhost)'
    )
    
    parser.add_argument(
        '--serv-port', '-sp',
        type=int,
        required=True,
        help='Server port to connect to (assigned by server)'
    )
    
    parser.add_argument(
        '--local-port', '-lp',
        type=int,
        required=True,
        help='Local port to listen on for incoming connections'
    )
    
    args = parser.parse_args()
    
    # Validate ports
    if args.serv_port < 1 or args.serv_port > 65535:
        print("Error: serv-port must be between 1 and 65535")
        sys.exit(1)
        
    if args.local_port < 1 or args.local_port > 65535:
        print("Error: local-port must be between 1 and 65535")
        sys.exit(1)
    
    # Create and start client
    client = CTClient(args.serv_ip, args.serv_port, args.local_port)
    
    try:
        client.start_client()
    except KeyboardInterrupt:
        print("\nClient interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
