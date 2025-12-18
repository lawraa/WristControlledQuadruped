from q8gait.kinematics_solver import k_solver
from q8gait.config_rx24f import default_config
from q8gait.robot import Robot
from q8gait.motion_runner import MotionRunner
from keyboard_interface import KeyboardInterface

CENTER_DIST = 30
L1 = 33
L2 = 44

def main():
    cfg = default_config() 
    robot = Robot(cfg)
    leg = k_solver(CENTER_DIST, L1, L2, L1, L2)

    kb = KeyboardInterface()

    robot.open()
    robot.torque(True)

    runner = MotionRunner(robot, leg, gait_name="TROT", hz=30)

    runner.move_to_neutral(seconds=1.0)

    try:
        runner.loop_forever(kb)
    finally:
        try:
            robot.torque(False)
        finally:
            robot.close()

if __name__ == "__main__":
    main()
