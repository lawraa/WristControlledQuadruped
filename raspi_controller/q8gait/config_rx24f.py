from dataclasses import dataclass
from typing import List

@dataclass
class MotorSpec:
    motor_id: int
    reverse: bool
    offset_ticks: int

@dataclass
class RX24FConfig:
    port: str # /dev/ttyUSB0
    baudrate: int # 1,000,000
    protocol_version: float # 1.0 for us
    ticks_per_300deg: int = 1023 # For RX-24F: typically 0..1023 ticks maps to 0..300 degrees
    max_deg: float = 300.0
    motors: List[MotorSpec] = None 

def default_config() -> RX24FConfig:
    return RX24FConfig(
        port="/dev/ttyUSB0",
        baudrate=1000000, 
        protocol_version=1.0,     # RX-24F is commonly Protocol 1.0
        motors=[
            # FL_q1, FL_q2, FR_q1, FR_q2, BL_q1, BL_q2, BR_q1, BR_q2  
            MotorSpec(motor_id=1, reverse=False, offset_ticks=0),
            MotorSpec(motor_id=2, reverse=False, offset_ticks=0),
            MotorSpec(motor_id=8, reverse=True,  offset_ticks=0),
            MotorSpec(motor_id=7, reverse=True,  offset_ticks=0),
            MotorSpec(motor_id=3, reverse=False,  offset_ticks=0),
            MotorSpec(motor_id=4, reverse=False,  offset_ticks=0),
            MotorSpec(motor_id=6, reverse=True, offset_ticks=0), 
            MotorSpec(motor_id=5, reverse=True, offset_ticks=0),    
        ],
    )
