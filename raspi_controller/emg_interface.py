# q8gait/emg_interface.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict
import time


# These are the only gesture strings the rest of your robot code should depend on.
GESTURES = {
    "forward",
    "backward",
    "turn_left",
    "turn_right",
    "stop",
    "jump",
    "jump_forward",
    "jump_backward",
    "jump_left",
    "jump_right",
}


@dataclass
class EMGConfig:
    """
    Configuration knobs your teammate can tune.

    sample_hz:
        Approx sensor sampling rate. Used for window sizing if needed.

    gesture_hold_ms:
        If a gesture is detected, how long to keep outputting it (reduces flicker).

    cooldown_ms:
        Minimum time between emitting non-stop gestures (prevents rapid jitter).

    debug:
        If True, stores last raw/frame/features for inspection.
    """
    sample_hz: int = 200
    gesture_hold_ms: int = 150
    cooldown_ms: int = 200
    debug: bool = False


class EMGInterface:
    """
    EMG-based gesture source (polled from main loop).

    Usage:
        emg = EMGInterface(cfg=EMGConfig())
        while True:
            emg.poll()
            gesture = emg.read_gesture()
            ...

    Contract:
      - poll() reads new sensor data and updates internal state
      - read_gesture() returns one of:
            "forward", "backward", "turn_left", "turn_right", "stop",
            "jump", "jump_forward", "jump_backward", "jump_left", "jump_right"
        or None if no update / no confident gesture.
    """

    def __init__(self, cfg: EMGConfig = EMGConfig()):
        self.cfg = cfg

        self._gesture: Optional[str] = None

        # timing state
        self._last_emit_t: float = 0.0
        self._hold_until_t: float = 0.0

        # optional debug state
        self.debug_last: Dict[str, Any] = {}

        # TODO(EMG): initialize hardware / serial / BLE / file reader here.
        # Example:
        #   self.sensor = MyEMGSensor(port=..., baud=...)
        self.sensor = None  # placeholder

    # ----------------------------
    # Public API expected by main
    # ----------------------------
    def poll(self) -> None:
        """
        Called frequently (e.g., 100-200 Hz) from the main loop.
        Should:
          1) read sensor frame(s)
          2) compute features
          3) classify into a gesture string
          4) apply debounce/cooldown/hold logic
        """
        now = time.time()

        # 0) If we're holding a previous gesture, keep it active until hold ends
        if self._gesture is not None and now < self._hold_until_t:
            return

        # 1) Read one "frame" from the EMG sensor
        frame = self._read_sensor_frame()
        if frame is None:
            # no new data available
            self._gesture = None
            return

        # 2) Compute features from raw data
        features = self._compute_features(frame)

        # 3) Classify features into a gesture (or None)
        gesture = self._classify(features)

        # 4) Validate output + apply cooldown/hold rules
        gesture = self._apply_rules(gesture, now)

        self._gesture = gesture

        if self.cfg.debug:
            self.debug_last = {
                "t": now,
                "frame": frame,
                "features": features,
                "gesture": gesture,
            }

    def read_gesture(self) -> Optional[str]:
        """
        Return latest gesture. May be None.
        """
        return self._gesture

    # ----------------------------
    # TODO blocks for teammate
    # ----------------------------
    def _read_sensor_frame(self) -> Optional[Any]:
        """
        Read raw data from the EMG sensor.

        Return:
            A single frame/sample/batch in any format your teammate chooses.
            Examples:
              - float (1-channel amplitude)
              - list[float] (multi-channel)
              - dict with timestamps + channels
              - bytes that later get parsed

            Return None if no new data is available.
        """
        # TODO(EMG): implement this.
        # Must be NON-BLOCKING (or very fast) since main loop is real-time.
        return None

    def _compute_features(self, frame: Any) -> Any:
        """
        Compute useful features for classification.

        Examples:
          - RMS over a window
          - mean absolute value (MAV)
          - waveform length (WL)
          - channel ratios/differences
          - IMU fusion features if available

        Return any object (dict recommended) consumed by _classify().
        """
        # TODO(EMG): implement feature extraction.
        return {"raw": frame}

    def _classify(self, features: Any) -> Optional[str]:
        """
        Map features -> gesture string.

        Must return one of:
            "forward", "backward", "turn_left", "turn_right", "stop",
            "jump", "jump_forward", "jump_backward", "jump_left", "jump_right"
        or None (no confident gesture).
        """
        # TODO(EMG): implement classification logic.
        # Suggested approach:
        #   - return "stop" when confidence is low / below thresholds
        #   - return "jump" or directional jump on a short high peak
        #   - return turning based on channel differences
        #
        # JUMP DETECTION GUIDANCE:
        # -------------------------
        # Jump gestures can be detected using IMU accelerometer data:
        #
        # 1. DETECTING A JUMP:
        #    - Look for a sudden spike in vertical acceleration (Z-axis or total magnitude)
        #    - Typical threshold: accel_magnitude > 2.5g (where g = 9.8 m/s²)
        #    - The spike should be short duration (< 200ms)
        #
        # 2. DETERMINING JUMP DIRECTION:
        #    - Sample the wrist orientation (pitch/roll/yaw) at the time of the jump
        #    - Forward jump: wrist pitched forward (pitch > 30°)
        #    - Backward jump: wrist pitched backward (pitch < -30°)
        #    - Left jump: wrist rolled left (roll > 30°)
        #    - Right jump: wrist rolled right (roll < -30°)
        #    - In-place jump: wrist level (|pitch| < 30° and |roll| < 30°)
        #
        # 3. EXAMPLE IMPLEMENTATION:
        #    ```python
        #    # Assuming features contains IMU data:
        #    accel_x = features.get('accel_x', 0)
        #    accel_y = features.get('accel_y', 0)
        #    accel_z = features.get('accel_z', 0)
        #    pitch = features.get('pitch', 0)  # in degrees
        #    roll = features.get('roll', 0)    # in degrees
        #
        #    # Calculate total acceleration magnitude
        #    accel_mag = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
        #
        #    # Jump detection threshold (in m/s² or g's)
        #    JUMP_THRESHOLD = 2.5 * 9.8  # 2.5g
        #
        #    if accel_mag > JUMP_THRESHOLD:
        #        # Jump detected! Now determine direction
        #        if abs(pitch) > abs(roll):
        #            # Pitch is dominant
        #            if pitch > 30:
        #                return "jump_forward"
        #            elif pitch < -30:
        #                return "jump_backward"
        #        else:
        #            # Roll is dominant
        #            if roll > 30:
        #                return "jump_left"
        #            elif roll < -30:
        #                return "jump_right"
        #
        #        # Default to in-place jump if orientation is neutral
        #        return "jump"
        #    ```
        #
        # 4. PREVENTING FALSE POSITIVES:
        #    - Use a cooldown period after each jump (already handled by _apply_rules)
        #    - Require the spike to return to baseline quickly
        #    - Consider adding a "gesture preparation" phase detection
        #
        return None

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _apply_rules(self, gesture: Optional[str], now: float) -> Optional[str]:
        """
        Debounce/cooldown/hold behavior so you don't spam the robot.
        """
        if gesture is None:
            return None

        if gesture not in GESTURES:
            raise ValueError(f"Invalid gesture '{gesture}'. Must be one of: {sorted(GESTURES)}")

        # Always allow stop immediately
        if gesture == "stop":
            self._last_emit_t = now
            self._hold_until_t = 0.0
            return "stop"

        # Cooldown for non-stop gestures
        if (now - self._last_emit_t) * 1000.0 < self.cfg.cooldown_ms:
            return None

        # Hold the gesture for a short time to reduce flicker
        self._last_emit_t = now
        self._hold_until_t = now + (self.cfg.gesture_hold_ms / 1000.0)
        return gesture
