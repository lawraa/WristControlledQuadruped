#!/usr/bin/env python3
"""
EMG Gesture Data Collector
Collects labeled EMG samples for training gesture recognition model
"""

import serial
import serial.tools.list_ports
import time
import json
import os
from datetime import datetime
from collections import deque
import numpy as np

class GestureDataCollector:
    def __init__(self, output_dir="training_data"):
        self.ser = None
        self.connected = False
        self.streaming = False

        # Settings
        self.BAUD_RATE = 115200
        self.TIMEOUT = 1
        self.EXCLUDED_PORTS = ['/dev/ttyUSB1']

        # Data collection
        self.output_dir = output_dir
        self.samples = []
        self.current_gesture = None

        # Packet parsing
        self.start_byte = 0xA0
        self.end_byte = 0xC0
        self.packet_buffer = bytearray()

        # Window settings for collection
        self.WINDOW_SIZE = 200  # Number of samples per window (200ms @ 1000Hz ≈ 200 samples)
        self.window_buffer = deque(maxlen=self.WINDOW_SIZE)

        # Gesture definitions
        self.GESTURES = {
            '1': 'forward',      # Wrist extension
            '2': 'backward',     # Wrist flexion
            '3': 'left',         # Ulnar deviation
            '4': 'right',        # Radial deviation
            '5': 'stop',         # Rest/neutral
            '6': 'jump',         # Hand spread
        }

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

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
        """Find OpenBCI port"""
        ports = list(serial.tools.list_ports.comports())
        available = [p for p in ports if p.device not in self.EXCLUDED_PORTS]

        if not available:
            return None

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
            self.ser.write(b'b')
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
                self.ser.write(b's')
                time.sleep(0.1)
                self.streaming = False
                self.print_status("Streaming stopped", "SUCCESS")
            except Exception as e:
                self.print_status(f"Error stopping stream: {e}", "ERROR")

    def parse_packet(self, packet):
        """Parse OpenBCI data packet"""
        if len(packet) != 33:
            return None

        if packet[0] != self.start_byte:
            return None

        # Channel data (8 channels, 3 bytes each)
        channels = []
        for i in range(8):
            offset = 2 + (i * 3)
            val = (packet[offset] << 16) | (packet[offset+1] << 8) | packet[offset+2]
            if val >= 0x800000:
                val -= 0x1000000
            channels.append(val)

        if packet[32] != self.end_byte:
            return None

        return channels

    def extract_pairs(self, channels):
        """Extract 4 pairs: N1P, N2P, N5P, N6P"""
        if len(channels) < 8:
            return None

        pairs = [
            channels[0],  # N1P
            channels[1],  # N2P
            channels[4],  # N5P
            channels[5],  # N6P
        ]

        return pairs

    def read_packet(self):
        """Read and parse one packet, return pairs or None"""
        try:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                self.packet_buffer.extend(data)

                while len(self.packet_buffer) >= 33:
                    start_idx = self.packet_buffer.find(self.start_byte)

                    if start_idx == -1:
                        self.packet_buffer.clear()
                        break

                    if start_idx > 0:
                        self.packet_buffer = self.packet_buffer[start_idx:]

                    if len(self.packet_buffer) < 33:
                        break

                    packet = self.packet_buffer[:33]
                    channels = self.parse_packet(packet)

                    if channels is not None:
                        pairs = self.extract_pairs(channels)
                        self.packet_buffer = self.packet_buffer[33:]
                        return pairs

                    self.packet_buffer = self.packet_buffer[33:]

        except Exception as e:
            pass

        return None

    def collect_window(self):
        """Collect a window of EMG data"""
        self.window_buffer.clear()

        print("\nCollecting window...", end="", flush=True)

        while len(self.window_buffer) < self.WINDOW_SIZE:
            pairs = self.read_packet()
            if pairs is not None:
                self.window_buffer.append(pairs)
                # Show progress
                if len(self.window_buffer) % 50 == 0:
                    print(".", end="", flush=True)
            time.sleep(0.001)

        print(" Done!")

        # Convert to numpy array
        window_data = np.array(self.window_buffer)
        return window_data

    def save_sample(self, window_data, gesture_label):
        """Save a sample with label"""
        sample = {
            'timestamp': datetime.now().isoformat(),
            'gesture': gesture_label,
            'data': window_data.tolist(),
            'shape': window_data.shape
        }

        self.samples.append(sample)

        # Also save incrementally to file
        filename = os.path.join(self.output_dir, f"{gesture_label}.jsonl")
        with open(filename, 'a') as f:
            f.write(json.dumps(sample) + '\n')

        self.print_status(f"Saved sample for gesture '{gesture_label}' (Total: {len(self.samples)})", "SUCCESS")

    def display_menu(self):
        """Display collection menu"""
        self.clear_screen()

        print("=" * 70)
        print("EMG Gesture Data Collector")
        print("=" * 70)
        print()
        print("Gestures to collect:")
        print()
        for key, gesture in self.GESTURES.items():
            count = sum(1 for s in self.samples if s['gesture'] == gesture)
            print(f"  [{key}] {gesture.upper():15} - {count} samples collected")
        print()
        print("Commands:")
        print("  [1-6] - Record sample for gesture")
        print("  [s]   - Show statistics")
        print("  [q]   - Quit and save")
        print()
        print("=" * 70)

    def show_statistics(self):
        """Show collection statistics"""
        print("\n" + "=" * 70)
        print("Collection Statistics")
        print("=" * 70)

        for gesture in self.GESTURES.values():
            count = sum(1 for s in self.samples if s['gesture'] == gesture)
            print(f"  {gesture.upper():15} - {count:3d} samples")

        print(f"\n  TOTAL: {len(self.samples)} samples")
        print("=" * 70)

        input("\nPress Enter to continue...")

    def save_all(self):
        """Save all collected data"""
        if not self.samples:
            self.print_status("No samples to save", "WARNING")
            return

        # Save summary file
        summary_file = os.path.join(self.output_dir, "dataset_summary.json")
        summary = {
            'total_samples': len(self.samples),
            'gestures': {
                gesture: sum(1 for s in self.samples if s['gesture'] == gesture)
                for gesture in self.GESTURES.values()
            },
            'window_size': self.WINDOW_SIZE,
            'num_channels': 4,
            'collection_date': datetime.now().isoformat()
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        self.print_status(f"Saved dataset summary to {summary_file}", "SUCCESS")
        self.print_status(f"Total samples: {len(self.samples)}", "INFO")

    def run(self):
        """Main collection loop"""
        self.clear_screen()
        print("Starting Gesture Data Collector...\n")

        if not self.connect():
            return

        if not self.start_streaming():
            return

        print("\nWaiting for data stream to stabilize...")
        time.sleep(2)

        try:
            while True:
                self.display_menu()

                choice = input("Enter command: ").strip().lower()

                if choice in self.GESTURES:
                    gesture_name = self.GESTURES[choice]
                    print(f"\n>>> Recording gesture: {gesture_name.upper()}")
                    print(">>> Get ready! Starting in 3 seconds...")
                    time.sleep(3)

                    window_data = self.collect_window()
                    self.save_sample(window_data, gesture_name)

                    time.sleep(0.5)

                elif choice == 's':
                    self.show_statistics()

                elif choice == 'q':
                    print("\nSaving and exiting...")
                    break

                else:
                    print("Invalid choice. Press Enter to continue...")
                    input()

        except KeyboardInterrupt:
            print("\n\nInterrupted by user...")

        finally:
            self.save_all()
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.streaming:
            self.stop_streaming()

        if self.connected and self.ser:
            self.ser.close()
            self.connected = False
            print("Connection closed")

def main():
    print("=" * 70)
    print("EMG Gesture Data Collection")
    print("=" * 70)
    print()
    print("Instructions:")
    print("  1. Position yourself comfortably")
    print("  2. Select a gesture to record")
    print("  3. Perform the gesture when prompted")
    print("  4. Record 30-50 samples per gesture for best results")
    print()
    print("Gesture Guide:")
    print("  FORWARD  - Extend wrist upward")
    print("  BACKWARD - Curl wrist downward")
    print("  LEFT     - Tilt wrist toward pinky")
    print("  RIGHT    - Tilt wrist toward thumb")
    print("  STOP     - Relax, neutral position")
    print("  JUMP     - Spread fingers wide")
    print()
    input("Press Enter to start...")

    collector = GestureDataCollector()
    collector.run()

if __name__ == "__main__":
    main()
