# Conveyor Belt Sorting System

A Raspberry Pi-powered conveyor belt sorting system that uses an Intel RealSense camera to detect red objects and controls an MG995 servo motor to sort them in real-time.

## Demo

[![Demo Video](https://img.youtube.com/vi/mK-RXC5Gd4w/0.jpg)](https://youtu.be/mK-RXC5Gd4w)

## Photos

### Full Setup
![Full Setup - Overview](photos/full_setup.jpg)
![Full Setup - Top View](photos/full_setup_top.jpg)

### Servo & Sorting Arm
![Servo Close-up](photos/servo_closeup.jpg)

### Camera & Electronics
![RealSense Camera & Raspberry Pi](photos/camera_electronics.jpg)

### Conveyor Belt Drive
![Gear Train](photos/gear_train.jpg)
![Belt Motor & Drive](photos/belt_motor.jpg)
![Belt End Roller](photos/belt_end.jpg)

## How It Works

1. The **Intel RealSense D435** camera watches the conveyor belt
2. OpenCV processes the video feed and detects **red objects** using HSV color filtering
3. When red is detected, the **MG995 servo** moves to 110° to sort the object
4. When no red is detected, the servo returns to 170°
5. A **live web dashboard** at `http://localhost:5000` shows the camera feed and red mask in real-time

## Hardware

- Raspberry Pi
- Intel RealSense D435 depth camera
- PCA9685 servo controller
- MG995 servo motor
- Conveyor belt

## Software Dependencies

- Python 3
- OpenCV
- pyrealsense2
- Flask
- adafruit-circuitpython-pca9685
- NumPy

## Files

| File | Description |
|------|-------------|
| `conveyor_camera.py` | Main system — red detection + servo control + live web stream |
| `motor_test.py` | Standalone servo test script for calibrating the MG995 |
| `test_realsense.py` | Standalone RealSense camera test with color detection |

## Usage

```bash
python3 conveyor_camera.py
```

Then open **http://localhost:5000** in your browser to see the live camera feed.

## Wiring

- **PCA9685 SDA** → Raspberry Pi SDA
- **PCA9685 SCL** → Raspberry Pi SCL
- **MG995 servo** → PCA9685 Channel 0
- **RealSense D435** → USB 3.0 port
