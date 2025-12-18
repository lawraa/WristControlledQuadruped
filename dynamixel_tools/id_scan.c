#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "dynamixel_sdk.h"

#define DEV "/dev/ttyUSB1"
#define PROTO 1.0

int main(int argc, char** argv){
  printf("Dev: %s\n", DEV); 
  if(argc < 2){ printf("Usage: %s <baud>\n", argv[0]); return 1; }
  int baud = atoi(argv[1]);
  int port = portHandler(DEV); packetHandler();
  if(!openPort(port)){ puts("openPort failed"); return 1; }
  if(!setBaudRate(port, baud)){ puts("setBaudRate failed"); return 1; }
  printf("Scanning 1..253 @ %d bps\n", baud);
  for(int id=1; id<=253; ++id){
    uint16_t model = pingGetModelNum(port, PROTO, id);
    int rc = getLastTxRxResult(port, PROTO);
    uint8_t err = getLastRxPacketError(port, PROTO);
    if(rc==COMM_SUCCESS && err==0){
      printf("  ID=%3d  Model=%u\n", id, model);
    }
  }
  closePort(port);
  return 0;
}
