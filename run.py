from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
last_direction = "stop"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/joystick', methods=['POST'])
def joystick():
    global last_direction
    direction = request.json.get("direction", "stop")
    if direction != last_direction:
        last_direction = direction
        print(f"{direction}")  # function for driving here using 'direction'
    return jsonify({"status": "ok", "direction": direction})

@app.route('/mer', methods=['POST'])
def set_mer():
    global mer
    mer = request.json.get("mer", False)
    print("mer :", mer) # toggle on or off MER here using 'mer'
    return jsonify({"status": "ok", "mer": mer})

@app.route('/accessory', methods=['POST'])
def accessory():
    action = request.json.get("action")
    state = request.json.get("state", False)
    print(f"{action} : {state}")
    return jsonify({"status": "ok", "action": action, "state": state})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
