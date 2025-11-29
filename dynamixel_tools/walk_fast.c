/*******************************************************************************
* RX-24F Fast Walking Example
* Faster alternating gait for 8-legged robot using Dynamixel RX-24F motors.
* Left legs: 1–4 | Right legs: 5–8
* CW = toward 0° (forward for left legs, backward for right legs)
*******************************************************************************/

#if defined(__linux__) || defined(__APPLE__)
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#define STDIN_FILENO 0
#elif defined(_WIN32) || defined(_WIN64)
#include <conio.h>
#include <windows.h>
#define sleep(x) Sleep(1000 * (x))
#endif

#include <stdio.h>
#include <stdlib.h>
#include "dynamixel_sdk.h"

// Control table addresses
#define ADDR_RX_TORQUE_ENABLE    24
#define ADDR_RX_GOAL_POSITION    30
#define ADDR_RX_PRESENT_POSITION 36

// Protocol version
#define PROTOCOL_VERSION 1.0

// Default settings
#define BAUDRATE       57600
#define DEVICENAME     "/dev/ttyUSB0"
#define TORQUE_ENABLE  1
#define TORQUE_DISABLE 0

// RX-24F position mapping
#define RX_RESOLUTION  1023.0
#define RX_MAX_DEGREES 300.0

// Neutral and swing parameters (increased speed and range)
#define CENTER_DEG     150.0
#define SWING_RANGE    50.0       // ±50° swing around center
#define STEP_DELAY_S   0.2        // 5× faster than the slow gait

// Convert degrees to Dynamixel position value
#define DEG2POS(deg)   ((int)((deg / RX_MAX_DEGREES) * RX_RESOLUTION))

int main(void)
{
    int port_num = portHandler(DEVICENAME);
    packetHandler();

    if (!openPort(port_num)) {
        printf("Failed to open port.\n");
        return 1;
    }
    if (!setBaudRate(port_num, BAUDRATE)) {
        printf("Failed to set baudrate.\n");
        closePort(port_num);
        return 1;
    }
    printf("Port opened successfully at %d baud.\n", BAUDRATE);

    double left_forward_deg  = CENTER_DEG - SWING_RANGE; // CW
    double left_backward_deg = CENTER_DEG + SWING_RANGE; // CCW
    double right_forward_deg = CENTER_DEG + SWING_RANGE; // opposite motion
    double right_backward_deg= CENTER_DEG - SWING_RANGE;

    int left_forward_pos  = DEG2POS(left_forward_deg);
    int left_backward_pos = DEG2POS(left_backward_deg);
    int right_forward_pos = DEG2POS(right_forward_deg);
    int right_backward_pos= DEG2POS(right_backward_deg);

    // Enable torque for all 8 legs
    for (int id = 1; id <= 8; id++) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_TORQUE_ENABLE, TORQUE_ENABLE);
    }
    printf("Torque enabled for all motors.\n");

    printf("Starting fast walking loop (±50° range, 0.2 s per phase). Press Ctrl+C to stop.\n");

    while (1) {
        printf("Step 1: Left legs forward, right legs backward.\n");
        for (int id = 1; id <= 8; id++) {
            if (id <= 4)
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, left_forward_pos);
            else
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, right_backward_pos);
        }
        sleep(STEP_DELAY_S);

        printf("Step 2: Left legs backward, right legs forward.\n");
        for (int id = 1; id <= 8; id++) {
            if (id <= 4)
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, left_backward_pos);
            else
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, right_forward_pos);
        }
        sleep(STEP_DELAY_S);
    }

    for (int id = 1; id <= 8; id++) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_TORQUE_ENABLE, TORQUE_DISABLE);
    }
    closePort(port_num);
    printf("Walking script terminated. Torque disabled.\n");
    return 0;
}

