/*******************************************************************************
* RX-24F Motor Calibration Example
* Sets Dynamixel RX-24F motors (IDs 1–8) to 150 degrees.
*******************************************************************************/

#if defined(__linux__) || defined(__APPLE__)
#include <fcntl.h>
#include <termios.h>
#define STDIN_FILENO 0
#elif defined(_WIN32) || defined(_WIN64)
#include <conio.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include "dynamixel_sdk.h"  // Dynamixel SDK library

// Control table address for RX-24F
#define ADDR_RX_TORQUE_ENABLE    24
#define ADDR_RX_GOAL_POSITION    30
#define ADDR_RX_PRESENT_POSITION 36

// Protocol version
#define PROTOCOL_VERSION 1.0

// Default settings
#define BAUDRATE       57600
#define DEVICENAME     "/dev/ttyUSB1"   // Linux example
#define TORQUE_ENABLE  1
#define TORQUE_DISABLE 0

// Conversion for 150 degrees
#define TARGET_DEGREES 150.0
#define RX_RESOLUTION  1023.0
#define RX_MAX_DEGREES 300.0
#define GOAL_POSITION_VALUE ((int)((TARGET_DEGREES / RX_MAX_DEGREES) * RX_RESOLUTION))

int main(void)
{
    int port_num = portHandler(DEVICENAME);
    packetHandler();

    if (!openPort(port_num)) {
        printf("❌ Failed to open port!\n");
        return 1;
    }
    printf("✅ Port opened successfully.\n");

    if (!setBaudRate(port_num, BAUDRATE)) {
        printf("❌ Failed to set baudrate!\n");
        closePort(port_num);
        return 1;
    }
    printf("✅ Baudrate set to %d.\n", BAUDRATE);

    printf("\nCalibrating RX-24F motors (IDs 1–8) to %d position (~150°)\n\n", GOAL_POSITION_VALUE);

    for (int dxl_id = 1; dxl_id <= 8; dxl_id++) {
        // Enable Torque
        write1ByteTxRx(port_num, PROTOCOL_VERSION, dxl_id, ADDR_RX_TORQUE_ENABLE, TORQUE_ENABLE);
        int dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION);
        uint8_t dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION);

        if (dxl_comm_result != COMM_SUCCESS)
            printf("[ID:%d] TxRx failed: %d\n", dxl_id, dxl_comm_result);
        else if (dxl_error)
            printf("[ID:%d] Error: %d\n", dxl_id, dxl_error);
        else
            printf("[ID:%d] Torque enabled.\n", dxl_id);

        // Set Goal Position
        write2ByteTxRx(port_num, PROTOCOL_VERSION, dxl_id, ADDR_RX_GOAL_POSITION, GOAL_POSITION_VALUE);
        dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION);
        dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION);

        if (dxl_comm_result != COMM_SUCCESS)
            printf("[ID:%d] TxRx failed: %d\n", dxl_id, dxl_comm_result);
        else if (dxl_error)
            printf("[ID:%d] Error: %d\n", dxl_id, dxl_error);
        else
            printf("[ID:%d] Goal position set to %d.\n", dxl_id, GOAL_POSITION_VALUE);
    }

    printf("\nVerifying positions...\n\n");

    for (int dxl_id = 1; dxl_id <= 8; dxl_id++) {
        int dxl_present_position = read2ByteTxRx(port_num, PROTOCOL_VERSION, dxl_id, ADDR_RX_PRESENT_POSITION);
        int dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION);
        uint8_t dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION);

        if (dxl_comm_result != COMM_SUCCESS)
            printf("[ID:%d] Read failed: %d\n", dxl_id, dxl_comm_result);
        else if (dxl_error)
            printf("[ID:%d] Error: %d\n", dxl_id, dxl_error);
        else
            printf("[ID:%d] Present Position: %d\n", dxl_id, dxl_present_position);
    }

    for (int dxl_id = 1; dxl_id <= 8; dxl_id++) {
        write1ByteTxRx(port_num, PROTOCOL_VERSION, dxl_id, ADDR_RX_TORQUE_ENABLE, TORQUE_DISABLE);
    }

    closePort(port_num);
    printf("\n✅ Calibration complete. All motors moved to ~150° and torque disabled.\n");

    return 0;
}

