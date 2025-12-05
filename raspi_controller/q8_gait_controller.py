import math
from typing import Dict, Optional

from .q8gait import k_solver, GaitManager, GAITS


class Q8GaitController:
    JOINT_ORDER = [
        "front_left_hip",
        "front_left_knee",
        "front_right_hip",
        "front_right_knee",
        "rear_left_hip",
        "rear_left_knee",
        "rear_right_hip",
        "rear_right_knee",
    ]

    def __init__(self, default_gait: str = "TROT") -> None:
        leg = k_solver()
        self.gait_manager = GaitManager(leg, available_gaits=GAITS)

        if default_gait not in GAITS:
            raise ValueError(f"Unknown gait '{default_gait}'. Available: {list(GAITS.keys())}")

        ok = self.gait_manager.load_gait(default_gait)
        if not ok:
            raise RuntimeError(f"Failed to load gait '{default_gait}'")

        self.current_direction_code: Optional[str] = None

        self._neutral_pose: Dict[str, float] = {name: 0.0 for name in self.JOINT_ORDER}

    # ---------------- Internal helpers ---------------- #

    def _map_command_to_direction(self, command: str) -> Optional[str]:
        """
        Map your high-level commands to q8bot direction codes.

        Your state machine currently uses:
            - 'idle'
            - 'forward'
            - 'turn_left'
            - 'turn_right'
        (We can extend this later for diagonals, backward, etc.)

        Returns:
            q8bot direction code (e.g. 'f', 'l', 'r') or None for idle.
        """
        if command == "idle":
            return None
        if command == "forward":
            return "f"
        if command == "backward":
            return "b"
        if command == "turn_left":
            return "l"
        if command == "turn_right":
            return "r"

        # Unknown / unsupported command -> treat as idle
        return None

    def _deg_list_to_joint_dict(self, angles_deg) -> Dict[str, float]:
        """
        Convert list[8] of degrees (q1/q2 per leg) to {joint_name: rad}.
        The q8bot order is:
            [FL_q1, FL_q2, FR_q1, FR_q2, BL_q1, BL_q2, BR_q1, BR_q2]
        """
        if angles_deg is None or len(angles_deg) != 8:
            # Fallback to neutral pose if anything looks off
            return self._neutral_pose.copy()

        result: Dict[str, float] = {}
        for name, angle_deg in zip(self.JOINT_ORDER, angles_deg):
            result[name] = math.radians(angle_deg)
        return result

    # ---------------- Public API (main.py uses this) ---------------- #

    def step(self, dt: float, command: str) -> Dict[str, float]:
        """
        Advance the gait by one step and return joint targets.

        Args:
            dt: timestep in seconds (currently unused, but kept for compatibility)
            command: high-level command string from your StateMachine

        Returns:
            Dict[joint_name, angle_rad]
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
                return self._neutral_pose.copy()

        # Get next point from the trajectory
        pos = self.gait_manager.tick()  # list of 8 joint angles in degrees
        return self._deg_list_to_joint_dict(pos)
