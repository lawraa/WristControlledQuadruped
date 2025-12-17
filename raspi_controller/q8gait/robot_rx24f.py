from __future__ import annotations
from typing import List, Optional
from dynamixel_sdk import PortHandler, PacketHandler, GroupSyncWrite
from .config_rx24f import RX24FConfig

# Protocol 1.0 control table addresses (common for AX/RX series)
ADDR_TORQUE_ENABLE = 24
ADDR_GOAL_POSITION = 30   # 2 bytes
ADDR_MOVING_SPEED  = 32   # 2 bytes (optional)
ADDR_TORQUE_LIMIT  = 34   # 2 bytes (optional)

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


ADDR_MOVING_SPEED  = 32
ADDR_TORQUE_LIMIT  = 34
ADDR_MAX_TORQUE   = 14 



class RX24FRobot:
    """
    Sends 8 joint angles (deg) to RX-24F motors using Protocol 1.0 SyncWrite.
    """
    def __init__(self, cfg: RX24FConfig):
        if cfg.motors is None or len(cfg.motors) != 8:
            raise ValueError("cfg.motors must have 8 MotorSpec entries.")

        self.cfg = cfg
        self.port = PortHandler(cfg.port)
        self.packet = PacketHandler(cfg.protocol_version)
        self.sync_write_pos = GroupSyncWrite(self.port, self.packet, ADDR_GOAL_POSITION, 2)
        self._is_open = False
        self._torque_on = False

    def open(self) -> None:
        if not self.port.openPort():
            raise RuntimeError(f"Failed to open port {self.cfg.port}")
        if not self.port.setBaudRate(self.cfg.baudrate):
            raise RuntimeError(f"Failed to set baudrate {self.cfg.baudrate}")
        self._is_open = True

    def close(self) -> None:
        if self._is_open:
            try:
                self.torque(False)
            except Exception:
                pass
            self.port.closePort()
        self._is_open = False

    def torque(self, on: bool) -> None:
        for m in self.cfg.motors:
            dxl_comm_result, dxl_error = self.packet.write1ByteTxRx(
                self.port, m.motor_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE if on else TORQUE_DISABLE
            )
            if dxl_comm_result != 0:
                raise RuntimeError(f"Torque write failed for ID {m.motor_id}: comm={dxl_comm_result}, err={dxl_error}")
        self._torque_on = on

    def deg_to_ticks(self, deg: float, motor_index: int) -> int:
        """
        Convert degrees to Dynamixel ticks for RX-24F (0..1023 for 0..300 deg typical).
        Apply reverse + offset.
        """
        spec = self.cfg.motors[motor_index]
        # Basic mapping
        ticks = int((deg / self.cfg.max_deg) * self.cfg.ticks_per_300deg + 0.5)
        ticks = clamp(ticks, 0, self.cfg.ticks_per_300deg)

        # Reverse direction (mirror)
        if spec.reverse:
            ticks = self.cfg.ticks_per_300deg - ticks

        # Apply offset calibration
        ticks = ticks + spec.offset_ticks

        # Wrap/clamp to valid
        ticks = clamp(ticks, 0, self.cfg.ticks_per_300deg)
        return ticks

    def write_positions_deg(self, pos_deg_8: List[float]) -> None:
        """
        pos_deg_8 is length-8:
        [FL_q1, FL_q2, FR_q1, FR_q2, BL_q1, BL_q2, BR_q1, BR_q2]
        """
        if len(pos_deg_8) != 8:
            raise ValueError("pos_deg_8 must have length 8.")

        self.sync_write_pos.clearParam()

        for i, deg in enumerate(pos_deg_8):
            spec = self.cfg.motors[i]
            ticks = self.deg_to_ticks(deg, i)
            # little-endian 2 bytes
            param = [ticks & 0xFF, (ticks >> 8) & 0xFF]
            ok = self.sync_write_pos.addParam(spec.motor_id, bytes(param))
            if not ok:
                raise RuntimeError(f"Failed to add param for ID {spec.motor_id}")

        dxl_comm_result = self.sync_write_pos.txPacket()
        if dxl_comm_result != 0:
            raise RuntimeError(f"SyncWrite failed: comm={dxl_comm_result}")
    
    def _write2(self, motor_id: int, addr: int, value: int) -> None:
        value = clamp(value, 0, 1023)
        dxl_comm_result, dxl_error = self.packet.write2ByteTxRx(self.port, motor_id, addr, value)
        if dxl_comm_result != 0:
            raise RuntimeError(f"Write2 failed ID {motor_id} addr {addr}: comm={dxl_comm_result}, err={dxl_error}")

    def set_moving_speed_all(self, speed: int) -> None:
        for m in self.cfg.motors:
            self._write2(m.motor_id, ADDR_MOVING_SPEED, speed)

    def set_torque_limit_all(self, limit: int) -> None:
        for m in self.cfg.motors:
            self._write2(m.motor_id, ADDR_TORQUE_LIMIT, limit)


    def _read2(self, motor_id: int, addr: int) -> int:
        val, dxl_comm_result, dxl_error = self.packet.read2ByteTxRx(self.port, motor_id, addr)
        if dxl_comm_result != 0:
            raise RuntimeError(f"Read2 failed ID {motor_id} addr {addr}: comm={dxl_comm_result}, err={dxl_error}")
        return int(val)

    def get_moving_speed_all(self) -> list[int]:
        return [self._read2(m.motor_id, ADDR_MOVING_SPEED) for m in self.cfg.motors]

    def get_torque_limit_all(self) -> list[int]:
        return [self._read2(m.motor_id, ADDR_TORQUE_LIMIT) for m in self.cfg.motors]

    def get_max_torque_all(self) -> list[int]:
        return [self._read2(m.motor_id, ADDR_MAX_TORQUE) for m in self.cfg.motors]
