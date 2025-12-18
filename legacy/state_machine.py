from enum import Enum
from typing import Tuple
from wrist_interface import Gesture


class RobotState(Enum):
    INIT = 0
    IDLE = 1
    MOVING = 2
    SAFETY_STOP = 3


class StateMachine:
    """
    Maps (current_state, wrist_gesture) -> (next_state, command_for_gait_controller).
    """

    def __init__(self) -> None:
        self.state = RobotState.INIT

    def update(self, gesture: Gesture) -> Tuple[RobotState, str]:
        if self.state == RobotState.INIT:
            self.state = RobotState.IDLE
            return self.state, "idle"

        if self.state == RobotState.SAFETY_STOP:
            if gesture in ("forward", "turn_left", "turn_right"):
                self.state = RobotState.MOVING
                return self.state, self._gesture_to_command(gesture)
            else:
                return self.state, "idle"

        if self.state == RobotState.IDLE:
            if gesture == "forward":
                self.state = RobotState.MOVING
                return self.state, "forward"
            elif gesture == "turn_left":
                self.state = RobotState.MOVING
                return self.state, "turn_left"
            elif gesture == "turn_right":
                self.state = RobotState.MOVING
                return self.state, "turn_right"
            else:
                return self.state, "idle"

        if self.state == RobotState.MOVING:
            if gesture in ("stop", "none"):
                self.state = RobotState.IDLE
                return self.state, "idle"
            else:
                return self.state, self._gesture_to_command(gesture)

        # Fallback
        return self.state, "idle"

    def emergency_stop(self) -> None:
        self.state = RobotState.SAFETY_STOP

    def _gesture_to_command(self, gesture: Gesture) -> str:
        if gesture == "forward":
            return "forward"
        if gesture == "turn_left":
            return "turn_left"
        if gesture == "turn_right":
            return "turn_right"
        return "idle"
