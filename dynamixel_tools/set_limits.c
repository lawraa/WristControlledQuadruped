#include <stdio.h>
#include <stdint.h>
#include "dynamixel_sdk.h"

#define PROTOCOL_VERSION 1.0
#define DEVICENAME "/dev/ttyUSB0"
#define BAUDRATE 57600
#define ID 2

#define ADDR_TORQUE_ENABLE   24
#define ADDR_CW_LIMIT         6
#define ADDR_CCW_LIMIT        8

int main(){
  int low_limit = 0;
  int high_limit = 1023;
  int port = portHandler(DEVICENAME);
  packetHandler();

  if(!openPort(port)){ puts("openPort failed"); return 1; }
  if(!setBaudRate(port, BAUDRATE)){ puts("setBaudRate failed"); return 1; }

  write1ByteTxRx(port, PROTOCOL_VERSION, ID, ADDR_TORQUE_ENABLE, 0);
  write2ByteTxRx(port, PROTOCOL_VERSION, ID, ADDR_CW_LIMIT, low_limit);
  write2ByteTxRx(port, PROTOCOL_VERSION, ID, ADDR_CCW_LIMIT, high_limit);

  int rc = getLastTxRxResult(port, PROTOCOL_VERSION);
  if(rc != COMM_SUCCESS) printf("TxRxResult: %s\n", getTxRxResult(PROTOCOL_VERSION, rc));
  uint8_t err = getLastRxPacketError(port, PROTOCOL_VERSION);
  if(err) printf("RxPacketError: %s\n", getRxPacketError(PROTOCOL_VERSION, err));
  else    printf("Wrote limits: CW=%d, CCW=%d. Now power-cycle the motor.\n", low_limit, high_limit);

  closePort(port);
  return 0;
}
