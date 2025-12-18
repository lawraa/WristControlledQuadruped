#!/usr/bin/env python3
"""
OpenBCI EMG Visualizer - Differential Pair Mode
Real-time visualization of 4 EMG differential pairs from forearm
"""

import serial
import serial.tools.list_ports
import time
import struct
from datetime import datetime
from collections import deque
import numpy as np

class EMGVisualizer:
    def __init__(self):
        self.ser = None
        self.connected = False
        self.streaming = False

        # Settings
        self.BAUD_RATE = 115200
        self.TIMEOUT = 1
        self.EXCLUDED_PORTS = ['/dev/ttyUSB0']  # Dynamixel port

        # Data buffers for 4 differential pairs (last 100 samples)
        self.pair_buffers = {i: deque(maxlen=100) for i in range(1, 5)}
        self.pair_stats = {i: {'min': 0, 'max': 0, 'current': 0, 'rms': 0} for i in range(1, 5)}

        # Raw channel data (8 channels)
        self.channel_data = [0] * 8

        # Packet parsing
        self.packet_count = 0
        self.error_count = 0
        self.start_byte = 0xA0
        self.end_byte = 0xC0

        # Packet buffer for syncing
        self.packet_buffer = bytearray()

    def clear_screen(self):
        """Clear terminal screen"""
        print("\033[2J\033[H", end="")

    def print_status(self, message, status_type="INFO"):
        """Print timestamped status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "ℹ",
            "SUCCESS": "✓",
            "ERROR": "✗",
            "WARNING": "⚠"
        }
        symbol = symbols.get(status_type, "•")
        print(f"[{timestamp}] {symbol} {message}")

    def find_port(self):
        """Find OpenBCI port (excluding Dynamixel port)"""
        ports = list(serial.tools.list_ports.comports())
        available = [p for p in ports if p.device not in self.EXCLUDED_PORTS]

        if not available:
            return None

        # Prefer /dev/ttyUSB0 or /dev/ttyACM0
        for port in available:
            if port.device in ['/dev/ttyUSB0', '/dev/ttyACM0']:
                return port.device

        return available[0].device if available else None

    def connect(self):
        """Connect to OpenBCI board"""
        port = self.find_port()
        if not port:
            self.print_status("No available port found", "ERROR")
            return False

        try:
            self.print_status(f"Connecting to {port}...", "INFO")
            self.ser = serial.Serial(
                port=port,
                baudrate=self.BAUD_RATE,
                timeout=self.TIMEOUT
            )
            time.sleep(2)
            self.ser.reset_input_buffer()
            self.connected = True
            self.print_status(f"Connected to {port}", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Connection failed: {e}", "ERROR")
            return False

    def start_streaming(self):
        """Start data stream"""
        if not self.connected:
            return False

        try:
            self.ser.write(b'b')  # Start streaming
            time.sleep(0.1)
            self.streaming = True
            self.print_status("Streaming started", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Failed to start streaming: {e}", "ERROR")
            return False

    def stop_streaming(self):
        """Stop data stream"""
        if self.connected and self.streaming:
            try:
                self.ser.write(b's')  # Stop streaming
                time.sleep(0.1)
                self.streaming = False
                self.print_status("Streaming stopped", "SUCCESS")
            except Exception as e:
                self.print_status(f"Error stopping stream: {e}", "ERROR")

    def parse_packet(self, packet):
        """Parse OpenBCI data packet (33 bytes)"""
        if len(packet) != 33:
            return None

        # Verify start byte
        if packet[0] != self.start_byte:
            return None

        # Sample number (byte 1)
        sample_num = packet[1]

        # Channel data (bytes 2-25, 3 bytes per channel, 8 channels)
        channels = []
        for i in range(8):
            offset = 2 + (i * 3)
            # Combine 3 bytes into 24-bit signed value
            val = (packet[offset] << 16) | (packet[offset+1] << 8) | packet[offset+2]
            # Convert to signed 24-bit
            if val >= 0x800000:
                val -= 0x1000000
            channels.append(val)

        # Verify end byte
        if packet[32] != self.end_byte:
            return None

        return channels

    def extract_pairs(self, channels):
        """Extract the 4 pairs we're using: N1P, N2P, N5P, N6P"""
        if len(channels) < 8:
            return None

        # Each channel is already differential (top pin - bottom pin)
        # We're using channels at indices: 0 (N1P), 1 (N2P), 4 (N5P), 5 (N6P)
        pairs = [
            channels[0],  # Pair 1: N1P
            channels[1],  # Pair 2: N2P
            channels[4],  # Pair 3: N5P
            channels[5],  # Pair 4: N6P
        ]

        return pairs

    def create_bar(self, value, min_val, max_val, width=40):
        """Create a text-based bar graph"""
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)

        bar_len = int(normalized * width)
        bar = '█' * bar_len + '░' * (width - bar_len)
        return bar

    def display_channels(self):
        """Display EMG differential pair activity"""
        self.clear_screen()

        print("=" * 90)
        print("OpenBCI EMG Visualizer - 4 Differential Pairs")
        print("=" * 90)
        print()
        print(f"Status: {'Connected' if self.connected else 'Disconnected'} | "
              f"Streaming: {'Yes' if self.streaming else 'No'} | "
              f"Packets: {self.packet_count} | "
              f"Errors: {self.error_count}")
        print()
        print("Electrode Configuration:")
        print("  Pair 1: Top/Bottom N1P  |  Pair 2: Top/Bottom N2P")
        print("  Pair 3: Top/Bottom N5P  |  Pair 4: Top/Bottom N6P")
        print("  Reference: Bottom BIAS (bony area)")
        print()
        print("Differential Pair Activity:")
        print("-" * 90)

        # Display 4 differential pairs
        pair_labels = [
            (1, "Pair 1 (N1P)"),
            (2, "Pair 2 (N2P)"),
            (3, "Pair 3 (N5P)"),
            (4, "Pair 4 (N6P)"),
        ]

        for pair_num, label in pair_labels:
            stats = self.pair_stats[pair_num]
            current = stats['current']
            min_val = stats['min']
            max_val = stats['max']
            rms = stats['rms']

            # Create bar graph
            bar = self.create_bar(current, min_val, max_val, width=50)

            # Display with RMS value
            print(f"{label:15} [{bar}] {current:10d}  RMS: {rms:8.0f}")

        print()
        print("-" * 90)
        print()
        print("Tips:")
        print("  - Flex/extend wrist to see muscle activity")
        print("  - RMS shows signal strength (higher = more muscle activity)")
        print("  - Make sure electrodes have good contact with skin")
        print()
        print("Press Ctrl+C to exit")

    def update_pair_stats(self, pair_num, value):
        """Update differential pair statistics"""
        if value < self.pair_stats[pair_num]['min']:
            self.pair_stats[pair_num]['min'] = value
        if value > self.pair_stats[pair_num]['max']:
            self.pair_stats[pair_num]['max'] = value
        self.pair_stats[pair_num]['current'] = value

        # Add to buffer
        self.pair_buffers[pair_num].append(value)

        # Calculate RMS from buffer
        if len(self.pair_buffers[pair_num]) > 0:
            buffer_array = np.array(self.pair_buffers[pair_num])
            self.pair_stats[pair_num]['rms'] = np.sqrt(np.mean(buffer_array**2))

    def read_and_process(self):
        """Read and process OpenBCI packets"""
        if not self.connected or not self.streaming:
            return

        try:
            # Read available data
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                self.packet_buffer.extend(data)

                # Process complete packets from buffer
                while len(self.packet_buffer) >= 33:
                    # Look for start byte
                    start_idx = self.packet_buffer.find(self.start_byte)

                    if start_idx == -1:
                        # No start byte found, clear buffer
                        self.packet_buffer.clear()
                        break

                    # Remove data before start byte
                    if start_idx > 0:
                        self.packet_buffer = self.packet_buffer[start_idx:]

                    # Check if we have a complete packet
                    if len(self.packet_buffer) < 33:
                        break

                    # Extract packet
                    packet = self.packet_buffer[:33]

                    # Parse packet
                    channels = self.parse_packet(packet)

                    if channels is not None:
                        # Extract the 4 pairs we're using
                        pairs = self.extract_pairs(channels)

                        if pairs is not None:
                            # Update stats for each pair
                            for i, pair_value in enumerate(pairs):
                                self.update_pair_stats(i + 1, pair_value)

                            self.packet_count += 1
                    else:
                        self.error_count += 1

                    # Remove processed packet from buffer
                    self.packet_buffer = self.packet_buffer[33:]

        except Exception as e:
            self.error_count += 1

    def run(self):
        """Main visualization loop"""
        self.clear_screen()
        print("Starting EMG Visualizer...")
        print()

        if not self.connect():
            return

        print()
        if not self.start_streaming():
            return

        print()
        print("Initializing visualization...")
        time.sleep(1)

        try:
            last_update = time.time()
            update_interval = 0.1  # Update display 10 times per second

            while True:
                # Read data continuously
                self.read_and_process()

                # Update display periodically
                if time.time() - last_update > update_interval:
                    self.display_channels()
                    last_update = time.time()

                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\nShutting down...")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.streaming:
            self.stop_streaming()

        if self.connected and self.ser:
            self.ser.close()
            self.connected = False
            print("Connection closed")

        print(f"\nSession summary:")
        print(f"  Packets received: {self.packet_count}")
        print(f"  Errors: {self.error_count}")

def main():
    viz = EMGVisualizer()
    viz.run()

if __name__ == "__main__":
    main()
