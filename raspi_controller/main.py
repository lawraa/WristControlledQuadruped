import time

from robot_interface import RobotInterface
from gait_controller import GaitController
from wrist_interface import WristInterface
from state_machine import StateMachine
import logging

logging.basicConfig(level=logging.INFO)

SAMPLING_RATE = 50.0 # sample at 50 times per second
DT = 1.0 / SAMPLING_RATE

def main() -> None:
    robot = RobotInterface()
    gait = GaitController()
    wrist = WristInterface()
    sm = StateMachine()

    robot.enable_torque()
    logging.info(f"Sampling Rate: {SAMPLING_RATE} Hz")
    logging.info("Right now using fake wrist input (constant 'forward')")

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
            state, command = sm.update(gesture) # feed in gesture and get command
            joint_targets = gait.step(DT, command) # Given time step DT and command, get joint targets
            robot.set_joint_positions(joint_targets) # send joint targets to robot to move joint motors
            if now - last_print_time > 1.0: # print status every second
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
