from __future__ import annotations
import time
from typing import Optional

from .gait_manager import GaitManager, GAITS
from .kinematics_solver import k_solver
from .robot import Robot

GESTURE_TO_DIR = {
    "forward": "f",
    "backward": "b",
    "turn_left": "l",
    "turn_right": "r",
    "stop": None,
    # Jump gestures with directional support
    "jump": "in_place",  # Default jump is in-place
    "jump_forward": "f",
    "jump_backward": "b",
    "jump_left": "l",
    "jump_right": "r",
}

class MotionRunner:
    def __init__(self, robot: Robot, leg_solver: k_solver, gait_name: str = "TROT", hz: int = 10,
                 neutral_center_deg: float = 150.0, custom_gaits: Optional[dict] = None):
        self.robot = robot
        self.leg = leg_solver
        self.hz = hz
        self.dt = 1.0 / hz
        self.neutral_center_deg = neutral_center_deg
        self.normal_speed = 0
        self.normal_torque = 600

        # Use custom gaits if provided, otherwise use default GAITS
        gaits = custom_gaits if custom_gaits is not None else GAITS
        self.gaits = gaits

        self.gait_manager = GaitManager(self.leg, gaits)
        if not self.gait_manager.load_gait(gait_name):
            raise RuntimeError(f"Failed to load gait {gait_name}")

        self.gait_name = gait_name
        self.current_dir: Optional[str] = None
        self.is_jumping = False  # Track if we're currently in a jump

        _, x0, y0, *_ = gaits[gait_name]
        self.neutral_x = x0 # x0 foot location
        self.neutral_y = y0 # y0 how tall it stands

        q1n, q2n, ok = self.leg.ik_solve(self.neutral_x, self.neutral_y, True, 3)
        if not ok:
            raise RuntimeError("IK failed for neutral pose.")
        self.q_neutral = [q1n, q2n, q1n, q2n, q1n, q2n, q1n, q2n]

    def _recenter_to_150(self, q_abs_8):
        out = []
        for i in range(8):
            out.append(self.neutral_center_deg + (q_abs_8[i] - self.q_neutral[i]))
        return out

    def move_to_neutral(self, seconds: float = 1.0) -> None:
        cmd = [self.neutral_center_deg] * 8
        n = max(1, int(seconds * self.hz))
        for _ in range(n):
            self.robot.write_positions_deg(cmd)
            time.sleep(self.dt)

    def do_jump(self, direction: str = "in_place") -> None:
        """
        Execute a jump in the specified direction.

        Args:
            direction: Jump direction ('in_place', 'f', 'b', 'l', 'r')
        """
        # Save current gait state
        saved_gait = self.gait_name

        # Stop current movement
        self.gait_manager.stop()
        self.current_dir = None

        # Determine which jump gait to use based on direction
        if direction == "f":
            jump_gait = "JUMP_FORWARD"
        elif direction == "b":
            jump_gait = "JUMP_BACKWARD"
        else:
            jump_gait = "JUMP"  # For in_place, left, right - use base JUMP

        print(f"[MotionRunner] Executing {jump_gait} in direction '{direction}'")

        # Load the jump gait
        if not self.gait_manager.load_gait(jump_gait):
            print(f"[MotionRunner] Failed to load jump gait {jump_gait}")
            return

        # Start the jump movement
        if not self.gait_manager.start_movement(direction):
            print(f"[MotionRunner] Failed to start jump movement in direction '{direction}'")
            self.gait_manager.load_gait(saved_gait)
            return

        self.is_jumping = True
        self.current_dir = direction

        # Calculate number of ticks for complete jump cycle
        jump_params = self.gaits[jump_gait]
        s1_count, s2_count = jump_params[6], jump_params[7]
        total_jump_ticks = s1_count + s2_count

        # Execute the jump for one complete cycle
        for _ in range(total_jump_ticks):
            q_abs = self.gait_manager.tick()
            if q_abs is not None:
                cmd = self._recenter_to_150(q_abs)
                self.robot.write_positions_deg(cmd)
            time.sleep(self.dt)

        # Stop the jump and restore the original gait
        self.gait_manager.stop()
        self.is_jumping = False
        self.current_dir = None

        # Reload the saved gait
        if not self.gait_manager.load_gait(saved_gait):
            print(f"[MotionRunner] Failed to restore gait {saved_gait}")

        print(f"[MotionRunner] Jump complete, restored to {saved_gait}")

        # Return to neutral position after jump
        self.move_to_neutral(0.5)

    def set_gesture(self, gesture: Optional[str]) -> None:
        if gesture is None:
            return

        # Handle jump gestures separately
        if gesture in ("jump", "jump_forward", "jump_backward", "jump_left", "jump_right"):
            direction = GESTURE_TO_DIR.get(gesture, "in_place")
            self.do_jump(direction)
            return

        if gesture in ("forward", "backward", "turn_left", "turn_right"):
            self.robot.set_torque_limit_all(self.normal_torque)
            self.robot.set_moving_speed_all(self.normal_speed)

        direction = GESTURE_TO_DIR.get(gesture, None)

        if direction is None:
            self.gait_manager.stop()
            self.current_dir = None
            return

        if self.gait_manager.start_movement(direction):
            self.current_dir = direction
        else:
            self.gait_manager.stop()
            self.current_dir = None

    def tick(self) -> None:
        q_abs = self.gait_manager.tick()

        if q_abs is None:
            self.robot.write_positions_deg([self.neutral_center_deg] * 8)
            return
        cmd = self._recenter_to_150(q_abs)
        self.robot.write_positions_deg(cmd)
    
    def loop_forever(self, keyboard_interface) -> None:
        next_t = time.perf_counter()
        last_gesture = None

        while True:
            keyboard_interface.poll()
            gesture = keyboard_interface.read_gesture()

            if gesture != last_gesture and gesture is not None:
                self.set_gesture(gesture)
                last_gesture = gesture

            now = time.perf_counter()
            if now >= next_t:
                self.tick()
                next_t += self.dt
            else:
                time.sleep(max(0.0, next_t - now))
