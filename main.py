# Aerospace Jam - code from official docs (https://docs.aerospacejam.org)
from flask import Flask, render_template
from flask_socketio import SocketIO
import random
import time

from picamera2 import Picamera2
import io
import base64

import RPi.GPIO as GPIO

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize sensors with error handling
bmp = None
mpu = None

def check_i2c_devices():
    """Check what I2C devices are available"""
    try:
        import subprocess
        result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
        print("I2C devices detected:")
        print(result.stdout)
    except Exception as e:
        print(f"Could not check I2C devices: {e}")

def init_sensors():
    """Initialize sensors with proper error handling"""
    global bmp, mpu
    
    print("Checking I2C devices...")
    check_i2c_devices()
    
    # Initialize BMP180 (barometric pressure sensor)
    try:
        from bmp180 import BMP180
        bmp = BMP180()
        print("BMP180 sensor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize BMP180 sensor: {e}")
        print("Make sure the BMP180 is properly connected to I2C pins")
        bmp = None
    
    # Initialize MPU6050 (accelerometer/gyroscope)
    try:
        from mpu6050 import mpu6050
        mpu = mpu6050(0x68)
        print("MPU6050 sensor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize MPU6050 sensor: {e}")
        print("Make sure the MPU6050 is properly connected to I2C pins")
        mpu = None

# Initialize sensors on startup
init_sensors()

# Motor - from Motor doc
IN1 = 12
IN2 = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)


def motor_forward():
    """Turns the motor forward"""
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)


def motor_backward():
    """Turns the motor backward"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)

#Ip 10.42.0.1
def motor_stop():
    """Stops the motor"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)


# Camera - from Camera doc
picam2 = None

def init_camera():
    """Initialize camera with error handling"""
    global picam2
    try:
        picam2 = Picamera2()
        camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
        picam2.configure(camera_config)
        picam2.start()
        print("Camera initialized successfully")
    except Exception as e:
        print(f"Failed to initialize camera: {e}")
        picam2 = None

# Initialize camera on startup
init_camera()


@app.route('/')
def index():
    return render_template('index.html')


def background_thread():
    while True:
        socketio.sleep(1)
        
        # Get barometric pressure with error handling
        barometricPressure = 0
        if bmp:
            try:
                barometricPressure = bmp.get_pressure()
            except Exception as e:
                print(f"Error reading BMP180: {e}")
                barometricPressure = 0
        
        # Get accelerometer and gyroscope data with error handling
        accel_data = {'x': 0, 'y': 0, 'z': 0}
        gyro_data = {'x': 0, 'y': 0, 'z': 0}
        
        if mpu:
            try:
                accel_data = mpu.get_accel_data()
                gyro_data = mpu.get_gyro_data()
            except Exception as e:
                print(f"Error reading MPU6050: {e}")
                accel_data = {'x': 0, 'y': 0, 'z': 0}
                gyro_data = {'x': 0, 'y': 0, 'z': 0}
        
        socketio.emit(
            'update_data',
            {
                'randomNumber': random.randint(1, 100),
                'barometricPressure': barometricPressure,
                'accel_x': accel_data['x'],
                'accel_y': accel_data['y'],
                'accel_z': accel_data['z'],
                'gyro_x': gyro_data['x'],
                'gyro_y': gyro_data['y'],
                'gyro_z': gyro_data['z'],
            }
        )


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.start_background_task(target=background_thread)


@socketio.on('do_a_thing')
def do_a_thing(msg):
    print(msg['hello'])


@socketio.on('motor_forward')
def handle_motor_forward():
    motor_forward()


@socketio.on('motor_backward')
def handle_motor_backward():
    motor_backward()


@socketio.on('motor_stop')
def handle_motor_stop():
    motor_stop()


@socketio.on('request_image')
def handle_image_request():
    if picam2:
        try:
            stream = io.BytesIO()
            picam2.capture_file(stream, format='jpeg')
            stream.seek(0)
            b64_image = base64.b64encode(stream.read()).decode('utf-8')
            socketio.emit('new_image', {'image_data': b64_image})
            print("Sent new image to client.")
        except Exception as e:
            print(f"Error capturing image: {e}")
            socketio.emit('new_image', {'image_data': '', 'error': 'Camera not available'})
    else:
        print("Camera not initialized")
        socketio.emit('new_image', {'image_data': '', 'error': 'Camera not initialized'})


def cleanup():
    """Clean up GPIO and camera resources"""
    try:
        GPIO.cleanup()
        print("GPIO cleaned up")
    except:
        pass
    
    try:
        if picam2:
            picam2.stop()
            print("Camera stopped")
    except:
        pass

def main():
    try:
        print("Starting Aerospace Jam application...")
        socketio.run(app, host='0.0.0.0', port=80, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cleanup()


if __name__ == '__main__':
    main()
