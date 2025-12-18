#!/usr/bin/env python3
"""
Read IMU data from OpenBCI Cyton board and display yaw, pitch, roll
"""

import serial
import serial.tools.list_ports
import time
import numpy as np
import math

class IMUReader:
    def __init__(self):
        self.ser = None
        self.connected = False
        self.streaming = False

        # Settings
        self.BAUD_RATE = 115200
        self.TIMEOUT = 1
        self.EXCLUDED_PORTS = ['/dev/ttyUSB0']

        # Packet parsing
        self.start_byte = 0xA0
        self.end_byte = 0xC0
        self.packet_buffer = bytearray()

        # IMU data
        self.accel_x = 0
        self.accel_y = 0
        self.accel_z = 0
        self.gyro_x = 0
        self.gyro_y = 0
        self.gyro_z = 0

        # Orientation
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

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
            print("✗ No available port found")
            return False

        try:
            print(f"Connecting to {port}...")
            self.ser = serial.Serial(
                port=port,
                baudrate=self.BAUD_RATE,
                timeout=self.TIMEOUT
            )
            time.sleep(2)
            self.ser.reset_input_buffer()
            self.connected = True
            print(f"✓ Connected to {port}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def start_streaming(self):
        """Start data stream"""
        if not self.connected:
            return False

        try:
            # Start streaming
            self.ser.write(b'b')
            time.sleep(0.1)
            self.streaming = True
            print("✓ Streaming started")
            return True
        except Exception as e:
            print(f"✗ Failed to start streaming: {e}")
            return False

    def stop_streaming(self):
        """Stop data stream"""
        if self.connected and self.streaming:
            try:
                self.ser.write(b's')
                time.sleep(0.1)
                self.streaming = False
                print("✓ Streaming stopped")
            except Exception as e:
                print(f"✗ Error stopping stream: {e}")

    def parse_packet(self, packet):
        """Parse OpenBCI data packet including auxiliary data"""
        if len(packet) != 33:
            return None

        if packet[0] != self.start_byte:
            return None

        # Parse EEG channels (not used here, but maintain structure)
        channels = []
        for i in range(8):
            offset = 2 + (i * 3)
            val = (packet[offset] << 16) | (packet[offset+1] << 8) | packet[offset+2]
            if val >= 0x800000:
                val -= 0x1000000
            channels.append(val)

        # Parse auxiliary data (bytes 26-31)
        # The Cyton board auxiliary data contains accelerometer values
        # Format: 2 bytes per axis (X, Y, Z) as signed 16-bit integers
        aux_data = []
        for i in range(3):  # 3 axes
            offset = 26 + (i * 2)
            val = (packet[offset] << 8) | packet[offset+1]
            # Convert to signed 16-bit
            if val >= 0x8000:
                val -= 0x10000
            aux_data.append(val)

        if packet[32] != self.end_byte:
            return None

        return {
            'channels': channels,
            'aux': aux_data  # [accel_x, accel_y, accel_z] or [gyro_x, gyro_y, gyro_z]
        }

    def read_packets(self):
        """Read and parse all available packets"""
        packets = []

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
                    parsed = self.parse_packet(packet)

                    if parsed is not None:
                        packets.append(parsed)

                    self.packet_buffer = self.packet_buffer[33:]

        except Exception as e:
            print(f"Exception in read_packets: {e}")

        return packets

    def calculate_orientation(self, accel_x, accel_y, accel_z):
        """Calculate roll, pitch, yaw from accelerometer data"""
        # Convert to g's (assuming range is ±4g for OpenBCI)
        # Scale factor depends on accelerometer configuration
        scale = 0.002  # Approximate scale factor

        ax = accel_x * scale
        ay = accel_y * scale
        az = accel_z * scale

        # Calculate roll (rotation around X-axis)
        self.roll = math.atan2(ay, az) * 180.0 / math.pi

        # Calculate pitch (rotation around Y-axis)
        self.pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 180.0 / math.pi

        # Yaw cannot be determined from accelerometer alone (needs magnetometer)
        # For now, we'll leave it at 0 or use gyro integration if available
        self.yaw = 0

    def clear_screen(self):
        """Clear terminal screen"""
        print("\033[2J\033[H", end="")

    def display_imu_data(self):
        """Display IMU data on screen"""
        self.clear_screen()

        print("=" * 70)
        print("IMU DATA - OpenBCI Cyton Board")
        print("=" * 70)
        print()
        print(f"  Roll:  {self.roll:7.2f}°  {'|' * int(abs(self.roll/5))}")
        print(f"  Pitch: {self.pitch:7.2f}°  {'|' * int(abs(self.pitch/5))}")
        print(f"  Yaw:   {self.yaw:7.2f}°  {'|' * int(abs(self.yaw/5))}")
        print()
        print("  Raw Accelerometer:")
        print(f"    X: {self.accel_x:6d}")
        print(f"    Y: {self.accel_y:6d}")
        print(f"    Z: {self.accel_z:6d}")
        print()
        print("=" * 70)
        print("Press Ctrl+C to stop")

    def run(self):
        """Main loop to read and display IMU data"""
        if not self.connect():
            return

        if not self.start_streaming():
            return

        print("\nWaiting for data stream to stabilize...")
        time.sleep(2)

        print("\nReading IMU data...\n")

        try:
            while True:
                packets = self.read_packets()

                if packets:
                    # Use the most recent packet
                    latest = packets[-1]

                    if 'aux' in latest and len(latest['aux']) >= 3:
                        self.accel_x = latest['aux'][0]
                        self.accel_y = latest['aux'][1]
                        self.accel_z = latest['aux'][2]

                        # Calculate orientation
                        self.calculate_orientation(
                            self.accel_x,
                            self.accel_y,
                            self.accel_z
                        )

                        # Display
                        self.display_imu_data()

                time.sleep(0.05)  # Update at ~20Hz

        except KeyboardInterrupt:
            print("\n\nStopping...")

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

def main():
    print("=" * 70)
    print("OpenBCI IMU Reader")
    print("=" * 70)
    print()
    print("This will display real-time orientation data from the Cyton board")
    print()
    input("Press Enter to start...")

    reader = IMUReader()
    reader.run()

if __name__ == "__main__":
    main()
