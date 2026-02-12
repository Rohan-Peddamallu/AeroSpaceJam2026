# Aerospace Jam Template

Aerospace Jam ground control and telemetry example, with:

- **BMP180 barometric pressure sensor** – Reads atmospheric pressure (hPa) from the Pi’s I2C bus. Falls back to mock data when running on a Mac for local development.
- **Client → server interaction** – A button on the page emits a `do_a_thing` event to the Pi, for use as a pattern for motors, servos, etc.

## Running on the Pi

1. Copy this code to `~/teamCode` on your Raspberry Pi running the Aerospace Jam SDK.
2. In **Development Mode**: Open `main.py` in Thonny and click Run. Visit `http://<PI_IP>/` from another device on the same network.
3. In **Competition Mode**: Double-click the Competition Mode shortcut, then visit `http://10.42.0.1/`.

## Running locally (Mac)

For testing without the Pi:

```bash
pip install flask flask-socketio
python main.py
```

Barometric pressure will show mock values. Visit `http://127.0.0.1/` (use `sudo python main.py` if port 80 requires elevated privileges).