import math
from typing import Dict, Optional

from q8gait import k_solver, GaitManager, GAITS

CENTER_DEG = 150.0

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

        # Compute neutral IK angles for this gait
        gait_params = GAITS[default_gait]
        _, x0, y0, *_ = gait_params
        q1_0, q2_0, _ = leg.ik_solve(x0, y0, deg=True, rounding=3)
        self._neutral_q1_deg = q1_0
        self._neutral_q2_deg = q2_0
        # print(f"Neutral IK angles: q1={q1_0} deg, q2={q2_0} deg")
        # ------------------------------------------------

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
            # print("OUTPUTING IDLE")
            return None
        if cmd_str in ("forward", "f"):
            # print("OUTPUTING FORWARD")
            return "f"
        if cmd_str in ("backward", "b"):
            # print("OUTPUTING BACKWARD")
            return "b"
        if cmd_str in ("turn_left", "left", "l"):
            # print("OUTPUTING LEFT")
            return "l"
        if cmd_str in ("turn_right", "right", "r"):
            # print("OUTPUTING RIGHT")
            return "r"

        # Unknown / unsupported command -> treat as idle
        # (If this ever happens, you'll still see State/Command in the logs)
        return None

    def _deg_list_to_joint_dict(self, angles_deg) -> Dict[str, float]:
        """
        Convert list[8] of ABSOLUTE degrees (q1/q2 per leg) from q8gait
        into {joint_name: rad OFFSET from neutral}.

        RobotInterface will add this offset (in deg) on top of 150°,
        so at neutral we want 0 rad here.
        """

        if angles_deg is None or len(angles_deg) != 8:
            return self._neutral_pose.copy()

        fl1, fl2, fr1, fr2, bl1, bl2, br1, br2 = angles_deg
        q1_0 = self._neutral_q1_deg
        q2_0 = self._neutral_q2_deg

        def off1(deg: float) -> float:
            return math.radians(deg - q1_0)

        def off2(deg: float) -> float:
            return math.radians(deg - q2_0)

        return {
            "front_left_leg_1":  off1(fl1),
            "front_left_leg_2":  off2(fl2),

            "back_left_leg_1":   off1(bl1),
            "back_left_leg_2":   off2(bl2),

            # RIGHT SIDE: swap joint1/joint2
            "front_right_leg_1": off2(fr2),
            "front_right_leg_2": off1(fr1),

            "back_right_leg_1":  off2(br2),
            "back_right_leg_2":  off1(br1),

            # "front_right_leg_1": off2(fr1),
            # "front_right_leg_2": off1(fr2),

            # "back_right_leg_1":  off2(br1),
            # "back_right_leg_2":  off1(br2),
        }



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


    def pose_from_xy(self, x: float, y: float) -> Dict[str, float]:
        # Solve IK once (same pose for all legs)
        q1, q2, ok = self.gait_manager.leg.ik_solve(x, y, deg=True, rounding=3)
        if not ok:
            return self._neutral_pose.copy()

        q1_0 = self._neutral_q1_deg
        q2_0 = self._neutral_q2_deg

        def off1(deg: float) -> float:
            return math.radians(deg - q1_0)

        def off2(deg: float) -> float:
            return math.radians(deg - q2_0)

        # All legs same absolute angles, but RIGHT side needs joint swap (your wiring)
        fl1, fl2 = q1, q2
        fr1, fr2 = q1, q2
        bl1, bl2 = q1, q2
        br1, br2 = q1, q2

        return {
            "front_left_leg_1":  off1(fl1),
            "front_left_leg_2":  off2(fl2),
            "back_left_leg_1":   off1(bl1),
            "back_left_leg_2":   off2(bl2),

            # right side joint swap
            "front_right_leg_1": off2(fr2),
            "front_right_leg_2": off1(fr1),
            "back_right_leg_1":  off2(br2),
            "back_right_leg_2":  off1(br1),
        }
