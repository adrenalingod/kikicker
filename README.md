# kikicker

Installing on a fresh Raspberry Pi 4B/5:
1. Run the [Raspberry Pi Imager](https://downloads.raspberrypi.com/imager/) and install `Other` -> `latest Raspberry Pi OS Lite (no desktop)` with ssh access as an extra setting
2. Once this is written to the sd card and running in the Raspberry Pi, connect to it via ssh (username pi, password raspberry)
3. Update with: `sudo apt update && sudo apt upgrade -y` to ensure all installed packages are the latest 
4. Install [LXQT](https://lxqt-project.org) and the sddm as desktop environment and display manager: `sudo apt install -y lxqt sddm` (this might take a while)
5. Install [xrdp](https://github.com/neutrinolabs/xrdp) (X Remote Desktop Protocol): `sudo apt update && sudo apt install -y xrdp` 
6. Install these Python packages for the camera and OpenCV: `sudo apt install python3-picamera2 python3-opencv `
7. Download our script: `wget https://raw.githubusercontent.com/kristofvl/kikicker/refs/heads/main/main.py`


# Execute program in debug mode (camera)
python main.py --debug

# Questions
