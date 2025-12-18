/*******************************************************************************
* RX-24F Walking Example
* Simple alternating gait for 8-legged robot using Dynamixel RX-24F motors.
* Left legs: 1–4 | Right legs: 5–8
*
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
#define BAUDRATE       1000000
#define DEVICENAME     "/dev/ttyUSB1"
#define TORQUE_ENABLE  1
#define TORQUE_DISABLE 0

// RX-24F position mapping
#define RX_RESOLUTION  1023.0
#define RX_MAX_DEGREES 300.0

// Neutral and swing ranges
#define CENTER_DEG     150.0
#define SWING_RANGE    10.0       // ±10° swing around center
#define STEP_DELAY_S   1.0        // seconds per step phase

// Convert degrees to Dynamixel position value
#define DEG2POS(deg)   ((int)((deg / RX_MAX_DEGREES) * RX_RESOLUTION))

int main(void)
{
    int port_num = portHandler(DEVICENAME);
    packetHandler();

    if (!openPort(port_num)) {
        printf("Failed to open port!\n");
        return 1;
    }
    if (!setBaudRate(port_num, BAUDRATE)) {
        printf("Failed to set baudrate!\n");
        closePort(port_num);
        return 1;
    }
    printf("✅ Port open at %d baud\n", BAUDRATE);

    double left_forward_deg  = CENTER_DEG - SWING_RANGE; // CW
    double left_backward_deg = CENTER_DEG + SWING_RANGE; // CCW
    double right_forward_deg = CENTER_DEG + SWING_RANGE; // opposite motion
    double right_backward_deg= CENTER_DEG - SWING_RANGE;

    int left_forward_pos  = DEG2POS(left_forward_deg);
    int left_backward_pos = DEG2POS(left_backward_deg);
    int right_forward_pos = DEG2POS(right_forward_deg);
    int right_backward_pos= DEG2POS(right_backward_deg);
    // int center_pos        = DEG2POS(CENTER_DEG);

    // Enable torque for all 8 legs
    for (int id = 1; id <= 8; id++) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_TORQUE_ENABLE, TORQUE_ENABLE);
    }
    printf("Torque enabled for all motors.\n");

    printf("Starting basic walking loop (Ctrl+C to stop)...\n");

    while (1) {
        printf("Step 1: Left legs forward / Right legs backward\n");
        for (int id = 1; id <= 8; id++) {
            if (id <= 4)
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, left_forward_pos);
            else
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, right_backward_pos);
        }
        sleep(STEP_DELAY_S);

        printf("Step 2: Left legs backward / Right legs forward\n");
        for (int id = 1; id <= 8; id++) {
            if (id <= 4)
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, left_backward_pos);
            else
                write2ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_GOAL_POSITION, right_forward_pos);
        }
        sleep(STEP_DELAY_S);
    }

    // (Never reached normally)
    for (int id = 1; id <= 8; id++) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, id, ADDR_RX_TORQUE_ENABLE, TORQUE_DISABLE);
    }
    closePort(port_num);
    printf("\n Walking script terminated, torque disabled.\n");
    return 0;
}

