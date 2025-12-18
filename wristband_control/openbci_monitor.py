#!/usr/bin/env python3
"""
OpenBCI Cyton Board Monitor
Real-time connection status and data display for OpenBCI Cyton 16-channel board
"""

import serial
import serial.tools.list_ports
import time
import sys
import struct
from datetime import datetime

class OpenBCIMonitor:
    def __init__(self):
        self.ser = None
        self.connected = False
        self.streaming = False
        self.packet_count = 0
        self.error_count = 0

        # OpenBCI Cyton settings
        self.BAUD_RATE = 115200
        self.TIMEOUT = 1

        # Packet format for 16-channel board (Cyton + Daisy)
        self.SAMPLE_RATE = 250  # Hz

        # Ports to exclude (used by other devices like Dynamixel motors)
        self.EXCLUDED_PORTS = ['/dev/ttyUSB1']

    def clear_screen(self):
        """Clear terminal screen"""
        print("\033[2J\033[H", end="")

    def print_status(self, message, status_type="INFO"):
        """Print timestamped status message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        symbols = {
            "INFO": "ℹ",
            "SUCCESS": "✓",
            "ERROR": "✗",
            "WARNING": "⚠",
            "DATA": "→"
        }
        symbol = symbols.get(status_type, "•")
        print(f"[{timestamp}] {symbol} {message}")

    def find_openbci_port(self):
        """Scan for OpenBCI board on serial ports"""
        self.print_status("Scanning for OpenBCI board...", "INFO")

        ports = list(serial.tools.list_ports.comports())

        if not ports:
            self.print_status("No serial ports found!", "ERROR")
            return None

        print(f"\nFound {len(ports)} serial port(s):")
        for i, port in enumerate(ports):
            excluded_marker = " [EXCLUDED - Dynamixel]" if port.device in self.EXCLUDED_PORTS else ""
            print(f"  [{i}] {port.device}{excluded_marker}")
            print(f"      Description: {port.description}")
            print(f"      Hardware ID: {port.hwid}")

        # Filter out excluded ports
        available_ports = [p for p in ports if p.device not in self.EXCLUDED_PORTS]

        if not available_ports:
            self.print_status("No available ports (all are excluded)!", "ERROR")
            return None

        # Try common OpenBCI ports first (excluding the excluded ones)
        common_ports = ['/dev/ttyUSB0', '/dev/ttyACM0']

        for port_name in common_ports:
            for port in available_ports:
                if port.device == port_name:
                    self.print_status(f"Trying {port_name}...", "INFO")
                    return port_name

        # If no common port found, try the first available (non-excluded)
        if available_ports:
            port_name = available_ports[0].device
            self.print_status(f"Trying {port_name}...", "INFO")
            return port_name

        return None

    def connect(self, port=None):
        """Connect to OpenBCI board"""
        if port is None:
            port = self.find_openbci_port()

        if port is None:
            self.print_status("No suitable port found", "ERROR")
            return False

        try:
            self.print_status(f"Connecting to {port} at {self.BAUD_RATE} baud...", "INFO")

            self.ser = serial.Serial(
                port=port,
                baudrate=self.BAUD_RATE,
                timeout=self.TIMEOUT,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )

            # Wait for board to initialize
            time.sleep(2)

            # Flush any existing data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            self.connected = True
            self.print_status(f"Connected to {port}", "SUCCESS")

            # Try to get board info
            self.get_board_info()

            return True

        except serial.SerialException as e:
            self.print_status(f"Connection failed: {e}", "ERROR")
            self.connected = False
            return False

    def get_board_info(self):
        """Request board information"""
        try:
            self.print_status("Requesting board information...", "INFO")

            # Send soft reset first
            self.ser.write(b'v')
            time.sleep(0.5)

            # Read response
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting)
                info = response.decode('utf-8', errors='ignore').strip()
                if info:
                    self.print_status(f"Board info: {info}", "SUCCESS")
                    return info
            else:
                self.print_status("No response from board", "WARNING")

        except Exception as e:
            self.print_status(f"Error getting board info: {e}", "ERROR")

        return None

    def start_streaming(self):
        """Start data streaming"""
        if not self.connected:
            self.print_status("Not connected to board", "ERROR")
            return False

        try:
            self.print_status("Starting data stream...", "INFO")
            self.ser.write(b'b')  # Start streaming command
            time.sleep(0.1)
            self.streaming = True
            self.print_status("Streaming started", "SUCCESS")
            return True

        except Exception as e:
            self.print_status(f"Error starting stream: {e}", "ERROR")
            return False

    def stop_streaming(self):
        """Stop data streaming"""
        if not self.connected:
            return

        try:
            self.print_status("Stopping data stream...", "INFO")
            self.ser.write(b's')  # Stop streaming command
            time.sleep(0.1)
            self.streaming = False
            self.print_status("Streaming stopped", "SUCCESS")

        except Exception as e:
            self.print_status(f"Error stopping stream: {e}", "ERROR")

    def read_data(self):
        """Read and display incoming data"""
        if not self.connected:
            return

        try:
            if self.ser.in_waiting > 0:
                # Read available data
                data = self.ser.read(self.ser.in_waiting)

                if len(data) > 0:
                    self.packet_count += 1

                    # Display data info every 10 packets to avoid spam
                    if self.packet_count % 10 == 0:
                        hex_preview = ' '.join([f'{b:02x}' for b in data[:16]])
                        if len(data) > 16:
                            hex_preview += "..."

                        self.print_status(
                            f"Packet #{self.packet_count} | {len(data)} bytes | {hex_preview}",
                            "DATA"
                        )

        except Exception as e:
            self.error_count += 1
            self.print_status(f"Read error: {e}", "ERROR")

    def monitor_loop(self):
        """Main monitoring loop"""
        self.clear_screen()
        print("=" * 70)
        print("OpenBCI Cyton 16-Channel Monitor")
        print("=" * 70)
        print()

        # Connect to board
        if not self.connect():
            return

        print()
        print("-" * 70)
        print("Press Ctrl+C to stop")
        print("-" * 70)
        print()

        # Start streaming
        self.start_streaming()

        try:
            last_status_time = time.time()

            while True:
                # Read data
                self.read_data()

                # Print periodic status update every 5 seconds
                if time.time() - last_status_time > 5:
                    self.print_status(
                        f"Status: {'Connected' if self.connected else 'Disconnected'} | "
                        f"Streaming: {'Yes' if self.streaming else 'No'} | "
                        f"Packets: {self.packet_count} | "
                        f"Errors: {self.error_count}",
                        "INFO"
                    )
                    last_status_time = time.time()

                time.sleep(0.01)  # Small delay to prevent CPU spinning

        except KeyboardInterrupt:
            print("\n")
            self.print_status("Shutting down...", "INFO")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.streaming:
            self.stop_streaming()

        if self.connected and self.ser:
            self.print_status("Closing connection...", "INFO")
            self.ser.close()
            self.connected = False
            self.print_status("Connection closed", "SUCCESS")

        print()
        print(f"Session summary:")
        print(f"  Total packets received: {self.packet_count}")
        print(f"  Total errors: {self.error_count}")
        print()

def main():
    monitor = OpenBCIMonitor()
    monitor.monitor_loop()

if __name__ == "__main__":
    main()
