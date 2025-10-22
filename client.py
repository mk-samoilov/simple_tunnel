#!/usr/bin/env python3
"""
Easy Tunnel Client
A TCP tunnel client that connects to the tunnel server and forwards local traffic.
"""

import argparse
import socket
import threading
import sys
import time
from typing import Optional


class TunnelClient:
    def __init__(self, remote_ip: str, remote_port: int, target_host: str, target_port: int, local_port: int):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.target_host = target_host
        self.target_port = target_port
        self.local_port = local_port
        self.running = False

    def forward_data(self, source: socket.socket, destination: socket.socket, direction: str):
        """Forward data between two sockets."""
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.send(data)
                print(f"[DEBUG] Forwarded {len(data)} bytes {direction}")
        except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
            print(f"[DEBUG] Connection closed in {direction}: {e}")
        finally:
            try:
                source.close()
            except:
                pass
            try:
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
            print(f"[INFO] Connected to tunnel server {self.remote_ip}:{self.remote_port}")

            # Send target information to server
            target_info = f"{self.target_host}:{self.target_port}"
            remote_socket.send(target_info.encode())

            # Wait for server response
            response = remote_socket.recv(1024)
            if response != b"OK":
                print(f"[ERROR] Server failed to connect to target: {response}")
                return

            print(f"[INFO] Tunnel established to {self.target_host}:{self.target_port}")

            # Create bidirectional forwarding
            local_to_remote = threading.Thread(
                target=self.forward_data,
                args=(local_socket, remote_socket, "local->remote"),
                daemon=True
            )
            remote_to_local = threading.Thread(
                target=self.forward_data,
                args=(remote_socket, local_socket, "remote->local"),
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
        print(f"[INFO] Listening locally on 127.0.0.1:{self.local_port}")
        print(f"[INFO] Remote server: {self.remote_ip}:{self.remote_port}")
        print(f"[INFO] Target application: {self.target_host}:{self.target_port}")
        print(
            f"[INFO] Local connections to 127.0.0.1:{self.local_port} will be tunneled to {self.target_host}:{self.target_port}")

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
  %(prog)s --remote-ip 192.168.1.100 --remote-port 5432 --target-host 127.0.0.1 --target-port 5000 --local-port 8080
  %(prog)s -ri 127.0.0.1 -rp 5432 -th 127.0.0.1 -tp 5000 -lp 3000

Data flow:
1. Local app connects to 127.0.0.1:local-port
2. Client connects to tunnel server and specifies target application
3. Server connects to target application
4. Data flows: local-app <-> client <-> server <-> target-app
        """
    )

    parser.add_argument(
        '--remote-ip', '-ri',
        type=str,
        required=True,
        help='IP address of the tunnel server (required)'
    )

    parser.add_argument(
        '--remote-port', '-rp',
        type=int,
        required=True,
        help='Port number of the tunnel server (required)'
    )

    parser.add_argument(
        '--target-host', '-th',
        type=str,
        default='127.0.0.1',
        help='Host of the target application (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--target-port', '-tp',
        type=int,
        required=True,
        help='Port number of the target application (required)'
    )

    parser.add_argument(
        '--local-port', '-lp',
        type=int,
        required=True,
        help='Local port to listen on for incoming connections (required)'
    )

    args = parser.parse_args()

    # Validate ports
    for port in [args.remote_port, args.target_port, args.local_port]:
        if port < 1 or port > 65535:
            print(f"[ERROR] Port must be between 1 and 65535")
            sys.exit(1)

    # Create and start client
    client = TunnelClient(args.remote_ip, args.remote_port, args.target_host, args.target_port, args.local_port)

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
