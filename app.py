from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import json
import atexit
import subprocess
import os

app = Flask(__name__)
last_direction = "stop"
mer_process = None

# Load config.json relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH) as f:
    config = json.load(f)

BACKWARDS_ENABLED = config.get("backwards_enabled", False)
MOTORS = config["motors"]

LEFT_BIAS = 85
RIGHT_BIAS = 100
PWM_FREQ = 1000

# --- GPIO Setup ---
GPIO.setwarnings(False)
GPIO.cleanup()   

PWM_CHANNELS = {}

# Initialize PWM channels safely
for side, dirs in MOTORS.items():
    for pin in dirs.values():
        GPIO.setmode(GPIO.BCM)  
        GPIO.setup(pin, GPIO.OUT)
        if pin in PWM_CHANNELS:
            PWM_CHANNELS[pin].stop()
        pwm = GPIO.PWM(pin, PWM_FREQ)
        pwm.start(0)
        PWM_CHANNELS[pin] = pwm

# --- Motor Control Functions ---
def stop():
    for pwm in PWM_CHANNELS.values():
        pwm.ChangeDutyCycle(0)

def forward():
    PWM_CHANNELS[MOTORS["left"]["forward"]].ChangeDutyCycle(LEFT_BIAS)
    PWM_CHANNELS[MOTORS["right"]["forward"]].ChangeDutyCycle(RIGHT_BIAS)

def backward():
    if not BACKWARDS_ENABLED:
        stop()
        return
    PWM_CHANNELS[MOTORS["left"]["backward"]].ChangeDutyCycle(LEFT_BIAS)
    PWM_CHANNELS[MOTORS["right"]["backward"]].ChangeDutyCycle(RIGHT_BIAS)

def left():
    PWM_CHANNELS[MOTORS["right"]["forward"]].ChangeDutyCycle(RIGHT_BIAS)
    if BACKWARDS_ENABLED:
        PWM_CHANNELS[MOTORS["left"]["backward"]].ChangeDutyCycle(LEFT_BIAS)

def right():
    PWM_CHANNELS[MOTORS["left"]["forward"]].ChangeDutyCycle(LEFT_BIAS)
    if BACKWARDS_ENABLED:
        PWM_CHANNELS[MOTORS["right"]["backward"]].ChangeDutyCycle(RIGHT_BIAS)

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

# --- Flask Routes ---
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
    return jsonify(status="ok", direction=direction, backwards_enabled=BACKWARDS_ENABLED)

@app.route('/mer', methods=['POST'])
def set_mer():
    global mer_process
    mer = request.json.get("mer", False)
    mer_script = os.path.join(BASE_DIR, "mer_us_sv.py")
    if mer and mer_process is None:
        mer_process = subprocess.Popen(["python3", mer_script])
    elif not mer and mer_process is not None:
        mer_process.terminate()
        mer_process.wait()
        mer_process = None
    return jsonify(status="ok", mer=mer)

@app.route('/accessory', methods=['POST'])
def accessory():
    return jsonify(status="ok", **request.json)

# --- Cleanup on exit ---
def cleanup():
    stop()
    for pwm in PWM_CHANNELS.values():
        pwm.stop()
    GPIO.cleanup()
    if mer_process:
        mer_process.terminate()

atexit.register(cleanup)

# --- Run Flask ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
