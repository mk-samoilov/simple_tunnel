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
    def __init__(self, client_port: int):
        self.client_port = client_port
        self.server_socket = None
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

    def handle_client_connection(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle connection from tunnel client."""
        print(f"[INFO] Tunnel client connected from {client_address}")

        try:
            # Wait for target connection info from client
            data = client_socket.recv(1024)
            if not data:
                return

            # Parse target info (format: "TARGET_HOST:TARGET_PORT")
            target_info = data.decode().strip()
            if ':' not in target_info:
                print(f"[ERROR] Invalid target info from client: {target_info}")
                return

            target_host, target_port = target_info.split(':', 1)
            target_port = int(target_port)

            print(f"[INFO] Client wants to connect to {target_host}:{target_port}")

            # Connect to the target service
            try:
                target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_socket.connect((target_host, target_port))
                print(f"[INFO] Connected to target {target_host}:{target_port}")

                # Send success response to client
                client_socket.send(b"OK")

                # Create bidirectional forwarding
                client_to_target = threading.Thread(
                    target=self.forward_data,
                    args=(client_socket, target_socket, "client->target"),
                    daemon=True
                )
                target_to_client = threading.Thread(
                    target=self.forward_data,
                    args=(target_socket, client_socket, "target->client"),
                    daemon=True
                )

                client_to_target.start()
                target_to_client.start()

                # Wait for threads to complete
                client_to_target.join()
                target_to_client.join()

            except Exception as e:
                print(f"[ERROR] Failed to connect to target {target_host}:{target_port}: {e}")
                client_socket.send(b"ERROR")

        except Exception as e:
            print(f"[ERROR] Error handling client {client_address}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            print(f"[INFO] Tunnel client {client_address} disconnected")

    def start(self):
        """Start the tunnel server."""
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
        print(f"[INFO] Listening for tunnel clients on 0.0.0.0:{self.client_port}")
        print(f"[INFO] Clients will specify their target applications")

        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client_connection,
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
  %(prog)s --client-port 5432
  %(prog)s -cp 5432

The server will:
1. Listen on the specified client-port for tunnel client connections
2. Clients will specify which target application to connect to
3. Forward traffic between clients and their target applications
        """
    )

    parser.add_argument(
        '--client-port', '-cp',
        type=int,
        required=True,
        help='Port to listen for tunnel client connections (required)'
    )

    args = parser.parse_args()

    # Validate port
    if args.client_port < 1 or args.client_port > 65535:
        print("[ERROR] Client port must be between 1 and 65535")
        sys.exit(1)

    # Create and start server
    server = TunnelServer(args.client_port)

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
