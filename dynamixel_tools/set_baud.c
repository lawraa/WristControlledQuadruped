#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "dynamixel_sdk.h"

#define DEV "/dev/ttyUSB0"
#define PROTO 1.0
#define ADDR_TORQUE_ENABLE 24
#define ADDR_BAUD 4

int main(int argc, char** argv){
  if(argc < 4){ printf("Usage: %s <current_baud> <id> <baudnum>\n", argv[0]); 
                printf("Example (57600): %s 57600 2 34\n", argv[0]); return 1; }
  int baud = atoi(argv[1]); int id = atoi(argv[2]); int baudnum = atoi(argv[3]);

  int port = portHandler(DEV); packetHandler();
  if(!openPort(port) || !setBaudRate(port, baud)){ puts("open/set baud failed"); return 1; }

  write1ByteTxRx(port, PROTO, id, ADDR_TORQUE_ENABLE, 0); // torque off
  write1ByteTxRx(port, PROTO, id, ADDR_BAUD, (uint8_t)baudnum);
  int rc = getLastTxRxResult(port, PROTO); uint8_t err = getLastRxPacketError(port, PROTO);
  if(rc!=COMM_SUCCESS||err){ printf("Failed to write baud rc=%d err=%u\n", rc, err); return 1; }

  puts("Baudnum written. Now reconnect at the NEW baud.");
  closePort(port); return 0;
}
