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


class TunnelClient:
    def __init__(self, remote_ip: str, remote_port: int, target_host: str, target_port: int):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.target_host = target_host
        self.target_port = target_port
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

    def handle_remote_connection(self, remote_socket: socket.socket):
        """Handle connection from tunnel server."""
        print(f"[INFO] Connected to tunnel server, setting up bridge to {self.target_host}:{self.target_port}")

        try:
            # Connect to target application (Flask)
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_host, self.target_port))
            print(f"[INFO] Connected to target {self.target_host}:{self.target_port}")

            # Create bidirectional forwarding
            remote_to_target = threading.Thread(
                target=self.forward_data,
                args=(remote_socket, target_socket, "server->target"),
                daemon=True
            )
            target_to_remote = threading.Thread(
                target=self.forward_data,
                args=(target_socket, remote_socket, "target->server"),
                daemon=True
            )

            remote_to_target.start()
            target_to_remote.start()

            # Wait for either thread to finish
            remote_to_target.join()
            target_to_remote.join()

        except Exception as e:
            print(f"[ERROR] Error handling remote connection: {e}")
        finally:
            try:
                remote_socket.close()
            except:
                pass
            print(f"[INFO] Connection to target closed")

    def start(self):
        """Start the tunnel client."""
        self.running = True

        print(f"[INFO] Tunnel client started")
        print(f"[INFO] Remote server: {self.remote_ip}:{self.remote_port}")
        print(f"[INFO] Target application: {self.target_host}:{self.target_port}")

        try:
            while self.running:
                try:
                    # Connect to tunnel server
                    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote_socket.connect((self.remote_ip, self.remote_port))
                    print(f"[INFO] Connected to tunnel server {self.remote_ip}:{self.remote_port}")

                    # Handle the connection
                    self.handle_remote_connection(remote_socket)

                    print(f"[INFO] Disconnected from tunnel server, reconnecting...")
                    time.sleep(2)  # Wait before reconnecting

                except ConnectionRefusedError:
                    print(f"[ERROR] Connection refused by server {self.remote_ip}:{self.remote_port}")
                    time.sleep(5)  # Wait before retrying
                except Exception as e:
                    print(f"[ERROR] Error connecting to server: {e}")
                    time.sleep(5)  # Wait before retrying

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
  %(prog)s --remote-ip 192.168.1.100 --remote-port 5432 --target-host 127.0.0.1 --target-port 5000
  %(prog)s -ri 127.0.0.1 -rp 5432 -th 127.0.0.1 -tp 5000

The client will:
1. Connect to the tunnel server on remote-port
2. Forward all traffic to the target application on target-port
3. Forward responses back to the tunnel server
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

    args = parser.parse_args()

    # Validate ports
    if args.remote_port < 1 or args.remote_port > 65535:
        print("[ERROR] Remote port must be between 1 and 65535")
        sys.exit(1)

    if args.target_port < 1 or args.target_port > 65535:
        print("[ERROR] Target port must be between 1 and 65535")
        sys.exit(1)

    # Create and start client
    client = TunnelClient(args.remote_ip, args.remote_port, args.target_host, args.target_port)

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
