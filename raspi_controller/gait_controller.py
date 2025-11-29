from typing import Dict
import math


class GaitController:
    def __init__(self) -> None:
        self.joint_names = [
            "front_left_hip", 
            "front_left_knee",
            "front_right_hip", 
            "front_right_knee",
            "rear_left_hip", 
            "rear_left_knee",
            "rear_right_hip", 
            "rear_right_knee",
        ]

        self.neutral_pose = {name: 0.0 for name in self.joint_names}

        self.t = 0.0

    def step(self, dt: float, command: str) -> Dict[str, float]:
        # dt: timestep (seconds) since last call
        # command: "idle", "forward", "turn_left", "turn_right", etc.
        self.t += dt

        if command == "idle":
            return self.neutral_pose.copy()

        if command in ("forward", "turn_left", "turn_right"):
            return self._simple_trot(command)

        return self.neutral_pose.copy()

    def _simple_trot(self, command: str) -> Dict[str, float]: 
        gait: Dict[str, float] = {}
        freq_hz = 0.5
        omega = 2.0 * math.pi * freq_hz

        turn_bias = 0.0
        if command == "turn_left":
            turn_bias = 0.2
        elif command == "turn_right":
            turn_bias = -0.2

        for name in self.joint_names:
            if "front_left" in name or "rear_right" in name:
                phase = 0.0
            else:
                phase = math.pi

            hip_amp = 0.3
            knee_amp = 0.4

            s = math.sin(omega * self.t + phase)

            if "hip" in name:
                angle = hip_amp * s
                if "left" in name:
                    angle += turn_bias
                elif "right" in name:
                    angle -= turn_bias
            elif "knee" in name:
                angle = -knee_amp * s
            else:
                angle = 0.0

            gait[name] = angle

        return gait
