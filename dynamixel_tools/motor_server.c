#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#include "dynamixel_sdk.h"

#define ADDR_RX_TORQUE_ENABLE    24
#define ADDR_RX_GOAL_POSITION    30
#define ADDR_RX_MOVING_SPEED     32

#define PROTOCOL_VERSION         1.0
#define BAUDRATE       1000000
// baud rates: 9600, 57600, 115200, 1000000
#define DEVICENAME     "/dev/ttyUSB0"
#define TORQUE_ENABLE  1
#define TORQUE_DISABLE 0

// ---- simple timer helper ----
static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

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

    // Enable torque (TxRx so we know it worked)
    for (int i = 0; i < NUM_JOINTS; ++i) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, joint_ids[i],
                       ADDR_RX_TORQUE_ENABLE, TORQUE_ENABLE);
    }
    fprintf(stdout, "[motor_server] Torque enabled on IDs 1..8\n");
    fflush(stdout);
    
    // Set moving speed to max (TxRx once at startup)
    for (int i = 0; i < NUM_JOINTS; ++i) {
        write2ByteTxRx(port_num, PROTOCOL_VERSION, joint_ids[i],
                       ADDR_RX_MOVING_SPEED, 1023);
    }
    fprintf(stdout, "[motor_server] Moving speed set to max on IDs 1..8\n");
    fflush(stdout);

    // For measuring how many commands per second we receive
    double last_print = now_sec();
    int line_count = 0;

    // Main loop: read lines from stdin
    char line[256];
    while (fgets(line, sizeof(line), stdin)) {
        line_count++;

        // Print lines-per-second once per second
        double t = now_sec();
        if (t - last_print >= 1.0) {
            fprintf(stderr, "[motor_server] Lines per second: %d\n", line_count);
            fflush(stderr);
            line_count = 0;
            last_print = t;
        }

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

        // Send positions (TxOnly = don't wait for reply, much faster)
        for (int i = 0; i < NUM_JOINTS; ++i) {
            int p = pos[i];
            if (p < 0)   p = 0;
            if (p > 1023) p = 1023;

            write2ByteTxOnly(port_num, PROTOCOL_VERSION, joint_ids[i],
                             ADDR_RX_GOAL_POSITION, (uint16_t)p);
        }
    }

    // Disable torque (TxRx once on shutdown)
    for (int i = 0; i < NUM_JOINTS; ++i) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, joint_ids[i],
                       ADDR_RX_TORQUE_ENABLE, TORQUE_DISABLE);
    }

    closePort(port_num);
    fprintf(stdout, "[motor_server] Exiting, torque disabled and port closed.\n");
    fflush(stdout);
    return 0;
}
