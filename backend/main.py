from flask import Flask, jsonify, request

app = Flask(__name__)

# A simple GET route
@app.route('/')
def home():
    return "Hello, SFU Robot Soccer!"

# A JSON API route
@app.route('/api/status', methods=['GET'])
def get_status():
    data = {
        "status": "online",
        "team": "StormForge",
        "active": True
    }
    return jsonify(data), 200

# A POST route to receive data
@app.route('/api/predict', methods=['POST'])
def post_prediction():
    content = request.json
    # Logic for processing prediction would go here
    return jsonify({"message": "Prediction received", "data": content}), 201

if __name__ == '__main__':
    # debug=True allows for live-reloading during development
    app.run(debug=True, port=5000)