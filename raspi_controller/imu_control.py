#!/usr/bin/env python3
"""
IMU-based control for quadruped robot using pitch and roll from wristband
"""

import sys
import os
import time
from typing import Optional

# Add wristband_control to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wristband_control', 'gesture_recognition'))

# Import IMU reader
from read_imu import IMUReader

from q8gait.kinematics_solver import k_solver
from q8gait.config_rx24f import default_config
from q8gait.robot import Robot
from q8gait.motion_runner import MotionRunner

CENTER_DIST = 30
L1 = 33
L2 = 44


class IMUInterface:
    """
    IMU-based gesture source (polled from main loop).

    Converts pitch and roll angles to quadruped movement gestures:
    - If |pitch| or |roll| > 30 degrees, choose the one with largest magnitude
    - Positive roll -> forward
    - Negative roll -> backward
    - Positive pitch -> turn_left
    - Negative pitch -> turn_right
    - If both < 30 degrees -> stop
    """

    def __init__(self, threshold: float = 30.0):
        self.threshold = threshold
        self._current_gesture: Optional[str] = "stop"
        self.imu_reader = IMUReader()

        # Connect to IMU
        if not self.imu_reader.connect():
            raise RuntimeError("Failed to connect to IMU")

        if not self.imu_reader.start_streaming():
            raise RuntimeError("Failed to start IMU streaming")

        print("\n[IMUInterface] IMU control enabled.")
        print(f"  Threshold: {threshold} degrees")
        print("  Positive roll -> forward")
        print("  Negative roll -> backward")
        print("  Positive pitch -> turn_left")
        print("  Negative pitch -> turn_right")
        print("  Below threshold -> stop")
        print()

        # Wait for data to stabilize
        print("Waiting for IMU data to stabilize...")
        time.sleep(2)
        print("Ready!\n")

    def poll(self) -> None:
        """Read latest IMU data and convert to gesture"""
        # Read all available packets
        packets = self.imu_reader.read_packets()

        if not packets:
            return

        # Use the most recent packet
        latest = packets[-1]

        if 'aux' in latest and len(latest['aux']) >= 3:
            self.imu_reader.accel_x = latest['aux'][0]
            self.imu_reader.accel_y = latest['aux'][1]
            self.imu_reader.accel_z = latest['aux'][2]

            # Calculate orientation
            self.imu_reader.calculate_orientation(
                self.imu_reader.accel_x,
                self.imu_reader.accel_y,
                self.imu_reader.accel_z
            )

            # Convert to gesture
            self._update_gesture()

    def _update_gesture(self) -> None:
        """
        Convert pitch and roll to gesture based on threshold logic
        """
        pitch = self.imu_reader.pitch
        roll = self.imu_reader.roll

        # Get absolute values
        abs_pitch = abs(pitch)
        abs_roll = abs(roll)

        # Check if either exceeds threshold
        if abs_pitch < self.threshold and abs_roll < self.threshold:
            # Both below threshold -> stop
            new_gesture = "stop"
        else:
            # Choose the one with largest magnitude
            if abs_pitch > abs_roll:
                # Pitch dominates
                if pitch > 0:
                    new_gesture = "turn_left"
                else:
                    new_gesture = "turn_right"
            else:
                # Roll dominates
                if roll > 0:
                    new_gesture = "forward"
                else:
                    new_gesture = "backward"

        # Update gesture if changed
        if new_gesture != self._current_gesture:
            print(f"[IMUInterface] Pitch: {pitch:6.2f}°, Roll: {roll:6.2f}° -> {new_gesture}")
            self._current_gesture = new_gesture

    def read_gesture(self) -> Optional[str]:
        """Return current gesture"""
        return self._current_gesture

    def close(self) -> None:
        """Clean up IMU resources"""
        if self.imu_reader:
            self.imu_reader.cleanup()


def main():
    """Main control loop using IMU interface"""
    print("=" * 80)
    print("IMU-Based Quadruped Control")
    print("=" * 80)
    print()
    print("This script uses wristband IMU data to control the quadruped robot.")
    print("Tilt your wrist to control movement:")
    print("  - Roll forward/backward to move forward/backward")
    print("  - Pitch left/right to turn left/right")
    print("  - Keep wrist level to stop")
    print()
    input("Press Enter to start...")
    print()

    # Initialize robot
    cfg = default_config()
    robot = Robot(cfg)
    leg = k_solver(CENTER_DIST, L1, L2, L1, L2)

    # Initialize IMU interface
    imu = IMUInterface(threshold=30.0)

    try:
        robot.open()
        robot.torque(True)

        runner = MotionRunner(robot, leg, gait_name="TROT_LOW", hz=50)
        runner.move_to_neutral(seconds=1.0)

        print("\n" + "=" * 80)
        print("ROBOT READY - Control with wrist movements!")
        print("=" * 80)
        print()

        # Main control loop
        runner.loop_forever(imu)

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        try:
            robot.torque(False)
        finally:
            robot.close()
            imu.close()


if __name__ == "__main__":
    main()
