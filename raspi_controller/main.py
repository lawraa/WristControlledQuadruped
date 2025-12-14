import time
import logging

from robot_interface import RobotInterface
from q8_gait_controller import Q8GaitController
from keyboard_interface import KeyboardInterface
from wrist_interface import WristInterface
from state_machine import StateMachine
import argparse
logging.basicConfig(level=logging.INFO)

SAMPLING_RATE = 50.0
DT = 1.0 / SAMPLING_RATE

SEND_EVERY = 1
MAX_LAG_SEC = 0.05 


def main() -> None:
    parser = argparse.ArgumentParser(description="Run quadruped controller.")
    parser.add_argument("--gait", "-g", default="TROT", help="Default gait to use for Q8GaitController.")
    args = parser.parse_args()

    robot = RobotInterface()
    gait = Q8GaitController(default_gait=args.gait)
    kb = KeyboardInterface()
    wrist = WristInterface()
    sm = StateMachine()

    robot.enable_torque()

    # import time

    # tests = [
    #     "front_left_leg_1",
    #     "front_left_leg_2",
    #     "front_right_leg_1",
    #     "front_right_leg_2",
    #     "back_left_leg_1",
    #     "back_left_leg_2",
    #     "back_right_leg_1",
    #     "back_right_leg_2",
    # ]

    # for name in tests:
    #     targets = {j: 0.0 for j in gait.JOINT_NAMES}
    #     targets[name] = 0.15  # rad (~8.6 deg). If too much, try 0.08.
    #     print("Poking:", name, targets[name])
    #     robot.set_joint_positions(targets)
    #     time.sleep(2.0)

    # # back to neutral
    # robot.set_joint_positions({j: 0.0 for j in gait.JOINT_NAMES})
    # time.sleep(2.0)


    logging.info(f"Sampling Rate: {SAMPLING_RATE} Hz (dt={DT:.6f}s)")
    logging.info(f"Motor send every {SEND_EVERY} tick(s) -> effective send rate ~ {SAMPLING_RATE / SEND_EVERY:.1f} Hz")
    logging.info("Using q8bot-based gait controller (TROT) with keyboard input (w/a/s/d).")

    last_print_time = time.perf_counter()
    next_tick = time.perf_counter()
    tick = 0

    try:
        while True:
            now = time.perf_counter()
            if now < next_tick:
                time.sleep(next_tick - now)
                continue
            if now - next_tick > MAX_LAG_SEC:
                next_tick = now
            next_tick += DT

            kb.poll()
            gesture = kb.read_gesture()
            # gesture = wrist.read_gesture()
            
            state, command = sm.update(gesture)

            # print(f"Gesture={gesture} -> Command={command}")
            joint_targets = gait.step(DT, command)
            tick += 1
            if (tick % SEND_EVERY) == 0:
                robot.set_joint_positions(joint_targets)

            if now - last_print_time > 3.0:
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