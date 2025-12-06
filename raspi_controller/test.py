#!/usr/bin/env python3
"""
q8_keyboard_direct.py

Keyboard control of Q8 gait, talking straight to motor_server
(using the same pattern as keyboard_motor_debug_direct_simple.py).

Controls:
  w : forward
  a : turn left
  d : turn right
  s or SPACE : stop/idle
  q : quit
"""

import sys
import time
import termios
import tty
import select
import subprocess
import math
from typing import List, Dict

from q8_gait_controller import Q8GaitController

DXL_RESOLUTION = 1023.0
DXL_MAX_DEGREES = 300.0
CENTER_DEG = 150.0  # neutral pose

LOOP_HZ = 50.0
DT = 1.0 / LOOP_HZ


def deg_to_pos(deg: float) -> int:
    """Convert degrees (0–300) to Dynamixel position (0–1023)."""
    deg = max(0.0, min(DXL_MAX_DEGREES, deg))
    return int((deg / DXL_MAX_DEGREES) * DXL_RESOLUTION)


def _getch_with_timeout(timeout: float) -> str:
    """Single-char read from stdin with a timeout."""
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if not rlist:
        return ""
    return sys.stdin.read(1)


def main() -> None:
    motor_server_path = "../dynamixel_tools/motor_server"

    print(f"Starting motor_server at: {motor_server_path}")
    proc = subprocess.Popen(
        [motor_server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,   # discard motor_server output
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Q8 gait controller
    gait = Q8GaitController(default_gait="TROT")

    # Joint order must match what motor_server expects (IDs 1..8)
    joint_order: List[str] = [
        "front_left_leg_1",   # ID 1
        "front_left_leg_2",   # ID 2
        "back_left_leg_1",    # ID 3
        "back_left_leg_2",    # ID 4
        "back_right_leg_1",   # ID 5
        "back_right_leg_2",   # ID 6
        "front_right_leg_1",  # ID 7
        "front_right_leg_2",  # ID 8
    ]

    # Start in idle / neutral
    current_command = "idle"
    joint_targets: Dict[str, float] = {name: 0.0 for name in joint_order}

    print(
        "\n=== Q8 Keyboard Gait Control (DIRECT) ===\n"
        "Controls:\n"
        "  w : forward\n"
        "  a : turn left\n"
        "  d : turn right\n"
        "  s or SPACE : stop/idle\n"
        "  q : quit\n"
    )

    fd = sys.stdin.fileno()
    try:
        old_settings = termios.tcgetattr(fd)
    except termios.error:
        print("[q8_keyboard_direct] stdin is not a TTY; keyboard control may not work.")
        return

    def send_positions():
        # Convert radians -> deg -> Dynamixel pos in Q8 order
        pos_vals: List[int] = []
        for name in joint_order:
            angle_rad = joint_targets.get(name, 0.0)
            offset_deg = math.degrees(angle_rad)
            target_deg = CENTER_DEG + offset_deg
            pos_vals.append(deg_to_pos(target_deg))

        line = " ".join(str(p) for p in pos_vals) + "\n"
        try:
            assert proc.stdin is not None
            proc.stdin.write(line)
            proc.stdin.flush()
        except BrokenPipeError:
            print("motor_server exited unexpectedly.")

    try:
        tty.setcbreak(fd)

        last_time = time.time()

        while True:
            # Compute how much time left till next tick (DT)
            now = time.time()
            elapsed = now - last_time
            if elapsed < DT:
                # During the remaining time, we can wait for a key press
                ch = _getch_with_timeout(DT - elapsed)
            else:
                # No time left; don't block on keyboard
                ch = _getch_with_timeout(0.0)
            now = time.time()
            last_time = now

            if ch:
                if ch == "q":
                    print("Quitting Q8 gait debug.")
                    break
                elif ch == "w":
                    current_command = "forward"
                    print("[q8] command -> forward")
                elif ch == "a":
                    current_command = "turn_left"
                    print("[q8] command -> turn_left")
                elif ch == "d":
                    current_command = "turn_right"
                    print("[q8] command -> turn_right")
                elif ch == "s" or ch == " ":
                    current_command = "idle"
                    print("[q8] command -> idle")

            # Step the Q8 gait controller
            joint_targets = gait.step(DT, current_command)

            # Send updated joint positions
            send_positions()

    finally:
        # Restore terminal and stop motor_server
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass

        print("\nStopping motor_server...")
        if proc.stdin:
            try:
                proc.stdin.write("QUIT\n")
                proc.stdin.flush()
            except Exception:
                pass
        try:
            proc.wait(timeout=2.0)
        except Exception:
            pass
        print("motor_server stopped.")


if __name__ == "__main__":
    main()