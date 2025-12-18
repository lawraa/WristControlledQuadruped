import sys
import termios
import tty
import select
import time
from typing import Literal

Gesture = Literal["none", "forward", "turn_left", "turn_right", "stop"]


class KeyboardInterface:
    """
    Keyboard-based gesture source (polled from main loop).

    Usage:
        kb = KeyboardInterface()
        ...
        while True:
            kb.poll()
            gesture = kb.read_gesture()
            ...

    Keys:
        w -> "forward"
        a -> "turn_left"
        d -> "turn_right"
        s or space -> "stop"
        x -> "backward"
        j -> "jump" (in-place)

    Jump with direction (two-key combinations):
        j + w -> "jump_forward"
        j + x -> "jump_backward"
        j + a -> "jump_left"
        j + d -> "jump_right"
    """

    def __init__(self) -> None:
        self._current_gesture: Gesture = "none"
        self._fd = sys.stdin.fileno()
        self._last_key = None  # Track last key for combination detection
        self._last_key_time = 0.0  # Track when last key was pressed
        self._combo_timeout = 0.3  # 300ms window for key combinations

        try:
            self._old_settings = termios.tcgetattr(self._fd)
        except termios.error:
            print("[KeyboardInterface] Warning: stdin is not a TTY; keyboard control may not work.")
            self._old_settings = None
            return

        # Put terminal into cbreak mode so we get characters immediately
        tty.setcbreak(self._fd)

        print(
            "\n[KeyboardInterface] Keyboard control enabled.\n"
            "  w = forward\n"
            "  a = turn left\n"
            "  d = turn right\n"
            "  s or space = stop/idle\n"
            "  x = backward\n"
            "  j = jump (in-place)\n"
            "  j+w = jump forward\n"
            "  j+x = jump backward\n"
            "  j+a = jump left\n"
            "  j+d = jump right\n"
            "  Ctrl+C in terminal = exit program\n"
        )

    def poll(self) -> None:
        if self._old_settings is None:
            return

        rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
        if not rlist:
            return

        ch = sys.stdin.read(1)
        current_time = time.time()

        # Check for jump combinations (j + direction key)
        if self._last_key == "j" and (current_time - self._last_key_time) < self._combo_timeout:
            if ch == "w":
                self._current_gesture = "jump_forward"
                print(f"[KeyboardInterface] Combo detected: j+w -> jump_forward")
                self._last_key = None
                return
            elif ch == "x":
                self._current_gesture = "jump_backward"
                print(f"[KeyboardInterface] Combo detected: j+x -> jump_backward")
                self._last_key = None
                return
            elif ch == "a":
                self._current_gesture = "jump_left"
                print(f"[KeyboardInterface] Combo detected: j+a -> jump_left")
                self._last_key = None
                return
            elif ch == "d":
                self._current_gesture = "jump_right"
                print(f"[KeyboardInterface] Combo detected: j+d -> jump_right")
                self._last_key = None
                return

        # Regular key presses
        if ch == "w":
            self._current_gesture = "forward"
            print(f"[KeyboardInterface] \"{ch}\" is pressed: gesture -> forward")
        elif ch == "a":
            self._current_gesture = "turn_left"
            print(f"[KeyboardInterface] \"{ch}\" is pressed: gesture -> turn_left")
        elif ch == "d":
            self._current_gesture = "turn_right"
            print(f"[KeyboardInterface] \"{ch}\" is pressed: gesture -> turn_right")
        elif ch == "s" or ch == " ":
            self._current_gesture = "stop"
            print(f"[KeyboardInterface] \"{ch}\" is pressed: gesture -> stop")
        elif ch == "x":
            self._current_gesture = "backward"
            print(f"[KeyboardInterface] \"{ch}\" is pressed: gesture -> backward")
        elif ch == "j":
            self._current_gesture = "jump"
            print(f"[KeyboardInterface] \"{ch}\" is pressed: gesture -> jump (press direction key within 0.3s for directional jump)")

        # Track this key for potential combinations
        self._last_key = ch
        self._last_key_time = current_time

    def read_gesture(self) -> Gesture:
        return self._current_gesture

    def close(self) -> None:
        if self._old_settings is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
            except Exception:
                pass
