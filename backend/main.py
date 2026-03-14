from flask import Flask, jsonify, request

app = Flask(__name__)

# A simple GET route
@app.route('/')
def home():
    return "F1 Prediction Game!"

# A JSON API route
@app.route('/api/status', methods=['GET'])
def get_status():
    data = {
        "status": "online",
        "team": "StormForge",
        "active": True
    }
    return jsonify(data), 200

# A GET route to get all the predictions of a certain race
@app.route("/api/race_predictions", methods=['GET'])
def get_prediction_of_race():
    race_id = request.args.get('type')
    return 200

# A GET rout to get the current race data to perform predictions
@app.route("/api/current_race", methods=['GET'])
def get_prediction_of_race():
    race_id = request.args.get('type')
    return 200
    
# A POST route to receive data
@app.route('/api/predict', methods=['POST'])
def post_prediction():
    content = request.json
    # Logic for processing prediction would go here
    return jsonify({"message": "Prediction received", "data": content}), 201



@app.route("/signin", methods=['POST'])
def signin():
    user_info = request.json
    # add it to data base
    return 200



if __name__ == '__main__':
    # debug=True allows for live-reloading during development
    app.run(debug=True, port=5000)