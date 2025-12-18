from q8gait.kinematics_solver import k_solver
from q8gait.config_rx24f import default_config
from q8gait.robot import Robot
from q8gait.motion_runner import MotionRunner
from keyboard_interface import KeyboardInterface

CENTER_DIST = 30
L1 = 33
L2 = 44

# Custom gait configurations with enhanced jumping
# This uses regular TROT (normal height) but with ENHANCED jump power

CUSTOM_GAITS = {
    # Regular TROT at normal height (y0=43.36)
    # Good for stable trotting and now optimized for jumping
    'TROT': ['trot', 15.0, 43.36, 40, 20, 0, 15, 30],

    # Enhanced jump gaits with LOWER CROUCH for MORE POWER
    # Original: y0=40.0, yrange2=25, s1_count=20
    # Enhanced: y0=30.0, yrange2=35, s1_count=30
    # - Lower crouch (y0=30 vs 40): More room to push off
    # - Higher push (yrange2=35 vs 25): More explosive force
    # - Longer crouch (s1_count=30 vs 20): More energy storage
    'JUMP': ['jump', 15.0, 30.0, 0, 0, 35, 30, 5],
    'JUMP_FORWARD': ['jump', 15.0, 30.0, 35, 0, 35, 30, 5],
    'JUMP_BACKWARD': ['jump', 15.0, 30.0, -35, 0, 35, 30, 5],
}

def main():
    cfg = default_config()
    robot = Robot(cfg)
    leg = k_solver(CENTER_DIST, L1, L2, L1, L2)

    kb = KeyboardInterface()

    robot.open()
    robot.torque(True)

    # Use regular TROT with enhanced jumping
    runner = MotionRunner(robot, leg, gait_name="TROT", hz=50, custom_gaits=CUSTOM_GAITS)

    # Move to neutral position
    runner.move_to_neutral(seconds=1.0)

    print("=" * 70)
    print("TROT with ENHANCED JUMPING - Maximum Jump Power")
    print("=" * 70)
    print()
    print("Active Gait: TROT (Normal Height)")
    print("  - Normal stance (y0=43.36mm) for balanced mobility")
    print("  - Full range of motion (yrange=20, xrange=40)")
    print("  - Good for stable trotting forward/backward")
    print()
    print("ENHANCED Jump Configuration (Maximum Power):")
    print("  - VERY LOW crouch (y0=30mm vs original 40mm)")
    print("  - MAXIMUM explosive push (yrange2=35 vs original 25)")
    print("  - EXTENDED energy storage (s1_count=30 vs original 20)")
    print("  - Result: HIGHEST possible jumps with maximum power!")
    print()
    print("Comparison with TROT_LOW_FULL:")
    print("  - TROT (this script): Better jumping from higher stance")
    print("  - TROT_LOW_FULL: Better stability, more ground clearance when walking")
    print()
    print("Keyboard Controls:")
    print("  w = forward    x = backward")
    print("  a = turn left  d = turn right")
    print("  s/space = stop")
    print()
    print("Jump Controls:")
    print("  j = jump in place (ENHANCED POWER)")
    print("  j+w = jump forward (ENHANCED POWER)")
    print("  j+x = jump backward (ENHANCED POWER)")
    print("  j+a = jump left (ENHANCED POWER)")
    print("  j+d = jump right (ENHANCED POWER)")
    print()
    print("Ctrl+C to exit")
    print("=" * 70)

    try:
        runner.loop_forever(kb)
    finally:
        try:
            robot.torque(False)
        finally:
            robot.close()

if __name__ == "__main__":
    main()
