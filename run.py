from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Store the last direction for demonstration (optional)
last_direction = "stop"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/joystick', methods=['POST'])
def joystick():
    global last_direction
    data = request.json
    direction = data.get('direction', 'stop')
    last_direction = direction
    print(f"Joystick: {direction}")  # For debugging
    return jsonify({"status": "ok", "direction": direction})

if __name__ == '__main__':
    app.run(debug=True)

