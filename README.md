# Kikicker

A computer vision and BLE-based foosball table scoring system for Raspberry Pi.

## Branch Description

This project extends and improves foosball table automation with the following features:
- Main application structure
- BLE (Bluetooth Low Energy) payload and advertisements
- ROI (Region of Interest) processing
- Ball detection using OpenCV

**Branch maintainer:** Ivan Gortschakow

## Prerequisites

- Raspberry Pi 4B or 5
- MicroSD card (16GB or larger recommended)
- Camera module compatible with Raspberry Pi

## Installation

### 1. Setup Raspberry Pi OS

1. Download and run the [Raspberry Pi Imager](https://downloads.raspberrypi.com/imager/)
2. Select `Other` → `Raspberry Pi OS Lite (64-bit, no desktop)`
3. Configure SSH access in the advanced settings before writing
4. Write the image to your SD card and boot the Raspberry Pi

### 2. Initial System Setup

Connect to your Raspberry Pi via SSH (default username: `pi`, default password: `raspberry`):

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y
```

### 3. Install Desktop Environment

```bash
# Install LXQT desktop environment and SDDM display manager
sudo apt install -y lxqt sddm
```

### 4. Install Remote Desktop Support

```bash
# Install xrdp for remote desktop access
sudo apt update && sudo apt install -y xrdp
```

### 5. Install Python Dependencies

```bash
# Install camera and OpenCV packages
sudo apt install -y python3-picamera2 python3-opencv
```

### 6. Download Application

```bash
# Download the main script
wget https://raw.githubusercontent.com/kristofvl/kikicker/refs/heads/main/main.py
```

## Usage

All commands must be run from the project directory.

### Scan BLE Devices

```bash
# Scan with raw bytes
sudo python3 bla_scanner.py --raw

# Scan with human-readable output (default)
sudo python3 bla_scanner.py
```

### Test BLE Advertising

```bash
# Start test BLE advertising
sudo python3 ble_glib.py
```

### Run Vision System

```bash
# Run kicker vision in debug mode (requires picamera2)
sudo python3 kicker_vision.py --debug
```

### Run Full Application

```bash
# Run complete application in debug mode
python3 main.py --debug
```

## Development

### Debug Mode

The `--debug` flag enables verbose logging and visual output for development and troubleshooting.

### Requirements

- Python 3.7+
- picamera2 (Raspberry Pi camera library)
- OpenCV (cv2)
- BLE libraries (bluez)
- GLib

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Original project by [kristofvl](https://github.com/kristofvl/kikicker)
