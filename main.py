# These two modules allow us to run a web server.
from flask import Flask, render_template
from flask_socketio import SocketIO
# This module lets us pick random numbers, you can remove it later.
import random

# BMP180 barometric pressure sensor (Pi-only; falls back to mock on Mac for local dev)
try:
    from bmp180 import BMP180
    bmp = BMP180()
    HAS_SENSOR = True
except (ImportError, OSError):
    bmp = None
    HAS_SENSOR = False

# Here, we create the neccesary base app. You don't need to worry about this.
app = Flask(__name__)
socketio = SocketIO(app)

# When someone requests the root page from our web server, we return 'index.html'.
@app.route('/')
def index():
    return render_template('index.html')

# This function runs in the background to transmit data to connected clients.
def background_thread():
    while True:
        # We sleep here for a single second, but this can be increased or decreased depending on how quickly you want data to be pushed to clients.
        socketio.sleep(1)
        # Read barometric pressure from BMP180 (or mock value when sensor not available)
        barometric_pressure = bmp.get_pressure() if HAS_SENSOR else round(1013.25 + random.uniform(-5, 5), 2)
        socketio.emit(
            'update_data',
            {
                'randomNumber': random.randint(1, 100),
                'barometricPressure': barometric_pressure,
            }
        )

# This function runs when someone connects to the server - and all we do is start the background thread to update the data.
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.start_background_task(target=background_thread)


@socketio.on('do_a_thing')
def do_a_thing(msg):
    """Handle button clicks from the client - use this pattern for motors, etc."""
    print(msg.get('hello', 'Button clicked!'))


def main():
    # These specific arguments are required to make sure the webserver is hosted in a consistent spot, so don't change them unless you know what you're doing.
    socketio.run(app, host='0.0.0.0', port=80, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
