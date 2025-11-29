#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "dynamixel_sdk.h"

#define DEV "/dev/ttyUSB0"
#define PROTO 1.0
#define ADDR_TORQUE_ENABLE 24
#define ADDR_ID 3

int main(int argc, char** argv){
  if(argc < 4){ printf("Usage: %s <baud> <current_id> <new_id>\n", argv[0]); return 1; }
  int baud = atoi(argv[1]); int cur = atoi(argv[2]); int nw = atoi(argv[3]);
  if(nw==254 || nw<0 || nw>253){ puts("New ID must be 0..253 (not 254)."); return 1; }

  int port = portHandler(DEV); packetHandler();
  if(!openPort(port) || !setBaudRate(port, baud)){ puts("open/set baud failed"); return 1; }

  write1ByteTxRx(port, PROTO, cur, ADDR_TORQUE_ENABLE, 0); // torque off
  int rc = getLastTxRxResult(port, PROTO); uint8_t err = getLastRxPacketError(port, PROTO);
  if(rc!=COMM_SUCCESS||err) printf("Warn: torque off rc=%d err=%u\n", rc, err);

  write1ByteTxRx(port, PROTO, cur, ADDR_ID, (uint8_t)nw);  // write new ID
  rc = getLastTxRxResult(port, PROTO); err = getLastRxPacketError(port, PROTO);
  if(rc!=COMM_SUCCESS||err) { printf("Failed to write ID rc=%d err=%u\n", rc, err); return 1; }

  printf("ID changed: %d -> %d\n", cur, nw);
  closePort(port); return 0;
}
