#!/usr/bin/env python3

import argparse
import socket
import struct
import threading

CMD_OPEN = 1
CMD_DATA = 2
CMD_CLOSE = 3

def parse_args():
    p = argparse.ArgumentParser(description="Reverse tunnel client")
    p.add_argument("--serv-ip", "-sa", required=True, help="Server IP")
    p.add_argument("--control-port", "-cp", type=int, default=9001, help="Server control port")
    p.add_argument("--local-port", "-lp", type=int, required=True, help="Local service port to connect to")
    return p.parse_args()

class TunnelClient:
    def __init__(self, serv_ip, control_port, local_port):
        self.addr = (serv_ip, control_port)
        self.local_port = local_port
        self.sock = None
        self.streams = {}

    def start(self):
        print(f"[INFO] Connecting to server control {self.addr} ...")
        self.sock = socket.create_connection(self.addr)
        print("[INFO] Connected to server.")
        threading.Thread(target=self._reader, daemon=True).start()

        try:
            while True:
                threading.Event().wait(3600)

        except KeyboardInterrupt:
            print("\n[STOP] client exiting")
            self.sock.close()

        print("\n  TUNNEL ACTIVATED\n")

    def _reader(self):
        buf = b""
        while True:
            data = self.sock.recv(4096)
            if not data:
                print("[ERR] control connection closed")
                return
            buf += data
            buf = self._process(buf)

    def _process(self, buf):
        offset = 0
        while True:
            if offset + 5 > len(buf):
                break
            cmd = buf[offset]
            stream_id = struct.unpack_from("!I", buf, offset+1)[0]
            offset += 5
            if cmd == CMD_OPEN:
                try:
                    s = socket.create_connection(("localhost", self.local_port))
                    self.streams[stream_id] = s
                    threading.Thread(target=self._forward_local_to_server, args=(stream_id, s), daemon=True).start()
                except Exception as e:
                    print(f"[ERR] cannot connect to local service: {e}")
                    try:
                        self.sock.sendall(struct.pack("!BI", CMD_CLOSE, stream_id))
                    except:
                        pass
            elif cmd == CMD_DATA:
                if offset + 4 > len(buf):
                    offset -= 5
                    break
                data_len = struct.unpack_from("!I", buf, offset)[0]
                offset += 4
                if offset + data_len > len(buf):
                    offset -= 9
                    break
                payload = buf[offset:offset+data_len]
                offset += data_len
                s = self.streams.get(stream_id)
                if s:
                    try:
                        s.sendall(payload)
                    except:
                        s.close()
                        del self.streams[stream_id]
            elif cmd == CMD_CLOSE:
                s = self.streams.pop(stream_id, None)
                if s:
                    s.close()
            else:
                pass
        return buf[offset:]

    def _forward_local_to_server(self, stream_id, local_sock):
        try:
            while True:
                data = local_sock.recv(4096)
                if not data:
                    break
                pkt = struct.pack("!BI", CMD_DATA, stream_id) + struct.pack("!I", len(data)) + data
                self.sock.sendall(pkt)
        except Exception:
            pass
        finally:
            try:
                self.sock.sendall(struct.pack("!BI", CMD_CLOSE, stream_id))
            except:
                pass

            local_sock.close()

if __name__ == "__main__":
    args = parse_args()
    TunnelClient(args.serv_ip, args.control_port, args.local_port).start()
