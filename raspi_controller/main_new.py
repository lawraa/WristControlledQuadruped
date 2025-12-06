import time
import logging

from robot_interface import RobotInterface
from q8_gait_controller import Q8GaitController
from keyboard_interface import KeyboardInterface
from wrist_interface import WristInterface
from state_machine import StateMachine

logging.basicConfig(level=logging.INFO)

SAMPLING_RATE = 50.0  # sample at 50 times per second
DT = 1.0 / SAMPLING_RATE


def main() -> None:
    robot = RobotInterface()
    gait = Q8GaitController(default_gait="TROT")  # q8bot gait trajectories
    kb = KeyboardInterface()
    wrist = WristInterface()
    sm = StateMachine()

    robot.enable_torque()
    logging.info(f"Sampling Rate: {SAMPLING_RATE} Hz")
    logging.info("Using q8bot-based gait controller (TROT) with keyboard input (w/a/s/d).")

    last_print_time = time.time()
    last_loop_time = time.time()

    try:
        while True:
            now = time.time()
            dt = now - last_loop_time
            if dt < DT:
                time.sleep(DT - dt)
                continue
            last_loop_time = now

            # Poll keyboard once per loop (non-blocking, very fast)
            kb.poll()
            gesture = kb.read_gesture()

            # gesture = wrist.read_gesture()

            # High-level command flow
            state, command = sm.update(gesture)
            joint_targets = gait.step(DT, command)
            
            # Low-level motor command
            robot.set_joint_positions(joint_targets)

            # Print status every second
            if now - last_print_time > 1.0:
                logging.info(f"State={state.name}, Gesture={gesture}, Command={command}")
                print(f"joint_targets: {joint_targets}")
                last_print_time = now

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - stopping control loop.")
    finally:
        robot.stop()
        robot.disable_torque()
        try:
            kb.close()
        except Exception:
            pass
        logging.info("Shutdown complete.")


if __name__ == "__main__":
    main()
