# P2PFileTransfer - Peer-to-Peer File Sharing

**P2PFileTransfer** is a peer-to-peer (P2P) file sharing application similar to BitTorrent. It enables efficient file distribution among peers over a TCP connection. The application implements the BitTorrent protocol with modifications, focusing on the choking-unchoking mechanism to regulate the flow of data between peers.

## Features

- **Peer-to-Peer File Sharing**: Efficiently share files among peers without the need for a central server.
- **Choking-Unchoking Mechanism**: Implement the BitTorrent protocol's choking-unchoking mechanism to manage bandwidth and connection efficiency.
- **Handshake**: Peers exchange handshake messages to establish a connection, ensuring secure communication.
- **TCP Communication**: Communication between peers is handled over reliable TCP connections.
- **Multiple Peers Support**: Handle multiple peers in the system, allowing for dynamic file sharing.

## Tech Stack

- **Programming Language**: Python
- **Protocol**: TCP for communication, BitTorrent-inspired protocol for file sharing
- **File Sharing**: Peer-to-Peer (P2P) mechanism
- **Data Serialization**: JSON for transmitting metadata and file details

## Requirements

- **Python 3.x** or higher
- **TCP Network Environment**

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/saipreethi18/P2PFileTransfer.git
   cd P2PFileTransfer
Install dependencies (if any): Make sure you have the necessary dependencies, such as socket and json for network communication and data serialization. You can install any dependencies using pip, e.g.:

bash
Copy
Edit
pip install -r requirements.txt
Run the project: To start the P2P file transfer application, run:

bash
Copy
Edit
python peerProcess.py
How to Use
Start Peers: Each peer runs the Python script peerProcess.py, which initializes the peer-to-peer file sharing system.

Connect Peers: Once the application is running, peers will automatically initiate connections with each other to begin file sharing.

Share Files: You can share files by placing them in the appropriate directories defined by the project and allowing other peers to download them.

Folder Structure
plaintext
Copy
Edit
P2PFileTransfer/
│
├── peerProcess.py        # Main script for handling the peer process
├── PeerInfo.cfg          # Configuration file for peer details
├── Common.cfg            # Common configurations for peers
├── utils/                # Utility functions for connection, file management, etc.
│   ├── connection.py
│   ├── file_manager.py
│   ├── log_manager.py
│   └── message.py
├── peer_1001/            # Peer-specific data (e.g., logs, shared files)
│   └── log_peer_1001.log
├── peer_1002/
│   └── log_peer_1002.log
└── __MACOSX/             # Mac OS-specific files
Protocol Description
This project follows a simplified BitTorrent protocol, with the following core components:

Handshake:

A handshake message consists of a 32-byte message with a header (P2PFILESHARINGPROJ), followed by 10 zero bytes, and a 4-byte peer ID.

Handshake establishes an initial connection between peers.

Choking-Unchoking Mechanism:

Peers control the flow of data by choking (pausing) or unchoking (resuming) other peers based on bandwidth and availability.

File Distribution:

Files are broken into pieces, and each peer shares pieces they have with other peers.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Contributing
Feel free to fork the repository, open issues, and submit pull requests. Contributions are welcome!

Contact
Author: Sai Preethi Kota

Email: saipreethikota18@gmail.com

GitHub: saipreethi18

vbnet
Copy
Edit

You can now paste this into your `README.md` file for your GitHub project. Let me know if you need further adjustments!







