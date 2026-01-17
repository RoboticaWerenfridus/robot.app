from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import json
import atexit

app = Flask(__name__)
last_direction = "stop"

with open("config.json") as f:
    config = json.load(f)

BACKWARDS_ENABLED = config.get("backwards_enabled", False)
MOTORS = config["motors"]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

USED_PINS = set()

for side in MOTORS.values():
    for pin in side.values():
        USED_PINS.add(pin)

for pin in USED_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def stop():
    for pin in USED_PINS:
        GPIO.output(pin, GPIO.LOW)

def forward():
    GPIO.output(MOTORS["left"]["forward"], GPIO.HIGH)
    GPIO.output(MOTORS["right"]["forward"], GPIO.HIGH)

def backward():
    if not BACKWARDS_ENABLED:
        stop()
        return
    GPIO.output(MOTORS["left"]["backward"], GPIO.HIGH)
    GPIO.output(MOTORS["right"]["backward"], GPIO.HIGH)

def left():
    if BACKWARDS_ENABLED:
        GPIO.output(MOTORS["left"]["backward"], GPIO.HIGH)
        GPIO.output(MOTORS["right"]["forward"], GPIO.HIGH)
    else:
        GPIO.output(MOTORS["right"]["forward"], GPIO.HIGH)

def right():
    if BACKWARDS_ENABLED:
        GPIO.output(MOTORS["left"]["forward"], GPIO.HIGH)
        GPIO.output(MOTORS["right"]["backward"], GPIO.HIGH)
    else:
        GPIO.output(MOTORS["left"]["forward"], GPIO.HIGH)

def drive(direction):
    stop()

    if direction == "up":
        forward()
    elif direction == "down":
        backward()
    elif direction == "left":
        left()
    elif direction == "right":
        right()
    else:
        stop()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/joystick', methods=['POST'])
def joystick():
    global last_direction

    direction = request.json.get("direction", "stop")

    if direction != last_direction:
        last_direction = direction
        drive(direction)
        print(f"Direction: {direction}")

    return jsonify({
        "status": "ok",
        "direction": direction,
        "backwards_enabled": BACKWARDS_ENABLED
    })

@app.route('/mer', methods=['POST'])
def set_mer():
    mer = request.json.get("mer", False)
    print("MER:", mer)
    return jsonify({"status": "ok", "mer": mer})

@app.route('/accessory', methods=['POST'])
def accessory():
    action = request.json.get("action")
    state = request.json.get("state", False)
    print(f"{action}: {state}")
    return jsonify({"status": "ok", "action": action, "state": state})

def cleanup():
    stop()
    GPIO.cleanup()

atexit.register(cleanup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
