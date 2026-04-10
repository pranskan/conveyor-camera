#!/usr/bin/env python3
"""
Conveyor camera system - detects red objects and controls servo motor
Red detected: servo to 110°
Red not detected: servo to 170°
Live view available at http://localhost:5000
"""

import cv2
import pyrealsense2 as rs
import numpy as np
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import threading
from flask import Flask, Response

# Initialize servo controller
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

# Shared frame data
latest_frame = None
latest_mask = None
frame_lock = threading.Lock()

# Flask app for live streaming
app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Conveyor Camera</title>
        <style>
            body { background: #1a1a1a; color: #fff; font-family: Arial; text-align: center; margin: 20px; }
            h1 { color: #4CAF50; }
            .streams { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
            .stream { background: #2a2a2a; padding: 10px; border-radius: 10px; }
            .stream h3 { margin: 0 0 10px 0; }
            img { border-radius: 5px; max-width: 640px; width: 100%; }
        </style>
    </head>
    <body>
        <h1>Conveyor Camera Live Feed</h1>
        <div class="streams">
            <div class="stream">
                <h3>Camera Feed</h3>
                <img src="/video_feed">
            </div>
            <div class="stream">
                <h3>Red Mask</h3>
                <img src="/mask_feed">
            </div>
        </div>
    </body>
    </html>
    '''

def generate_frame(feed_type):
    while True:
        with frame_lock:
            if feed_type == 'video' and latest_frame is not None:
                frame = latest_frame.copy()
            elif feed_type == 'mask' and latest_mask is not None:
                frame = latest_mask.copy()
            else:
                time.sleep(0.01)
                continue
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frame('video'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/mask_feed')
def mask_feed():
    return Response(generate_frame('mask'), mimetype='multipart/x-mixed-replace; boundary=frame')

def set_servo_angle(channel, angle):
    """Set servo angle (0 to 170 degrees)"""
    angle = max(0, min(170, angle))
    angle_for_pulse = (angle / 170.0) * 180
    angle_for_pulse = 180 - angle_for_pulse
    pulse_ms = 0.5 + (angle_for_pulse / 180.0) * 2.0
    duty_cycle = int((pulse_ms / 20.0) * 65535)
    channel.duty_cycle = duty_cycle

def detect_red(frame):
    """Detect red objects in frame, return True if red detected, and red_mask for visualization"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Red color range in HSV (two ranges because red wraps around)
    lower_red1 = np.array([0, 150, 150])
    upper_red1 = np.array([5, 255, 255])
    lower_red2 = np.array([175, 150, 150])
    upper_red2 = np.array([180, 255, 255])
    
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    
    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter by minimum area
    large_contours = [c for c in contours if cv2.contourArea(c) > 100]
    
    return len(large_contours) > 0, red_mask, contours

# Initialize RealSense camera
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, rs.format.z16, 30)
pipeline.start(config)

print("Conveyor camera system started")
print("Red detected → Servo to 110°")
print("Red not detected → Servo to 170°")
print("Live view at → http://localhost:5000")
print("Press Ctrl+C to stop\n")

# Start Flask web server in background thread
def start_web():
    app.run(host='0.0.0.0', port=5000, threaded=True)

web_thread = threading.Thread(target=start_web, daemon=True)
web_thread.start()

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            continue
        
        color_image = np.asanyarray(color_frame.get_data())
        
        # Detect red
        red_detected, red_mask, contours = detect_red(color_image)
        
        # Control servo based on detection
        if red_detected:
            set_servo_angle(pca.channels[0], 110)
            status = "RED DETECTED - Servo: 110°"
        else:
            set_servo_angle(pca.channels[0], 170)
            status = "No red - Servo: 170°"
        
        # Draw contours on frame for visualization
        display_frame = color_image.copy()
        large_contours = [c for c in contours if cv2.contourArea(c) > 100]
        cv2.drawContours(display_frame, large_contours, -1, (0, 255, 0), 2)
        
        # Add status text
        cv2.putText(display_frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Update shared frames for web stream
        mask_colored = cv2.cvtColor(red_mask, cv2.COLOR_GRAY2BGR)
        with frame_lock:
            latest_frame = display_frame
            latest_mask = mask_colored
        
        print(f"\r{status}", end="", flush=True)
        
except KeyboardInterrupt:
    print("\n\nStopping...")
    set_servo_angle(pca.channels[0], 90)  # Center servo
    pipeline.stop()
    print("Done!")


