# q8gait/motion_runner.py

from __future__ import annotations
import time
from typing import Optional

from .gait_manager import GaitManager, GAITS
from .kinematics_solver import k_solver
from .robot_rx24f import RX24FRobot


GESTURE_TO_DIR = {
    "forward": "f",
    "backward": "b",
    "turn_left": "l",
    "turn_right": "r",
    "stop": None,
}


class MotionRunner:
    def __init__(self, robot: RX24FRobot, leg_solver: k_solver, gait_name: str = "TROT", hz: int = 10,
                 neutral_center_deg: float = 150.0):
        self.robot = robot
        self.leg = leg_solver
        self.hz = hz
        self.dt = 1.0 / hz
        self.neutral_center_deg = neutral_center_deg
        self.normal_speed = 0
        self.normal_torque = 1023
        self.gait_manager = GaitManager(self.leg, GAITS)
        if not self.gait_manager.load_gait(gait_name):
            raise RuntimeError(f"Failed to load gait {gait_name}")

        self.gait_name = gait_name
        self.current_dir: Optional[str] = None

        _, x0, y0, *_ = GAITS[gait_name]
        self.neutral_x = x0 # x0 foot location
        self.neutral_y = y0 # y0 how tall it stands

        q1n, q2n, ok = self.leg.ik_solve(self.neutral_x, self.neutral_y, True, 3)
        if not ok:
            raise RuntimeError("IK failed for neutral pose.")
        self.q_neutral = [q1n, q2n, q1n, q2n, q1n, q2n, q1n, q2n]

    def _recenter_to_150(self, q_abs_8):
        """
        Convert absolute IK angles into centered motor commands:
          cmd = 150 + (q_abs - q_neutral)
        """
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

    def set_gesture(self, gesture: Optional[str]) -> None:
        if gesture is None:
            return
        
        if gesture in ("forward", "backward", "turn_left", "turn_right"):
            self.robot.set_torque_limit_all(self.normal_torque)
            self.robot.set_moving_speed_all(self.normal_speed)

        # if gesture == "jump":
        #     self.gait_manager.stop()
        #     self.current_dir = None
        #     self.do_jump()
        #     return
            
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
