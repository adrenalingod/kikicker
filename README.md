# kikicker

Installing on a fresh Raspberry Pi 4B/5:
1. Run the [Raspberry Pi Imager](https://downloads.raspberrypi.com/imager/) and install `Other` -> `latest Raspberry Pi OS Lite (no desktop)` with ssh access as an extra setting
2. Once this is written to the sd card and running in the Raspberry Pi, connect to it via ssh (username pi, password raspberry)
3. Update with: `sudo apt update && sudo apt upgrade -y` to ensure all installed packages are the latest 
4. Install [LXQT](https://lxqt-project.org) and the sddm as desktop environment and display manager: `sudo apt install -y lxqt sddm` (this might take a while)
5. Install [xrdp](https://github.com/neutrinolabs/xrdp) (X Remote Desktop Protocol): `sudo apt update && sudo apt install -y xrdp` 
6. Install these Python packages for the camera and OpenCV: `sudo apt install python3-picamera2 python3-opencv `
7. Download our script: `wget https://raw.githubusercontent.com/kristofvl/kikicker/refs/heads/main/main.py`


Okay I defined the functions. Ask if you have questions

Each frame gives ball coordinate x,y  integer (pixel coordinates of the frame . we work on them not the roi coordinates (doenst matter. just for info) I implemented a quantize function to translate it into the roi coordinates (also doenst matter. just for info))

Functions:
    1. Use prev_pos and curr_pos to compute:
       - current speed (float)
       - current motion angle radians

    2. Decide whether a bounce happened: (i think it is called radians in english. That is what is ment by angle i wont change it everywhere too lazy)
       - Compare current angle vs prev_angle.
       - If |delta_angle| > configured threshold (AND speed is high enough (edge case) dont implement that) => bounce

    3. Decide whether a goal happened:
       - Check if curr_pos lies inside one of the pre-defined goal regions. (angle pierces goal region, no bounce detected, next frame no ball detected sth like this think about that)

    4. Determine the field quadrant:
       - Use curr_pos and pre-defined quadrant boundaries from field_model. ( Just check the coordinate of the bounce frame. should be good enough)

python main.py --simulate-camera --simulate-advertising --debug

python -c "from bla_receiver import BLAReceiver; r=BLAReceiver(simulate=True); r.start(); r.inject_packet(bytes.fromhex('464454f01c80')); r.stop(); print('DONE')"

python main.py
Start with debug windows:
python [main.py](http://_vscodecontentref_/15) --debug
To validate the receiver locally (without Pi/hardware) using an injected sample payload:

python -c "from bla_receiver import BLAReceiver; r=BLAReceiver(simulate=True); r.start(); r.inject_packet(bytes.fromhex('464454f01c80')); r.stop(); print('DONE')"

Send/Broadcast	Bless	Advertiser (Peripheral)
Receive/Scan	Bleak	Observer (Central)
Parse/Unpack	bleparser	Data Processing

python3 -m venv venv
source venv/bin/activate
pip install bleak bless bleparser
