set -e

echo "=== Installing system dependencies ==="
sudo apt update
sudo apt install -y git gcc-5 build-essential

echo "=== Cloning DynamixelSDK ==="
if [ ! -d "$HOME/DynamixelSDK" ]; then
  cd ~
  git clone https://github.com/ROBOTIS-GIT/DynamixelSDK.git
fi

echo "=== Building DynamixelSDK for linux_sbc ==="
cd ~/DynamixelSDK/c/build/linux_sbc
make
sudo make install

echo "=== Building protocol 1.0 read_write example ==="
cd ~/DynamixelSDK/c/example/protocol1.0/read_write/linux_sbc
make

echo "=== Done. Remember to give USB permission when you plug in the USB2Dynamixel ==="
echo "    sudo chmod a+rw /dev/ttyUSB0"
