from typing import Dict, List
import math
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DXL_RESOLUTION = 1023.0
DXL_MAX_DEGREES = 300.0
CENTER_DEG = 150.0


def deg_to_pos(deg: float) -> int:
    # convert 0-300 degrees to 0-1023 position
    deg = max(0.0, min(DXL_MAX_DEGREES, deg))
    pos = int((deg / DXL_MAX_DEGREES) * DXL_RESOLUTION)
    return pos


class RobotInterface:
    def __init__(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.tools_dir = repo_root / "dynamixel_tools"
        self.motor_server_path = self.tools_dir / "motor_server"

        if not self.motor_server_path.exists():
            raise FileNotFoundError(f"motor_server not found at {self.motor_server_path}")

        self.joint_order: List[str] = [
            "front_left_leg_1",
            "front_left_leg_2",
            "back_left_leg_1",
            "back_left_leg_2",
            "back_right_leg_1",
            "back_right_leg_2",
            "front_right_leg_1",
            "front_right_leg_2",
        ]

        # self.proc = subprocess.Popen(
        #     [str(self.motor_server_path)],
        #     stdin=subprocess.PIPE,
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.STDOUT,
        #     text=True,
        #     bufsize=1,
        # )
        self.proc = subprocess.Popen(
            [str(self.motor_server_path)],
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1,
        )

        logger.info(f"Started motor_server at {self.motor_server_path}")
        
    def enable_torque(self) -> None:
        logger.info("Torque enable handled by motor_server.")

    def disable_torque(self) -> None:
        logger.info("Torque disable handled by motor_server on quit.")

    def set_joint_positions(self, joint_positions: Dict[str, float]) -> None:
        if self.proc.poll() is not None:
            logger.error("motor_server process has exited unexpectedly.")
            return

        pos_vals: List[int] = []

        for name in self.joint_order:
            angle_rad = joint_positions.get(name, 0.0)
            # print(f"Joint {name}: angle_rad={angle_rad}")
            offset_deg = math.degrees(angle_rad)
            target_deg = CENTER_DEG + offset_deg
            pos = deg_to_pos(target_deg)
            pos_vals.append(pos)

        line = " ".join(str(p) for p in pos_vals) + "\n"
        logger.info(f"Sending positions to motor_server: {line.strip()}")
        try:
            assert self.proc.stdin is not None
            self.proc.stdin.write(line)
            self.proc.stdin.flush()
        except BrokenPipeError:
            logger.error("Broken pipe to motor_server (it may have crashed).")

    def stop(self) -> None:
        """
        Send a QUIT command so the C server can disable torque and close the port.
        """
        if self.proc.poll() is None and self.proc.stdin is not None:
            try:
                self.proc.stdin.write("QUIT\n")
                self.proc.stdin.flush()
            except BrokenPipeError:
                pass

        # Wait for process to exit
        self.proc.wait(timeout=2.0)
        logger.info("motor_server stopped.")
        

    def __del__(self) -> None:
        try:
            self.stop()
        except Exception:
            pass
