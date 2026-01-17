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
        print(f"Joystick: {direction}")  # Only prints when direction changes
    return jsonify({"status": "ok", "direction": direction})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
