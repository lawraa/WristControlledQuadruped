#!/usr/bin/env python3
"""
Automated EMG Gesture Data Collector
Automatically cycles through gestures with timed prompts
"""

import serial
import serial.tools.list_ports
import time
import json
import os
from datetime import datetime
from collections import deque
import numpy as np
import random

class AutoGestureCollector:
    def __init__(self, session_name=None):
        self.ser = None
        self.connected = False
        self.streaming = False

        # Settings
        self.BAUD_RATE = 115200
        self.TIMEOUT = 1
        self.EXCLUDED_PORTS = ['/dev/ttyUSB1']

        # Data collection
        self.session_name = session_name
        self.output_dir = None  # Set after session name is determined
        self.samples = []

        # Packet parsing
        self.start_byte = 0xA0
        self.end_byte = 0xC0
        self.packet_buffer = bytearray()

        # Window settings
        self.WINDOW_SIZE = 200

        # Gesture definitions with detailed instructions
        self.GESTURES = [
            {
                'name': 'forward',
                'display': 'FORWARD',
                'action': 'Extend wrist upward',
                'description': 'Point your hand toward the ceiling',
                'command': 'Make the quadruped move forward'
            },
            {
                'name': 'backward',
                'display': 'BACKWARD',
                'action': 'Flex wrist downward',
                'description': 'Point your hand toward the floor',
                'command': 'Make the quadruped move backward'
            },
            {
                'name': 'left',
                'display': 'LEFT',
                'action': 'Tilt wrist toward pinky side',
                'description': 'Ulnar deviation - bend wrist left',
                'command': 'Make the quadruped turn left'
            },
            {
                'name': 'right',
                'display': 'RIGHT',
                'action': 'Tilt wrist toward thumb side',
                'description': 'Radial deviation - bend wrist right',
                'command': 'Make the quadruped turn right'
            },
            {
                'name': 'stop',
                'display': 'STOP',
                'action': 'Relax - neutral position',
                'description': 'Let your hand rest naturally',
                'command': 'Make the quadruped stop'
            },
            {
                'name': 'jump',
                'display': 'JUMP',
                'action': 'Spread fingers wide',
                'description': 'Open your hand and spread all fingers',
                'command': 'Make the quadruped jump'
            }
        ]

        # Session presets
        self.PRESETS = {
            'single': {
                'name': 'Single Sample Test (1 per gesture)',
                'duration_minutes': 1,
                'samples_per_gesture': 1,
                'gesture_duration': 1.0,
                'rest_duration': 0.3
            },
            'test': {
                'name': '1-Minute Test Session (5 per gesture)',
                'duration_minutes': 1,
                'samples_per_gesture': 5,
                'gesture_duration': 1.0,
                'rest_duration': 0.3
            },
            'quick': {
                'name': '5-Minute Quick Session',
                'duration_minutes': 5,
                'samples_per_gesture': 15,
                'gesture_duration': 1.5,
                'rest_duration': 1.0
            },
            'standard': {
                'name': '15-Minute Standard Session',
                'duration_minutes': 15,
                'samples_per_gesture': 50,
                'gesture_duration': 2.0,
                'rest_duration': 1.0
            },
            'long': {
                'name': '30-Minute Extended Session',
                'duration_minutes': 30,
                'samples_per_gesture': 100,
                'gesture_duration': 2.5,
                'rest_duration': 1.0
            },
            'custom_fast': {
                'name': '10-Minute Fast Session',
                'duration_minutes': 10,
                'samples_per_gesture': 30,
                'gesture_duration': 1.0,
                'rest_duration': 0.5
            }
        }

    def set_session_name(self, name):
        """Set session name and create output directory"""
        self.session_name = name
        self.output_dir = os.path.join("training_data", name)
        os.makedirs(self.output_dir, exist_ok=True)

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
            channels[0],
            channels[1],
            channels[4],
            channels[5],
        ]

        return pairs

    def read_packet(self):
        """Read and parse one packet"""
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

    def collect_window(self, duration_seconds):
        """Collect EMG data for specified duration"""
        window_buffer = deque(maxlen=self.WINDOW_SIZE * 10)  # Large buffer
        start_time = time.time()
        packets_read = 0
        null_count = 0

        while time.time() - start_time < duration_seconds:
            pairs = self.read_packet()
            if pairs is not None:
                window_buffer.append(pairs)
                packets_read += 1
            else:
                null_count += 1
            time.sleep(0.001)

        # Debug output
        elapsed = time.time() - start_time
        print(f"\n  Collected {len(window_buffer)} samples in {elapsed:.2f}s (need {self.WINDOW_SIZE})")
        print(f"  Packets read: {packets_read}, Null reads: {null_count}")

        if len(window_buffer) > 0:
            print(f"  Sample data shape: {np.array(list(window_buffer)[:1]).shape}")
            print(f"  First sample: {list(window_buffer)[0]}")

        # Return the collected data as numpy array
        if len(window_buffer) >= self.WINDOW_SIZE:
            result = np.array(list(window_buffer))
            print(f"  Final array shape: {result.shape}")
            return result
        else:
            print(f"  WARNING: Not enough samples! Only got {len(window_buffer)}/{self.WINDOW_SIZE}")
            return None

    def save_sample(self, window_data, gesture_label):
        """Save a sample with label"""
        sample = {
            'timestamp': datetime.now().isoformat(),
            'gesture': gesture_label,
            'data': window_data.tolist(),
            'shape': window_data.shape
        }

        self.samples.append(sample)

        filename = os.path.join(self.output_dir, f"{gesture_label}.jsonl")
        with open(filename, 'a') as f:
            f.write(json.dumps(sample) + '\n')

        print(f"  ✓ Saved sample to {filename} (shape: {window_data.shape})")

    def display_gesture_prompt(self, gesture, countdown=None, collecting=False):
        """Display current gesture prompt"""
        self.clear_screen()

        print("=" * 80)
        print("AUTOMATED GESTURE COLLECTION")
        print("=" * 80)
        print()

        if collecting:
            print(f">>> PERFORMING GESTURE NOW! <<<")
            print()
            print(f"  Gesture: {gesture['display']}")
            print(f"  Action:  {gesture['action']}")
            print()
            print("  " + "█" * 60)
        elif countdown is not None:
            print(f"Next Gesture: {gesture['display']}")
            print()
            print(f"  Action:      {gesture['action']}")
            print(f"  Description: {gesture['description']}")
            print(f"  Command:     {gesture['command']}")
            print()
            print(f"  Get ready in: {countdown} seconds...")
            print()
            print("  " + "░" * 60)
        else:
            print(f"Current Gesture: {gesture['display']}")
            print()
            print(f"  Action:      {gesture['action']}")
            print(f"  Description: {gesture['description']}")
            print(f"  Command:     {gesture['command']}")

        print()
        print("=" * 80)

    def display_rest(self, seconds_left):
        """Display rest period"""
        self.clear_screen()

        print("=" * 80)
        print("REST PERIOD")
        print("=" * 80)
        print()
        print("  Relax your hand...")
        print(f"  Next gesture in: {seconds_left:.1f} seconds")
        print()
        print("=" * 80)

    def display_progress(self, current, total, gesture_counts):
        """Display session progress"""
        print()
        print("-" * 80)
        print(f"Progress: {current}/{total} samples collected")
        print()
        print("Samples per gesture:")
        for gesture in self.GESTURES:
            count = gesture_counts.get(gesture['name'], 0)
            bar = "█" * count + "░" * (max(gesture_counts.values()) - count)
            print(f"  {gesture['display']:10} [{bar[:30]}] {count}")
        print("-" * 80)

    def run_session(self, preset_key, session_name):
        """Run automated collection session"""
        preset = self.PRESETS[preset_key]

        # Set session name and create directory
        self.set_session_name(session_name)

        self.clear_screen()
        print("=" * 80)
        print(f"Starting: {preset['name']}")
        print("=" * 80)
        print()
        print(f"  Session name: {self.session_name}")
        print(f"  Save location: {self.output_dir}/")
        print()
        print(f"  Duration: {preset['duration_minutes']} minutes")
        print(f"  Target: {preset['samples_per_gesture']} samples per gesture")
        print(f"  Gesture duration: {preset['gesture_duration']}s")
        print(f"  Rest duration: {preset['rest_duration']}s")
        print()
        print("  Total samples: ~{} samples".format(preset['samples_per_gesture'] * len(self.GESTURES)))
        print()
        print("=" * 80)
        print()
        print("Instructions:")
        print("  1. Follow the on-screen prompts")
        print("  2. Perform each gesture when prompted")
        print("  3. Return to neutral position during rest periods")
        print("  4. Press Ctrl+C to stop early (data will be saved)")
        print()
        input("Press Enter to begin...")

        if not self.connect():
            return

        if not self.start_streaming():
            return

        print("\nWaiting for data stream to stabilize...")
        time.sleep(2)

        # Test if we're receiving data
        print("\nTesting data reception...")
        test_count = 0
        test_start = time.time()
        while time.time() - test_start < 2.0 and test_count < 10:
            pairs = self.read_packet()
            if pairs is not None:
                test_count += 1
                if test_count == 1:
                    print(f"  ✓ First packet received: {pairs}")

        if test_count == 0:
            print("  ✗ ERROR: No data received! Check OpenBCI connection.")
            self.cleanup()
            return
        else:
            print(f"  ✓ Data reception OK: {test_count} packets in 2 seconds")

        # Calculate total samples needed
        total_samples_target = preset['samples_per_gesture'] * len(self.GESTURES)
        samples_collected = 0
        gesture_counts = {g['name']: 0 for g in self.GESTURES}

        # Create randomized gesture sequence
        gesture_sequence = []
        for _ in range(preset['samples_per_gesture']):
            gesture_sequence.extend(self.GESTURES.copy())
        random.shuffle(gesture_sequence)

        session_start = time.time()

        try:
            for gesture in gesture_sequence:
                # Check if time limit exceeded
                elapsed_minutes = (time.time() - session_start) / 60
                if elapsed_minutes >= preset['duration_minutes']:
                    print("\n\nTime limit reached!")
                    break

                # Show gesture prompt with countdown
                for countdown in range(3, 0, -1):
                    self.display_gesture_prompt(gesture, countdown=countdown)
                    time.sleep(1)

                # Show collecting state
                self.display_gesture_prompt(gesture, collecting=True)

                # Collect data
                window_data = self.collect_window(preset['gesture_duration'])

                if window_data is not None and len(window_data) >= self.WINDOW_SIZE:
                    self.save_sample(window_data, gesture['name'])
                    samples_collected += 1
                    gesture_counts[gesture['name']] += 1

                    # Show progress
                    self.display_progress(samples_collected, total_samples_target, gesture_counts)
                    time.sleep(1)

                # Rest period
                rest_time = preset['rest_duration']
                rest_start = time.time()
                while time.time() - rest_start < rest_time:
                    seconds_left = rest_time - (time.time() - rest_start)
                    self.display_rest(seconds_left)
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nSession interrupted by user...")

        finally:
            self.save_summary(preset, gesture_counts)
            self.cleanup()

    def save_summary(self, preset, gesture_counts):
        """Save session summary"""
        summary_file = os.path.join(self.output_dir, "session_info.json")
        summary = {
            'session_name': self.session_name,
            'total_samples': sum(gesture_counts.values()),
            'gestures': gesture_counts,
            'window_size': self.WINDOW_SIZE,
            'num_channels': 4,
            'session_preset': preset['name'],
            'collection_date': datetime.now().isoformat()
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 80)
        print("SESSION COMPLETE!")
        print("=" * 80)
        print()
        print(f"Total samples collected: {sum(gesture_counts.values())}")
        print()
        print("Samples per gesture:")
        for gesture_name, count in sorted(gesture_counts.items()):
            print(f"  {gesture_name:10} - {count:3d} samples")
        print()
        print(f"Data saved to: {self.output_dir}/")
        print(f"Summary: {summary_file}")
        print()
        print("=" * 80)
        print()
        print("Next step: Run ./train_model.py to train your classifier!")

    def cleanup(self):
        """Clean up resources"""
        if self.streaming:
            self.stop_streaming()

        if self.connected and self.ser:
            self.ser.close()
            self.connected = False
            print("Connection closed")

def main():
    print("=" * 80)
    print("AUTOMATED EMG GESTURE DATA COLLECTION")
    print("=" * 80)
    print()

    collector = AutoGestureCollector()

    # List existing sessions
    training_data_dir = "training_data"
    if os.path.exists(training_data_dir):
        existing_sessions = [d for d in os.listdir(training_data_dir)
                           if os.path.isdir(os.path.join(training_data_dir, d))]
        if existing_sessions:
            print("Existing sessions:")
            for session in sorted(existing_sessions):
                session_info_file = os.path.join(training_data_dir, session, "session_info.json")
                if os.path.exists(session_info_file):
                    with open(session_info_file, 'r') as f:
                        info = json.load(f)
                        print(f"  - {session} ({info['total_samples']} samples, {info['collection_date'][:10]})")
                else:
                    print(f"  - {session}")
            print()

    # Get session name
    print("=" * 80)
    print("Session Name:")
    print("  Use a descriptive name (e.g., 'morning_session', 'electrodes_v1', 'john_seated')")
    print("  Default: Current timestamp will be used")
    print()
    session_name = input("Enter session name (or press Enter for timestamp): ").strip()

    if not session_name:
        # Use timestamp as default
        session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Using session name: {session_name}")

    print()
    print("=" * 80)
    print()
    print("Choose a session preset:")
    print()

    presets_list = [
        ('single', collector.PRESETS['single']),
        ('test', collector.PRESETS['test']),
        ('quick', collector.PRESETS['quick']),
        ('custom_fast', collector.PRESETS['custom_fast']),
        ('standard', collector.PRESETS['standard']),
        ('long', collector.PRESETS['long'])
    ]

    for i, (key, preset) in enumerate(presets_list, 1):
        print(f"  [{i}] {preset['name']}")
        print(f"      Duration: {preset['duration_minutes']} min | "
              f"Samples: {preset['samples_per_gesture']}/gesture | "
              f"Gesture: {preset['gesture_duration']}s | "
              f"Rest: {preset['rest_duration']}s")
        print()

    print("=" * 80)

    while True:
        choice = input("\nEnter choice (1-6): ").strip()
        if choice in ['1', '2', '3', '4', '5', '6']:
            preset_key = presets_list[int(choice) - 1][0]
            break
        print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

    collector.run_session(preset_key, session_name)

if __name__ == "__main__":
    main()
