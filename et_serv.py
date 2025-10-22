#!/usr/bin/env python3
"""
et_serv.py — Reverse tunnel server
Listens on --share-port (public port).
Generates random free control port if not specified.
"""

import argparse
import socket
import threading
import struct
import random

CMD_OPEN = 1
CMD_DATA = 2
CMD_CLOSE = 3


def parse_args():
    p = argparse.ArgumentParser(description="Reverse tunnel server")
    p.add_argument("--share-port", "-sp", type=int, required=True,
                   help="Public port to listen for external clients.")
    p.add_argument("--control-port", "-cp", type=int, default=0,
                   help="Port for control connection from tunnel client (0 = auto)")
    return p.parse_args()


def find_free_port(max_port=10000):
    """Find random free TCP port below max_port"""
    while True:
        port = random.randint(1024, max_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue


class TunnelServer:
    def __init__(self, share_port, control_port):
        if control_port == 0:
            control_port = find_free_port()
        self.share_port = share_port
        self.control_port = control_port
        self.client_conn = None
        self.lock = threading.Lock()

    def start(self):
        print(f"[INFO] Control port: {self.control_port}")
        threading.Thread(target=self._wait_for_client, daemon=True).start()
        self._listen_share_port()

    def _wait_for_client(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.control_port))
        s.listen(1)
        print(f"[INFO] Waiting for tunnel client on control port {self.control_port} ...")
        conn, addr = s.accept()
        print(f"[INFO] Tunnel client connected from {addr}")
        with self.lock:
            self.client_conn = conn

    def _listen_share_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.share_port))
        s.listen(5)
        print(f"[INFO] Listening on 0.0.0.0:{self.share_port}")
        while True:
            conn, addr = s.accept()
            print(f"[NEW] Incoming external connection from {addr}")
            threading.Thread(target=self._handle_ext_conn, args=(conn,), daemon=True).start()

    def _handle_ext_conn(self, ext_sock):
        while True:
            with self.lock:
                if self.client_conn:
                    ctrl = self.client_conn
                    break
        stream_id = id(ext_sock) & 0xFFFFFFFF
        try:
            ctrl.sendall(struct.pack("!BI", CMD_OPEN, stream_id))
        except Exception as e:
            print(f"[ERR] cannot send OPEN: {e}")
            ext_sock.close()
            return
        threading.Thread(target=self._forward, args=(ext_sock, ctrl, stream_id), daemon=True).start()

    def _forward(self, src, ctrl, stream_id):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                packet = struct.pack("!BI", CMD_DATA, stream_id) + struct.pack("!I", len(data)) + data
                ctrl.sendall(packet)
        except Exception:
            pass
        finally:
            try:
                ctrl.sendall(struct.pack("!BI", CMD_CLOSE, stream_id))
            except:
                pass
            src.close()
            print(f"[-] Connection {stream_id} closed")


if __name__ == "__main__":
    args = parse_args()
    srv = TunnelServer(args.share_port, args.control_port)
    srv.start()
