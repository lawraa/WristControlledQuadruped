#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "dynamixel_sdk.h"

#define DEV   "/dev/ttyUSB1"
#define PROTO 1.0

#define ADDR_BAUD_RATE 4   // Baud Rate register for AX/RX series

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: %s <new_baud>\n", argv[0]);
        printf("Example: %s 115200\n", argv[0]);
        return 1;
    }

    int new_baud = atoi(argv[1]);
    if (new_baud <= 0) {
        printf("Invalid new_baud: %d\n", new_baud);
        return 1;
    }

    // Compute BaudVal = (2000000 / Baud) - 1
    int baud_val = (int)((2000000.0 / (double)new_baud) - 1.0 + 0.5); // round
    if (baud_val < 0 || baud_val > 255) {
        printf("Computed baud_val=%d is out of range for 1-byte Baud Rate.\n", baud_val);
        return 1;
    }

    printf("Dev: %s\n", DEV);
    printf("Setting all servos 1..8 to baud=%d (baud_val=%d)\n", new_baud, baud_val);

    int port = portHandler(DEV);
    packetHandler();

    // TALK TO THEM AT CURRENT BAUD (115200)
    int current_baud = 115200;
    if (!openPort(port)) {
        puts("openPort failed");
        return 1;
    }
    if (!setBaudRate(port, current_baud)) {
        printf("setBaudRate(%d) failed\n", current_baud);
        closePort(port);
        return 1;
    }

    for (int id = 1; id <= 8; ++id) {
        printf("  ID=%d: setting baud_val=%d...\n", id, baud_val);

        write1ByteTxRx(port, PROTO, id, ADDR_BAUD_RATE, (uint8_t)baud_val);

        int rc  = getLastTxRxResult(port, PROTO);
        uint8_t err = getLastRxPacketError(port, PROTO);

        if (rc == COMM_SUCCESS && err == 0) {
            printf("    OK\n");
        } else {
            printf("    FAILED (rc=%d, err=%u)\n", rc, err);
        }
    }

    closePort(port);
    printf("Done. Now re-open the port at %d baud to talk to them.\n", new_baud);
    return 0;
}
