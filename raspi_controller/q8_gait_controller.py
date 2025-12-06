import math
from typing import Dict, Optional

from q8gait import k_solver, GaitManager, GAITS


class Q8GaitController:
    JOINT_NAMES = [
        "front_left_leg_1",
        "front_left_leg_2",
        "back_left_leg_1",
        "back_left_leg_2",
        "back_right_leg_1",
        "back_right_leg_2",
        "front_right_leg_1",
        "front_right_leg_2",
    ]

    def __init__(self, default_gait: str = "TROT") -> None:
        leg = k_solver()
        self.gait_manager = GaitManager(leg, available_gaits=GAITS)

        if default_gait not in GAITS:
            raise ValueError(f"Unknown gait '{default_gait}'. Available: {list(GAITS.keys())}")

        ok = self.gait_manager.load_gait(default_gait)
        if not ok:
            raise RuntimeError(f"Failed to load gait '{default_gait}'")

        self._neutral_pose: Dict[str, float] = {name: 0.0 for name in self.JOINT_NAMES}

    # ----------------- Command mapping ----------------- #

    def _map_command_to_direction(self, command) -> Optional[str]:
        """
        Map high-level command to q8bot direction code used in trajectories.

        Accepts:
          - plain strings: "forward", "backward", "turn_left", "turn_right", "idle"
          - Enums: uses command.value if present
          - case-insensitive, ignores surrounding whitespace
        """
        # Extract a string from command (supports Enum.value, etc.)
        raw = getattr(command, "value", command)
        cmd_str = str(raw).strip().lower()

        if cmd_str in ("idle", "none", "stop", ""):
            return None
        if cmd_str in ("forward", "f"):
            return "f"
        if cmd_str in ("backward", "b"):
            return "b"
        if cmd_str in ("turn_left", "left", "l"):
            return "l"
        if cmd_str in ("turn_right", "right", "r"):
            return "r"

        # Unknown / unsupported command -> treat as idle
        # (If this ever happens, you'll still see State/Command in the logs)
        return None

    # ----------------- Angle conversion ----------------- #

    def _deg_list_to_joint_dict(self, angles_deg) -> Dict[str, float]:
        """
        Convert list[8] of degrees (q1/q2 per leg) to {joint_name: rad}.

        q8bot's trajectory order (from append_pos_list) is:
            [FL_q1, FL_q2, FR_q1, FR_q2, BL_q1, BL_q2, BR_q1, BR_q2]

        Physical motor order:
            index 0 (ID 1) = front_left_leg_1  (FL_q1)
            index 1 (ID 2) = front_left_leg_2  (FL_q2)
            index 2 (ID 3) = back_left_leg_1   (BL_q1)
            index 3 (ID 4) = back_left_leg_2   (BL_q2)
            index 4 (ID 5) = back_right_leg_1  (BR_q1)
            index 5 (ID 6) = back_right_leg_2  (BR_q2)
            index 6 (ID 7) = front_right_leg_1 (FR_q1)
            index 7 (ID 8) = front_right_leg_2 (FR_q2)
        """
        if angles_deg is None or len(angles_deg) != 8:
            # If this happens, something is wrong upstream (tick / trajectories)
            return self._neutral_pose.copy()

        fl1, fl2, fr1, fr2, bl1, bl2, br1, br2 = angles_deg

        return {
            "front_left_leg_1":  math.radians(fl1),
            "front_left_leg_2":  math.radians(fl2),
            "back_left_leg_1":   math.radians(bl1),
            "back_left_leg_2":   math.radians(bl2),
            "back_right_leg_1":  math.radians(br1),
            "back_right_leg_2":  math.radians(br2),
            "front_right_leg_1": math.radians(fr1),
            "front_right_leg_2": math.radians(fr2),
        }

    # ----------------- Main step API ----------------- #

    def step(self, dt: float, command) -> Dict[str, float]:
        """
        Advance the gait by one step.

        Args:
            dt: timestep (seconds)
            command: high-level command from StateMachine ("forward", "idle", etc. or Enum)

        Returns:
            Dict[joint_name -> angle_rad]
        """
        direction = self._map_command_to_direction(command)

        # If idle -> stop movement and return neutral pose
        if direction is None:
            if self.gait_manager.is_moving():
                self.gait_manager.stop()
            return self._neutral_pose.copy()

        # If direction changed or not moving yet, (re)start movement
        if (not self.gait_manager.is_moving()) or (direction != self.gait_manager.get_current_direction()):
            started = self.gait_manager.start_movement(direction)
            if not started:
                # No trajectory for this direction -> fall back to neutral
                # (e.g., asking for 'l' when WALK gait only has 'f'/'b'; but TROT has f/b/l/r)
                return self._neutral_pose.copy()

        # Get next point from the trajectory
        pos = self.gait_manager.tick()  # list of 8 joint angles in degrees
        return self._deg_list_to_joint_dict(pos)
