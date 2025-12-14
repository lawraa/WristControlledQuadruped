## Raspberry Pi Setup

To install the Dynamixel SDK and build required examples:

```bash
./setup_pi.sh
```

Make sure your USB2Dynamixel / USB-RS485 adapter shows up as /dev/ttyUSB0, and give it permissions:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

### Building the tools
From the repo root:

```bash 
cd dynamixel_tools
make

# Example usage:
./walk_basic
```

```bash 
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install scipy
```

## raspi_controller
```bash 
raspi_controller/
  main.py
  gait_controller.py
  state_machine.py
  wrist_interface.py
  robot_interface.py
```

### main.py
At 50 Hz, main.py does the following loop:

1. Read gesture from WristInterface (wrist_interface.py)
    - currently only gives forward gesture -> will later implement reading EMG/IMU data, classify gestures(require training a model), and return commands like "forward", "turn_left", etc.

2. Update state machine (state_machine.py)
    - decides whether we’re IDLE, MOVING, or SAFETY_STOP (cann add more states later)

3. Generate joint targets (GaitController.step)
    - returns a dict: joint_name → angle_offset_in_radians

4. Send to motors (robot_interface.py)
    - converts angles → degrees → Dynamixel positions → streams to motor_server as text


### wrist_interface.py
Defines WristInterface class: reads data from the wrist controller over serial and outputs high-level commands like "forward", "turn_left", etc.

- `read_gesture()`:
    - input: none
    - output: str command ("forward", "turn_left", "idle", etc.)
    - will later implement reading EMG/IMU data, classifying gestures (require training a model), and returning commands


### gait_controller.py
Defines GaitController class: generates joint angle offsets based on high-level commands and time.

- `step(command: str, dt: float) -> Dict[str, float]`:
    - input: command string, time delta since last call
    - output: dict of joint_name → angle_offset_in_radians
    - currently implements a simple trot gait for "forward" command; can be extended for more complex gaits and commands   
- `_simple_trot(command: str) -> Dict[str, float]`:
    - input: command string
    - output: dict of joint_name → angle_offset_in_radians
    - defines a simple trot gait with sine wave motion for hips and knees, with turning bias for left/right turns 

### state_machine.py
Defines StateMachine class: manages robot states (IDLE, MOVING, SAFETY_STOP).
- `update(command: str) -> str`:
    - input: command string from WristInterface
    - output: current state string
    - transitions between states based on commands and safety conditions    


### robot_interface.py
Defines RobotInterface class: handles communication with the motor server and sending joint commands.
- `send_joint_commands(joint_commands: Dict[str, float])`:
    - input: dict of joint_name → angle_offset_in_radians
    - output: none
    - converts angles to Dynamixel positions and streams commands to motor server

## dynamixel_tools

Makefile is provided to build tools in dynamixel_tools/ after you have installed the Dynamixel SDK into the your system. Download location example: `/home/dgrant/DynamixelSDK` :

```bash
cd dynamixel_tools
make 
```

1. `motor_server.py`: Runs on Raspberry Pi, interfaces with Dynamixel motors over serial. Listens for joint position commands over TCP socket.

    - in the main loop
    
    ```bash
    while (fgets(line, sizeof(line), stdin)) {
        // Allow "QUIT" to exit cleanly
        if (strncmp(line, "QUIT", 4) == 0) {
            break;
        }

        int pos[8];
        int n = sscanf(line, "%d %d %d %d %d %d %d %d",
                       &pos[0], &pos[1], &pos[2], &pos[3],
                       &pos[4], &pos[5], &pos[6], &pos[7]);
        if (n != NUM_JOINTS) {
            fprintf(stderr, "[motor_server] Expected 8 ints, got %d. Line: %s", n, line);
            fflush(stderr);
            continue;
        }

        // Send positions
        for (int i = 0; i < NUM_JOINTS; ++i) {
            int p = pos[i];
            if (p < 0) p = 0;
            if (p > 1023) p = 1023;

            write2ByteTxRx(port_num, PROTOCOL_VERSION, joint_ids[i],
                           ADDR_RX_GOAL_POSITION, (uint16_t)p);
        }
    }
    ```

    This code reads lines of joint positions from stdin, parses them, and sends the positions to the Dynamixel motors.

    - Example way to send instructions to motor_server from Python:

    ```python
    # This is in an example Python script to send joint positions to motor_server
    
    import subprocess
    # initialize motor_server process
    proc = subprocess.Popen(
        ["./motor_server", "/dev/ttyUSB0", "1000000"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # send joint positions
    example_positions = [512, 512, 512, 512, 512, 512, 512, 512]

    command_str = " ".join(str(p) for p in example_positions) + "\n"

    # command_str will look like: "512 512 512 512 512 512 512 512\n"

    proc.stdin.write(command_str)
    proc.stdin.flush()
    ```

 
