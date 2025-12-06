import sys
import termios
import tty
import select
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
    """

    def __init__(self) -> None:
        self._current_gesture: Gesture = "none"
        self._fd = sys.stdin.fileno()

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
            "  Ctrl+C in terminal = exit program\n"
        )

    def poll(self) -> None:
        """
        Non-blocking poll for a keypress. Call this every loop.
        Updates self._current_gesture if a valid key is pressed.
        """
        if self._old_settings is None:
            return  # no TTY

        rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
        if not rlist:
            return

        ch = sys.stdin.read(1)

        if ch == "w":
            self._current_gesture = "forward"
            print("[KeyboardInterface] gesture -> forward")
        elif ch == "a":
            self._current_gesture = "turn_left"
            print("[KeyboardInterface] gesture -> turn_left")
        elif ch == "d":
            self._current_gesture = "turn_right"
            print("[KeyboardInterface] gesture -> turn_right")
        elif ch == "s" or ch == " ":
            self._current_gesture = "stop"
            print("[KeyboardInterface] gesture -> stop")
        # You can add more keys here later (e.g., backward, diagonals)

    def read_gesture(self) -> Gesture:
        """Return the most recent gesture decided by keyboard input."""
        return self._current_gesture

    def close(self) -> None:
        """Restore terminal settings."""
        if self._old_settings is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
            except Exception:
                pass
