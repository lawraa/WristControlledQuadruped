# Wristband Control - OpenBCI Interface

Interface for reading EMG data from the OpenBCI Cyton 16-channel board for wristband control.

## Hardware

- OpenBCI Cyton 16-channel board
- RF USB dongle (typically appears as `/dev/ttyUSB0`)

## Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Make sure your user has access to serial ports:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in for this to take effect
```

## Usage

### 1. Check Connection Status

Run the monitor script to verify the board is communicating:

```bash
./openbci_monitor.py
```

This will:
- Auto-detect the OpenBCI board on available serial ports
- **Automatically exclude `/dev/ttyUSB1` (reserved for Dynamixel motors)**
- Display connection status
- Show real-time data streaming
- Update packet counts and error rates

### 2. Visualize EMG Data

Once you have electrodes connected, use the visualizer for real-time EMG display:

```bash
./emg_visualizer.py
```

This shows:
- Live bar graphs for each channel
- Current signal values
- Channel activity as you flex/extend your wrist

### 3. Electrode Setup

See `ELECTRODE_GUIDE.md` for detailed instructions on:
- Where to place electrodes on your forearm
- How to wire them to the OpenBCI board
- Muscle locations for different movements
- Troubleshooting signal quality

Press `Ctrl+C` to stop any script.

## Port Exclusion

The script is configured to **avoid `/dev/ttyUSB1`** which is used for Dynamixel motor control. This port will be marked as `[EXCLUDED - Dynamixel]` during port scanning and will never be used for OpenBCI communication.

To modify excluded ports, edit the `EXCLUDED_PORTS` list in `openbci_monitor.py`:
```python
self.EXCLUDED_PORTS = ['/dev/ttyUSB1']  # Add more ports as needed
```

## Connection Settings

- Baud rate: 115200
- Data bits: 8
- Stop bits: 1
- Parity: None
- Sample rate: 250 Hz

## Troubleshooting

If you see permission errors, you may need to add yourself to the `dialout` or `plugdev` group:
```bash
sudo usermod -a -G dialout $USER
sudo usermod -a -G plugdev $USER
```

Then log out and back in.
