#!/usr/bin/env python3
"""
test_motor_mapping.py

Small utility to figure out which physical joint corresponds to each
Dynamixel ID (1..8) / index (0..7) in motor_server's order.

Usage:
    cd raspi_controller
    python test_motor_mapping.py

For each index, it will:
  - Center all joints
  - Wiggle one joint (ID = index+1) back and forth a few times
  - Ask you to note which physical joint moved
"""

import subprocess
import time

# These match the RobotInterface / Dynamixel setup
DXL_RESOLUTION = 1023.0
DXL_MAX_DEGREES = 300.0
CENTER_DEG = 150.0  # neutral = mid of 0–300°


def deg_to_pos(deg: float) -> int:
    """Convert degrees (0–300) to Dynamixel position (0–1023)."""
    deg = max(0.0, min(DXL_MAX_DEGREES, deg))
    return int((deg / DXL_MAX_DEGREES) * DXL_RESOLUTION)


def main() -> None:
    # Path to motor_server relative to raspi_controller/
    motor_server_path = "../dynamixel_tools/motor_server"

    print(f"Starting motor_server at: {motor_server_path}")
    proc = subprocess.Popen(
        [motor_server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        # Base (neutral) position for all joints
        base_deg = CENTER_DEG
        base_pos = deg_to_pos(base_deg)
        joint_positions = [base_pos] * 8

        print(
            "\n=== Motor Mapping Test ===\n"
            "For each step:\n"
            "  - Press Enter to start testing that index.\n"
            "  - Watch which physical joint moves.\n"
            "  - Write down something like: index 0 (ID 1) = front_left_leg_1.\n"
        )

        # Give motors a moment to torque on & settle
        print("Centering all 8 motors first...")
        line = " ".join(str(p) for p in joint_positions) + "\n"
        proc.stdin.write(line)
        proc.stdin.flush()
        time.sleep(2.0)

        for idx in range(8):
            motor_id = idx + 1
            input(f"\nPress Enter to test index {idx} (Dynamixel ID {motor_id})...")

            print("  Centering all joints...")
            joint_positions = [base_pos] * 8
            line = " ".join(str(p) for p in joint_positions) + "\n"
            proc.stdin.write(line)
            proc.stdin.flush()
            time.sleep(1.0)

            print("  Wiggling this motor (watch the robot!)...")
            # Wiggle this joint a few times
            for cycle in range(3):
                # Move a bit positive
                joint_positions[idx] = deg_to_pos(base_deg + 20.0)
                line = " ".join(str(p) for p in joint_positions) + "\n"
                proc.stdin.write(line)
                proc.stdin.flush()
                time.sleep(0.7)

                # Move a bit negative
                joint_positions[idx] = deg_to_pos(base_deg - 20.0)
                line = " ".join(str(p) for p in joint_positions) + "\n"
                proc.stdin.write(line)
                proc.stdin.flush()
                time.sleep(0.7)

            # Return to center
            joint_positions[idx] = base_pos
            line = " ".join(str(p) for p in joint_positions) + "\n"
            proc.stdin.write(line)
            proc.stdin.flush()
            time.sleep(0.5)

            print(
                f"  >>> Record which physical joint moved for index {idx} (ID {motor_id})."
            )

        print("\n=== Test complete! ===")
        print(
            "Now you should have a mapping like:\n"
            "  index 0 (ID 1) = ???\n"
            "  index 1 (ID 2) = ???\n"
            "  ...\n"
            "Send me that mapping and we’ll update the joint_order in RobotInterface."
        )

    finally:
        print("\nStopping motor_server...")
        if proc.stdin:
            try:
                proc.stdin.write("QUIT\n")
                proc.stdin.flush()
            except BrokenPipeError:
                pass
        try:
            proc.wait(timeout=2.0)
        except Exception:
            pass
        print("motor_server stopped.")


if __name__ == "__main__":
    main()
