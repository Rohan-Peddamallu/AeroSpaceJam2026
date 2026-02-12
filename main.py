# Aerospace Jam - code from official docs (https://docs.aerospacejam.org)
from flask import Flask, render_template
from flask_socketio import SocketIO
import random
from bmp180 import BMP180

from picamera2 import Picamera2
import io
import base64

from mpu6050 import mpu6050
import RPi.GPIO as GPIO

app = Flask(__name__)
socketio = SocketIO(app)
bmp = BMP180()
mpu = mpu6050(0x68)

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


def motor_stop():
    """Stops the motor"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)


# Camera - from Camera doc
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(camera_config)
picam2.start()


@app.route('/')
def index():
    return render_template('index.html')


def background_thread():
    while True:
        socketio.sleep(1)
        barometricPressure = bmp.get_pressure()
        accel_data = mpu.get_accel_data()
        gyro_data = mpu.get_gyro_data()
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
    stream = io.BytesIO()
    picam2.capture_file(stream, format='jpeg')
    stream.seek(0)
    b64_image = base64.b64encode(stream.read()).decode('utf-8')
    socketio.emit('new_image', {'image_data': b64_image})
    print("Sent new image to client.")


def main():
    socketio.run(app, host='0.0.0.0', port=80, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
