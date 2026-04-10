#!/usr/bin/env python3
"""Stream RealSense D435 video feed over HTTP"""

import cv2
import pyrealsense2 as rs
from flask import Flask, render_template_string, Response
import numpy as np

app = Flask(__name__)

# RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, rs.format.z16, 30)

pipeline.start(config)

def generate_frames():
    """Generate frames from RealSense camera with blue color detection"""
    try:
        while True:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                continue
            
            # Convert to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
            
            # Define red color range in HSV
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            # Create mask for red colors (two ranges because red wraps around)
            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            # Apply morphological operations to separate individual objects
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours of red objects
            contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by minimum area to detect individual LEGOs
            min_area = 100  # Smaller for individual LEGOs
            large_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            # Draw contours on color image
            color_with_detection = color_image.copy()
            cv2.drawContours(color_with_detection, large_contours, -1, (0, 255, 0), 2)
            
            # Add text with count
            red_count = len(large_contours)
            cv2.putText(color_with_detection, f"Red objects: {red_count}", 
                       (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Normalize depth for display
            depth_image_normalized = cv2.normalize(depth_image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            # Invert so closer = warm colors (red), farther = cool colors (blue)
            depth_image_normalized = 255 - depth_image_normalized
            depth_image_colored = cv2.applyColorMap(depth_image_normalized, cv2.COLORMAP_JET)
            
            # Concatenate side by side
            combined = cv2.hconcat([color_with_detection, depth_image_colored])
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', combined)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        pipeline.stop()

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RealSense D435 Stream</title>
        <style>
            body { font-family: Arial; text-align: center; }
            img { max-width: 100%; height: auto; }
        </style>
    </head>
    <body>
        <h1>RealSense D435 Feed (Color | Depth)</h1>
        <img src="/video_feed" />
    </body>
    </html>
    """)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Starting RealSense stream on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
