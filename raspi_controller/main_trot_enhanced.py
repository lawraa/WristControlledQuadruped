from q8gait.kinematics_solver import k_solver
from q8gait.config_rx24f import default_config
from q8gait.robot import Robot
from q8gait.motion_runner import MotionRunner
from keyboard_interface import KeyboardInterface

CENTER_DIST = 30
L1 = 33
L2 = 44

# Custom gait configurations with enhanced parameters
# Format: [stacktype, x0, y0, xrange, yrange, yrange2, s1_count, s2_count]
# - x0: Foot location (forward/backward position)
# - y0: How tall it stands (height)
# - xrange: How big each step is
# - yrange: How high the foot lifts during swing phase
# - yrange2: Extra push/jump power
# - s1_count: Duration of lift/crouch phase
# - s2_count: Duration of ground contact phase

CUSTOM_GAITS = {
    # TROT_LOW_FULL: Low stance (y0=25) but with FULL range of motion
    # - y0=25: Low center of gravity for stability
    # - yrange=20 (same as TROT): High foot lift for ground clearance
    # - xrange=40 (same as TROT): Full stride length
    # This picks up feet higher during low trot for better obstacle clearance
    'TROT_LOW_FULL': ['trot', 15.0, 25, 40, 20, 0, 15, 30],

    # Original TROT for comparison (good jumping with yrange2 added)
    # Updated with yrange2=8 for some jump capability
    'TROT': ['trot', 15.0, 43.36, 40, 20, 8, 15, 30],

    # Original TROT_LOW for comparison (limited foot lift)
    'TROT_LOW': ['trot', 15.0, 25, 20, 10, 0, 15, 30],

    # Jump gaits with enhanced power
    # Lower crouch (y0=30 vs 40) allows more explosive force
    # Higher push (yrange2=30 vs 25) generates more height
    # Longer crouch (s1_count=25 vs 20) stores more energy
    'JUMP': ['jump', 15.0, 30.0, 0, 0, 30, 25, 5],
    'JUMP_FORWARD': ['jump', 15.0, 30.0, 30, 0, 30, 25, 5],
    'JUMP_BACKWARD': ['jump', 15.0, 30.0, -30, 0, 30, 25, 5],
}

def main():
    cfg = default_config()
    robot = Robot(cfg)
    leg = k_solver(CENTER_DIST, L1, L2, L1, L2)

    kb = KeyboardInterface()

    robot.open()
    robot.torque(True)

    # Use TROT_LOW_FULL with full range of motion
    runner = MotionRunner(robot, leg, gait_name="TROT_LOW_FULL", hz=50, custom_gaits=CUSTOM_GAITS)

    # Move to neutral position
    runner.move_to_neutral(seconds=1.0)

    print("=" * 70)
    print("ENHANCED GAIT CONTROLLER - TROT_LOW_FULL with Power Jumping")
    print("=" * 70)
    print()
    print("Active Gait: TROT_LOW_FULL")
    print("  - Low stance (y0=25mm) for stability")
    print("  - Full range of motion (yrange=20, xrange=40)")
    print("  - High foot lift for better ground clearance during trotting")
    print()
    print("Enhanced Jump Configuration:")
    print("  - Lower crouch (y0=30mm vs original 40mm)")
    print("  - More explosive push (yrange2=30 vs original 25)")
    print("  - Longer energy storage (s1_count=25 vs original 20)")
    print("  - Result: Higher, more powerful jumps!")
    print()
    print("Keyboard Controls:")
    print("  w = forward    x = backward")
    print("  a = turn left  d = turn right")
    print("  s/space = stop")
    print()
    print("Jump Controls:")
    print("  j = jump in place")
    print("  j+w = jump forward")
    print("  j+x = jump backward")
    print("  j+a = jump left")
    print("  j+d = jump right")
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
