from flask import Flask, jsonify, request
from flask_cors import CORS
from database import supabase

app = Flask(__name__)
CORS(app)

# A simple GET route to confirm the backend server is running
@app.route('/')
def home():
    return "F1 Prediction Game!"

# A JSON API route to check backend status
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": "online",
        "team": "StormForge",
        "active": True
    }), 200

# A GET route to retrieve all drivers from the database
@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    try:
        response = (
            supabase
            .table("driver")
            .select("driver_id, first_name, last_name, team_id")
            .order("driver_id")
            .execute()
        )
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A GET route to retrieve all races from the database
@app.route('/api/races', methods=['GET'])
def get_races():
    try:
        response = (
            supabase
            .table("race")
            .select("race_id, location, race_date, season_year")
            .order("race_id")
            .execute()
        )
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A GET route to retrieve all predictions stored in the database
@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        response = (
            supabase
            .table("prediction")
            .select("pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned")
            .order("pred_id")
            .execute()
        )
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A POST route to submit a new race prediction
@app.route('/api/predict', methods=['POST'])
def post_prediction():
    content = request.json or {}

    user_id = content.get("user_id")
    race_id = content.get("race_id")
    p1_pick = content.get("p1_pick")
    p2_pick = content.get("p2_pick")
    p3_pick = content.get("p3_pick")
    safety_car_prediction = content.get("safety_car_prediction", False)

    if not user_id or not race_id:
        return jsonify({"error": "user_id and race_id are required"}), 400

    if not p1_pick or not p2_pick or not p3_pick:
        return jsonify({"error": "p1_pick, p2_pick, and p3_pick are required"}), 400

    if len({p1_pick, p2_pick, p3_pick}) != 3:
        return jsonify({"error": "P1, P2, and P3 picks must all be different"}), 400

    try:
        response = (
            supabase
            .table("prediction")
            .insert({
                "user_id": user_id,
                "race_id": race_id,
                "p1_pick": p1_pick,
                "p2_pick": p2_pick,
                "p3_pick": p3_pick,
                "safety_car_prediction": safety_car_prediction,
                "points_earned": 0
            })
            .execute()
        )

        return jsonify({
            "message": "Prediction inserted successfully",
            "data": response.data
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A POST route to insert a new team into the database
@app.route('/api/teams', methods=['POST'])
def insert_team():
    content = request.json or {}
    team_name = content.get('team_name', '').strip()

    if not team_name:
        return jsonify({"error": "team_name is required"}), 400

    try:
        response = supabase.table("team").insert({"team_name": team_name}).execute()
        return jsonify({"message": "Team inserted", "data": response.data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def check_user_exists(email):
    try:
        response = supabase.table("users").select("email", count="exact").eq("email", email.lower()).execute()
        return response.count > 0
    except Exception as e:
        print("Error checking if user already exists: ", e)
        return False
                            


# A POST route to sign in user and add it to the database
@app.route("/api/sign-in", methods=["POST"])
def signin():
    content = request.json or {}
    print(content)
    if check_user_exists(content.get('email', '').strip()) is False:
        try:
            response = supabase.table("users").insert(content).execute()
            return jsonify({"message": "Signed in successfully!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": "User already exists"}), 409
    

if __name__ == '__main__':
    # debug=True allows for live-reloading during development
    app.run(debug=True, port=5000)



