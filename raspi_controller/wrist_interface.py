from typing import Literal

Gesture = Literal["none", "forward", "turn_left", "turn_right", "stop"]


class WristInterface:
    # this is still a fake interface for now
    def __init__(self) -> None:
        self._current_gesture: Gesture = "forward"

    def read_gesture(self) -> Gesture:
        # this will read the emg/imu 
        # then filter and extract features --> run classifier i'm guessing
        # output one of the Gesture literals
        return self._current_gesture

    def set_fake_gesture(self, gesture: Gesture) -> None:
        # for testing right now
        self._current_gesture = gesture
