"""
Test script for MG995 servo with PCA9685 servo controller on Raspberry Pi
Connect via SSH or local serial connection
"""

import time
import board
import busio
from adafruit_pca9685 import PCA9685

def initialize_servo_controller():
    """Initialize the PCA9685 servo controller"""
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        pca = PCA9685(i2c, address=0x40)
        pca.frequency = 50  # 50 Hz for standard servos
        print("✓ Servo controller initialized successfully")
        return pca
    except Exception as e:
        print(f"✗ Failed to initialize servo controller: {e}")
        print("  Make sure:")
        print("  - Raspberry Pi I2C is enabled (raspi-config)")
        print("  - PCA9685 is connected to I2C pins (SDA/SCL)")
        print("  - Power is supplied to PCA9685")
        return None

def set_servo_angle(channel, angle):
    """Set servo angle (0 to 170 degrees)"""
    # MG995 servo: 50 Hz frequency
    
    angle = max(0, min(170, angle))
    angle_for_pulse = (angle / 170.0) * 180  # Map 0-170 to 0-180 for pulse
    angle_for_pulse = 180 - angle_for_pulse  # Invert direction
    pulse_ms = 0.5 + (angle_for_pulse / 180.0) * 2.0  # 0.5ms to 2.5ms
    duty_cycle = int((pulse_ms / 20.0) * 65535)  # 20ms period for 50Hz
    channel.duty_cycle = duty_cycle

def test_servo_basic(pca):
    """Test basic servo operations"""
    if pca is None:
        return
    
    print("\n=== Basic Servo Test ===")
    channel = pca.channels[0]  # Using channel 0 (servo 1)
    
    # Center position (85°)
    print("Moving to center (85°)...")
    set_servo_angle(channel, 85)
    time.sleep(2)
    
    # Move to 0°
    print("Moving to 0°...")
    set_servo_angle(channel, 0)
    time.sleep(2)
    
    # Move to 85°
    print("Moving to 85°...")
    set_servo_angle(channel, 85)
    time.sleep(2)
    
    # Move to 170°
    print("Moving to 170°...")
    set_servo_angle(channel, 170)
    time.sleep(2)
    
    # Back to center
    print("Moving back to center (85°)...")
    set_servo_angle(channel, 85)
    print("✓ Basic servo test completed")

def test_servo_sweep(pca, duration=10):
    """Sweep servo from 0° to 170° and back"""
    if pca is None:
        return
    
    print(f"\n=== Servo Sweep Test ({duration}s) ===")
    channel = pca.channels[0]
    
    steps = 17
    step_duration = duration / (steps * 2)
    
    # Sweep 0° to 170°
    for i in range(steps + 1):
        angle = (i / steps) * 170
        set_servo_angle(channel, angle)
        print(f"  Angle: {angle:.0f}°")
        time.sleep(step_duration)
    
    # Sweep 170° back to 0°
    for i in range(steps, -1, -1):
        angle = (i / steps) * 170
        set_servo_angle(channel, angle)
        print(f"  Angle: {angle:.0f}°")
        time.sleep(step_duration)
    
    set_servo_angle(channel, 85)
    print("✓ Sweep test completed")

def test_servo_manual(pca):
    """Interactive manual servo control"""
    if pca is None:
        return
    
    print("\n=== Manual Servo Control ===")
    print("Commands:")
    print("  a <angle> - Set angle (0-170)")
    print("  c         - Center (85°)")
    print("  q         - Quit")
    print()
    
    channel = pca.channels[0]
    
    try:
        while True:
            cmd = input("Enter command: ").strip().lower()
            
            if cmd == 'q':
                set_servo_angle(channel, 85)
                break
            elif cmd == 'c':
                set_servo_angle(channel, 85)
                print("Centered at 85°")
            elif cmd.startswith('a'):
                try:
                    angle = int(cmd.split()[1])
                    angle = max(0, min(170, angle))
                    set_servo_angle(channel, angle)
                    print(f"Angle: {angle}°")
                except:
                    print("Usage: a <angle> (0-170)")
            else:
                print("Unknown command")
    except KeyboardInterrupt:
        set_servo_angle(channel, 85)
        print("\nCentered")

def main():
    """Run servo tests"""
    print("MG995 Servo Test Suite")
    print("=" * 50)
    
    # Initialize
    pca = initialize_servo_controller()
    if pca is None:
        return
    
    print("\nSelect test:")
    print("1. Basic servo test (0°/85°/170°)")
    print("2. Sweep test (0° to 170° and back)")
    print("3. Manual control (interactive)")
    print("4. Run all tests")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            test_servo_basic(pca)
        elif choice == '2':
            test_servo_sweep(pca)
        elif choice == '3':
            test_servo_manual(pca)
        elif choice == '4':
            test_servo_basic(pca)
            time.sleep(2)
            test_servo_sweep(pca)
            time.sleep(2)
            test_servo_manual(pca)
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        # Return to center
        if pca is not None:
            set_servo_angle(pca.channels[0], 85)
        print("\nServo centered. Test complete.")

if __name__ == "__main__":
    main()
