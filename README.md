# Simple Tunnel

### A simple reverse tunnel implementation in Python that allows you to expose local services through a remote server.
### Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

## Overview

Easy Tunnel consists of two components:
- **Server** (`et_serv.py`) - Runs on a public server and accepts external connections
- **Client** (`client.py`) - Runs on your local machine and connects to the server

The tunnel works by establishing a control connection between the client and server, then forwarding data from external connections through the server to your local service.

## Features

- Simple reverse tunnel implementation
- No authentication (use with caution)
- Automatic control port selection
- Multithreaded data forwarding
- Clean connection handling

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Usage

### 1. Start the Server

On your public server, run:

```bash
python3 et_serv.py --share-port 8080 --control-port 9001
```

- `--share-port` (required): Public port where external clients will connect
- `--control-port` (optional): Port for control connection from tunnel client (default: auto-select)

### 2. Start the Client

On your local machine, run:

```bash
python3 client.py --serv-ip YOUR_SERVER_IP --local-port 3000 --control-port 9001
```

- `--serv-ip` (required): IP address of your server
- `--local-port` (required): Local service port to tunnel
- `--control-port` (optional): Server control port (default: 9001)

### (the ports can be changed)

### 3. Connect to Your Service

Once both are running, external clients can connect to `YOUR_SERVER_IP:8080` and their traffic will be forwarded to your local service on port 3000.

## Protocol

### The tunnel uses a simple binary protocol:

- `CMD_OPEN (1)`: Open a new stream
- `CMD_DATA (2)`: Send data through a stream  
- `CMD_CLOSE (3)`: Close a stream

### Each message consists of:
- 1 byte: Command
- 4 bytes: Stream ID (big-endian)
- Variable: Payload (for DATA commands)

## Security Note

This implementation has no authentication or encryption. Use only in trusted networks or add your own security measures.
#### In the future, protective measures will be added.

## License and Contributing

#### Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

### GNU General Public License v3.0 - see LICENSE file for details.
