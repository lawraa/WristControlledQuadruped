import time
import logging

from robot_interface import RobotInterface
from q8_gait_controller import Q8GaitController
from wrist_interface import WristInterface
from state_machine import StateMachine

logging.basicConfig(level=logging.INFO)

SAMPLING_RATE = 50.0  # sample at 50 times per second
DT = 1.0 / SAMPLING_RATE


def main() -> None:
    robot = RobotInterface()
    gait = Q8GaitController(default_gait="TROT")
    wrist = WristInterface()
    sm = StateMachine()

    robot.enable_torque()
    logging.info(f"Sampling Rate: {SAMPLING_RATE} Hz")
    logging.info("Using q8bot-based gait controller (TROT). Wrist input currently fake/static.")

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

            gesture = wrist.read_gesture()
            state, command = sm.update(gesture)
            joint_targets = gait.step(DT, command) 

            robot.set_joint_positions(joint_targets) 

            if now - last_print_time > 1.0:
                logging.info(f"State={state.name}, Gesture={gesture}, Command={command}")
                last_print_time = now

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - stopping control loop.")
    finally:
        robot.stop()
        robot.disable_torque()
        logging.info("Shutdown complete.")


if __name__ == "__main__":
    main()
