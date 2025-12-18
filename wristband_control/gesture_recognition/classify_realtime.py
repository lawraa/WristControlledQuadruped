#!/usr/bin/env python3
"""
Real-time EMG Gesture Classifier
Uses trained model to classify gestures in real-time
"""

import serial
import serial.tools.list_ports
import time
import numpy as np
from collections import deque
from datetime import datetime
import joblib
import os

class RealtimeGestureClassifier:
    def __init__(self, model_path="models/gesture_model.pkl"):
        self.ser = None
        self.connected = False
        self.streaming = False

        # Settings
        self.BAUD_RATE = 115200
        self.TIMEOUT = 1
        self.EXCLUDED_PORTS = ['/dev/ttyUSB0']

        # Load trained model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}\nRun a train_model script first!")

        print(f"Loading model from {model_path}...")
        model_data = joblib.load(model_path)
        self.model = model_data['model']
        self.scaler = model_data.get('scaler', None)  # SVM/LDA use scaler
        self.gestures = model_data['gestures']
        self.feature_type = model_data.get('feature_type', 'default')
        self.method = model_data.get('method', 'Unknown')
        print(f"✓ Model loaded: {self.method}")
        print(f"  Gestures: {self.gestures}")
        print(f"  Feature type: {self.feature_type}")

        # Packet parsing
        self.start_byte = 0xA0
        self.end_byte = 0xC0
        self.packet_buffer = bytearray()

        # Sliding window for classification
        self.WINDOW_SIZE = 200  # Same as training
        self.window_buffer = deque(maxlen=self.WINDOW_SIZE)

        # Classification output
        self.current_gesture = "unknown"
        self.gesture_confidence = 0.0
        self.classification_count = 0

        # Gesture history for smoothing
        self.gesture_history = deque(maxlen=5)

        # Quadruped command mapping
        self.COMMAND_MAP = {
            'forward': '↑ FORWARD',
            'backward': '↓ BACKWARD',
            'left': '← LEFT',
            'right': '→ RIGHT',
            'stop': '■ STOP',
            'jump': '⤊ JUMP'
        }

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
            if port.device in ['/dev/ttyUSB1', '/dev/ttyACM0']:
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
            channels[0],  # N1P
            channels[1],  # N2P
            channels[4],  # N5P
            channels[5],  # N6P
        ]

        return pairs

    def extract_features(self, window_data):
        """Extract features from window (matches training method)"""
        if self.feature_type == 'MAV':
            return self.extract_features_mav(window_data)
        elif self.feature_type == 'time_domain':
            return self.extract_features_time_domain(window_data)
        else:
            return self.extract_features_default(window_data)

    def extract_features_default(self, window_data):
        """Default feature extraction (Random Forest)"""
        features = []
        num_channels = window_data.shape[1]

        for ch in range(num_channels):
            channel_data = window_data[:, ch]

            # RMS
            rms = np.sqrt(np.mean(channel_data**2))

            # MAV
            mav = np.mean(np.abs(channel_data))

            # Waveform Length
            wl = np.sum(np.abs(np.diff(channel_data)))

            # Zero Crossings
            threshold = 0.01 * np.max(np.abs(channel_data))
            zc = np.sum(np.diff(np.sign(channel_data)) != 0)

            # Variance
            var = np.var(channel_data)

            features.extend([rms, mav, wl, zc, var])

        return np.array(features)

    def extract_features_mav(self, window_data):
        """MAV feature extraction (SVM)"""
        features = []
        num_channels = window_data.shape[1]

        for ch in range(num_channels):
            channel_data = window_data[:, ch]

            # Mean Absolute Value
            mav = np.mean(np.abs(channel_data))

            # Root Mean Square
            rms = np.sqrt(np.mean(channel_data**2))

            # Variance
            var = np.var(channel_data)

            features.extend([mav, rms, var])

        return np.array(features)

    def extract_features_time_domain(self, window_data):
        """Time-domain feature extraction (LDA)"""
        features = []
        num_channels = window_data.shape[1]

        for ch in range(num_channels):
            channel_data = window_data[:, ch]

            # MAV
            mav = np.mean(np.abs(channel_data))

            # RMS
            rms = np.sqrt(np.mean(channel_data**2))

            # Waveform Length
            wl = np.sum(np.abs(np.diff(channel_data)))

            # Zero Crossings
            threshold = 0.01 * np.max(np.abs(channel_data)) if np.max(np.abs(channel_data)) > 0 else 0.01
            zc = np.sum(np.diff(np.sign(channel_data)) != 0)

            # Slope Sign Changes
            diff_signal = np.diff(channel_data)
            ssc = np.sum(np.diff(np.sign(diff_signal)) != 0)

            # Variance
            var = np.var(channel_data)

            # Integrated EMG
            iemg = np.sum(np.abs(channel_data))

            # Willison Amplitude
            wa_threshold = 0.01 * np.max(np.abs(channel_data)) if np.max(np.abs(channel_data)) > 0 else 0.01
            wa = np.sum(np.abs(np.diff(channel_data)) > wa_threshold)

            features.extend([mav, rms, wl, zc, ssc, var, iemg, wa])

        return np.array(features)

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

    def classify_gesture(self):
        """Classify current window"""
        if len(self.window_buffer) < self.WINDOW_SIZE:
            return None, 0.0

        # Convert to numpy array
        window_data = np.array(self.window_buffer)

        # Extract features
        features = self.extract_features(window_data)

        # Scale features if scaler is available (for SVM/LDA)
        if self.scaler is not None:
            features = self.scaler.transform([features])[0]
            prediction = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0]
        else:
            prediction = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0]

        confidence = np.max(probabilities)

        return prediction, confidence

    def smooth_prediction(self, gesture):
        """Smooth predictions using history"""
        self.gesture_history.append(gesture)

        if len(self.gesture_history) < 3:
            return gesture

        # Use majority vote from last 5 predictions
        unique, counts = np.unique(list(self.gesture_history), return_counts=True)
        return unique[np.argmax(counts)]

    def display_status(self):
        """Display current classification status"""
        self.clear_screen()

        print("=" * 80)
        print("Real-time EMG Gesture Classifier - Quadruped Control")
        print("=" * 80)
        print()
        print(f"Status: {'Connected' if self.connected else 'Disconnected'} | "
              f"Streaming: {'Yes' if self.streaming else 'No'} | "
              f"Classifications: {self.classification_count}")
        print()
        print("-" * 80)

        # Current gesture
        command = self.COMMAND_MAP.get(self.current_gesture, "UNKNOWN")
        confidence_bar = "█" * int(self.gesture_confidence * 50)

        print()
        print(f"  DETECTED GESTURE: {command}")
        print(f"  Confidence: [{confidence_bar:<50}] {self.gesture_confidence:.1%}")
        print()

        print("-" * 80)
        print()
        print("Gesture Guide:")
        print("  FORWARD  → Wrist extension (hand up)")
        print("  BACKWARD → Wrist flexion (hand down)")
        print("  LEFT     → Ulnar deviation (toward pinky)")
        print("  RIGHT    → Radial deviation (toward thumb)")
        print("  STOP     → Rest/neutral position")
        print("  JUMP     → Spread fingers wide")
        print()
        print("-" * 80)
        print("Buffer: " + ("█" * int(len(self.window_buffer) / self.WINDOW_SIZE * 50)))
        print()
        print("Press Ctrl+C to exit")

    def run(self):
        """Main classification loop"""
        self.clear_screen()
        print("Starting Real-time Gesture Classifier...\n")

        if not self.connect():
            return

        if not self.start_streaming():
            return

        print("\nWaiting for data stream to stabilize...")
        time.sleep(2)

        try:
            last_update = time.time()
            update_interval = 0.1  # Update display 10 times per second

            while True:
                # Read packets continuously
                pairs = self.read_packet()
                if pairs is not None:
                    self.window_buffer.append(pairs)

                    # Classify when window is full
                    if len(self.window_buffer) == self.WINDOW_SIZE:
                        gesture, confidence = self.classify_gesture()

                        if gesture is not None:
                            # Smooth prediction
                            smoothed_gesture = self.smooth_prediction(gesture)

                            self.current_gesture = smoothed_gesture
                            self.gesture_confidence = confidence
                            self.classification_count += 1

                # Update display periodically
                if time.time() - last_update > update_interval:
                    self.display_status()
                    last_update = time.time()

                time.sleep(0.001)

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
        print(f"  Total classifications: {self.classification_count}")

def main():
    print("=" * 80)
    print("Real-time EMG Gesture Classifier")
    print("=" * 80)
    print()

    # List available models
    models_dir = "models"
    if not os.path.exists(models_dir):
        print("Error: No models directory found!")
        print("Run a train_model script first.")
        return

    available_models = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]

    if not available_models:
        print("Error: No models found!")
        print("Run a train_model script first (train_model.py, train_model_svm.py, etc.)")
        return

    print("Available models:")
    print()
    for i, model in enumerate(sorted(available_models), 1):
        model_path = os.path.join(models_dir, model)
        try:
            model_data = joblib.load(model_path)
            method = model_data.get('method', 'Unknown')
            n_samples = model_data.get('n_samples', 'Unknown')
            date = model_data.get('training_date', 'Unknown')
            if date != 'Unknown' and 'T' in date:
                date = date.split('T')[0]
            print(f"  [{i}] {model}")
            print(f"      Method: {method}")
            print(f"      Samples: {n_samples} | Date: {date}")
        except:
            print(f"  [{i}] {model} (could not load metadata)")
        print()

    print("=" * 80)
    print()

    # Get user selection
    choice = input("Select model to use (default=1): ").strip()

    if choice == "":
        choice = "1"

    if not choice.isdigit():
        print("Error: Invalid selection!")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(available_models):
        print("Error: Invalid selection!")
        return

    selected_model = sorted(available_models)[idx]
    model_path = os.path.join(models_dir, selected_model)

    print()
    print(f"Using model: {selected_model}")
    print()
    input("Press Enter to start classification...")

    classifier = RealtimeGestureClassifier(model_path=model_path)
    classifier.run()

if __name__ == "__main__":
    main()
