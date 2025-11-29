#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#include "dynamixel_sdk.h"

#define ADDR_RX_TORQUE_ENABLE    24
#define ADDR_RX_GOAL_POSITION    30
#define PROTOCOL_VERSION         1.0
#define BAUDRATE       57600
#define DEVICENAME     "/dev/ttyUSB0"
#define TORQUE_ENABLE  1
#define TORQUE_DISABLE 0

int main(void)
{
    // Joint IDs in fixed order: 1..8
    const int NUM_JOINTS = 8;
    uint8_t joint_ids[8] = {1,2,3,4,5,6,7,8};

    // Initialize port and packet handlers
    int port_num = portHandler(DEVICENAME);
    packetHandler();

    if (!openPort(port_num)) {
        fprintf(stderr, "[motor_server] Failed to open port %s\n", DEVICENAME);
        return 1;
    }
    if (!setBaudRate(port_num, BAUDRATE)) {
        fprintf(stderr, "[motor_server] Failed to set baudrate %d\n", BAUDRATE);
        closePort(port_num);
        return 1;
    }
    fprintf(stdout, "[motor_server] Port open on %s @ %d\n", DEVICENAME, BAUDRATE);
    fflush(stdout);

    // Enable torque
    for (int i = 0; i < NUM_JOINTS; ++i) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, joint_ids[i],
                       ADDR_RX_TORQUE_ENABLE, TORQUE_ENABLE);
    }
    fprintf(stdout, "[motor_server] Torque enabled on IDs 1..8\n");
    fflush(stdout);

    // Main loop: read lines from stdin
    char line[256];
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

    // Disable torque
    for (int i = 0; i < NUM_JOINTS; ++i) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, joint_ids[i],
                       ADDR_RX_TORQUE_ENABLE, TORQUE_DISABLE);
    }

    closePort(port_num);
    fprintf(stdout, "[motor_server] Exiting, torque disabled and port closed.\n");
    fflush(stdout);
    return 0;
}
