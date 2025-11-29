# ============================
# Build all Dynamixel tools
# ============================

CC      = gcc
CFLAGS  = -I$(HOME)/DynamixelSDK/c/include/dynamixel_sdk
LDFLAGS = -L$(HOME)/DynamixelSDK/c/build/linux_sbc
LIBS    = -ldxl_sbc_c -lpthread

# All executables to build
TOOLS = \
    walk_basic \
    walk_fast \
    id_scan \
    motor_calibration \
    set_baud \
    set_id \
    set_limits \
	motor_server

# Default target: build all
all: $(TOOLS)

# Generic build rule: any .c → binary
%: %.c
	$(CC) $< -o $@ $(CFLAGS) $(LDFLAGS) $(LIBS)

# Remove binaries
clean:
	rm -f $(TOOLS)
