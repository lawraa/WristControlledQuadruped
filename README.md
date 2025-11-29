## Raspberry Pi Setup

To install the Dynamixel SDK and build required examples:

```bash
./setup_pi.sh
```

Make sure your USB2Dynamixel / USB-RS485 adapter shows up as /dev/ttyUSB0, and give it permissions:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

### Building the tools
From the repo root:

```bash 
cd dynamixel_tools
make

# Example usage:
./walk_basic
```
