# Peer-to-Peer File Sharing System

## Overview

This project implements a peer-to-peer (P2P) file-sharing system that efficiently distributes a file among peers. The system is inspired by the BitTorrent protocol and includes features such as preferred neighbors, optimistic unchoking, bitfield exchange, and piece requests for robust data transmission.

---

## Features

1. **File Sharing**:
   - Allows peers to share and download files in pieces efficiently.
   - Supports dynamic connections between multiple peers.

2. **Preferred Neighbors**:
   - Selects preferred neighbors based on download rates for optimal performance.

3. **Optimistic Unchoking**:
   - Periodically unchokes a random peer to ensure fairness.

4. **Bitfield Exchange**:
   - Synchronizes piece availability information between peers.

5. **Logging**:
   - Provides detailed logs for all peer interactions and events.

---

## Configuration

### Common Configuration (`common.cfg`)

Defines global settings for the P2P system:

```plaintext
NumberOfPreferredNeighbors 3
UnchokingInterval 5
OptimisticUnchokingInterval 10
FileName TheFile.dat
FileSize 20971520
PieceSize 16384
```

- **NumberOfPreferredNeighbors**: Number of preferred neighbors selected during each interval.
- **UnchokingInterval**: Interval (in seconds) for recalculating preferred neighbors.
- **OptimisticUnchokingInterval**: Interval (in seconds) for optimistic unchoking.
- **FileName**: Name of the file being shared.
- **FileSize**: Size of the file in bytes.
- **PieceSize**: Size of each file piece in bytes.

### Peer Configuration (`peer_info.cfg`)

Defines peer-specific settings, including ports and initial file availability:

```plaintext
1001 localhost 6001 1
1002 localhost 6002 0
1003 localhost 6003 0
1004 localhost 6004 0
1005 localhost 6005 0
```

- **Peer ID**: Unique identifier for each peer.
- **Hostname**: Hostname of the peer (e.g., `localhost`).
- **Port**: Port number for the peer.
- **Has File**: `1` if the peer has the complete file initially, `0` otherwise.

---

## How to Run

### Prerequisites

- Python 3.x
- Adequate disk space (~150MB) for file storage and temporary pieces.

### Steps

1. **Download the Project**:
   - Download the project files from your source.

2. **Configure Settings**:
   - Update `common.cfg` and `peer_info.cfg` to reflect your environment.

3. **Start Peers**:
   Run each peer in a separate terminal window:
   ```bash
   python peerProcess.py <peerID>
   ```
   Replace `<peerID>` with the respective peer ID (e.g., `1001`, `1002`, etc.).

4. **File Sharing**:
   - The peer with the complete file (`has_file=1`) starts sharing.
   - Logs are generated in the working directory for each peer (e.g., `log_peer_1001.log`).

---

## Code Structure

### Main Files

1. **`peerProcess.py`**:
   - Entry point for the application. Initializes peers, manages server and client listeners, and handles shutdowns.

2. **`utils/connection.py`**:
   - Manages peer connections and message exchanges.

3. **`utils/file_manager.py`**:
   - Handles file operations, including splitting and merging file pieces.

4. **`utils/peer_manager.py`**:
   - Tracks peer states, bitfields, and neighbor preferences.

5. **`utils/log_manager.py`**:
   - Generates logs for peer activities.

6. **`utils/message.py`**:
   - Defines message types and handles their encoding/decoding.

---

## Logging

Each peer generates a log file (e.g., `log_peer_<peerID>.log`). Logs include:

- Peer connections and disconnections.
- Message exchanges (`HAVE`, `REQUEST`, `PIECE`, etc.).
- Download progress and completion.
- Optimistic unchoking events.

### Example Log

```plaintext
[2024-12-04 22:00:00] Peer 1002 makes a connection to Peer 1001.
[2024-12-04 22:00:05] Peer 1002 received the 'HAVE' message from Peer 1001 for piece 5.
[2024-12-04 22:00:10] Peer 1002 downloaded piece 5. Source: Peer 1001.
[2024-12-04 22:00:15] Peer 1002 has downloaded the complete file.
[2024-12-04 22:00:20] Peer 1002 optimistically unchoked Peer 1003.
```

---

## Video Demonstration

Watch the system in action: [https://drive.google.com/file/d/12h21UvRlGdgop_CLqM_A8M3lXuRXCmkj/view?usp=sharing](#).

---

## Future Enhancements

- Implement encryption for secure file transfers.
- Add peer discovery for dynamic networks.
- Optimize bandwidth utilization for large-scale systems.

---

## Authors

- Deepthi Nidasanametla
- UFID : 1933-1193

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
