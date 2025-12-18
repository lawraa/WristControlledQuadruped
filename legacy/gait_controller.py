from typing import Dict
import math


class GaitController:
    def __init__(self) -> None:
        self.joint_names = [
            "front_left_leg_1",
            "front_left_leg_2",
            "back_left_leg_1",
            "back_left_leg_2",
            "back_right_leg_1",
            "back_right_leg_2",
            "front_right_leg_1",
            "front_right_leg_2",
        ]

        self.neutral_pose = {name: 0.0 for name in self.joint_names}
        self.t = 0.0

    def step(self, dt: float, command: str) -> Dict[str, float]:
        """
        dt: timestep (seconds) since last call
        command: "idle", "forward", "turn_left", "turn_right", etc.
        """
        self.t += dt

        if command == "idle":
            return self.neutral_pose.copy()

        if command in ("forward", "turn_left", "turn_right"):
            return self._simple_trot(command)

        # Fallback
        return self.neutral_pose.copy()

    def _simple_trot(self, command: str) -> Dict[str, float]:
        """
        Very simple trot:
          - front_left + back_right in phase
          - front_right + back_left in opposite phase
          - leg_1 behaves like "hip" (swing)
          - leg_2 behaves like "knee" (lift)
        """
        gait: Dict[str, float] = {}

        # Gait frequency ~0.5 Hz (one full cycle = 2 seconds)
        freq_hz = 0.5
        omega = 2.0 * math.pi * freq_hz

        # Turn bias (small offset added to "hip" joints)
        turn_bias = 0.0
        if command == "turn_left":
            turn_bias = 0.2
        elif command == "turn_right":
            turn_bias = -0.2

        # Amplitudes for hip (leg_1) and knee (leg_2)
        hip_amp = 0.3   # radians (~17 deg)
        knee_amp = 0.4  # radians (~23 deg)

        for name in self.joint_names:
            # Figure out which leg this is
            is_front = name.startswith("front_")
            is_back = name.startswith("back_")
            is_left = "_left_" in name
            is_right = "_right_" in name

            is_leg1 = name.endswith("_leg_1")  # treat as "hip"
            is_leg2 = name.endswith("_leg_2")  # treat as "knee"

            # Diagonal pairing for trot:
            #   - Pair 1: front_left & back_right  -> phase 0
            #   - Pair 2: front_right & back_left -> phase pi
            if (is_front and is_left) or (is_back and is_right):
                phase = 0.0
            else:
                phase = math.pi

            s = math.sin(omega * self.t + phase)

            if is_leg1:
                # "Hip" joint: swing forward/back
                angle = hip_amp * s
                # Apply turn bias on hips: left/right difference
                if is_left:
                    angle += turn_bias
                elif is_right:
                    angle -= turn_bias
            elif is_leg2:
                # "Knee" joint: mostly lifts feet up/down
                angle = -knee_amp * s
            else:
                # Shouldn't happen with current naming, but safe fallback
                angle = 0.0

            gait[name] = angle

        return gait
