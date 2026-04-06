from flask import Flask, jsonify, request
from flask_cors import CORS
from database import supabase
import openf1

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
                            


# A POST route to sign up a new user and add them to the database
@app.route("/api/sign-up", methods=["POST"])
def signup():
    content = request.json or {}
    print(content)
    if check_user_exists(content.get('email', '').strip()) is False:
        try:
            response = supabase.table("users").insert(content).execute()
            return jsonify({"message": "Signed up successfully!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": "User already exists"}), 409
    

# GET /api/live-race
# Returns the current session's live state: top 3 positions, safety car status,
# and whether the race has finished. The frontend polls this every 30s.
@app.route("/api/live-race", methods=["GET"])
def live_race():
    try:
        session = openf1.get_latest_session()
        if not session:
            return jsonify({"error": "No active session found"}), 404

        session_key = session["session_key"]
        positions = openf1.get_driver_positions(session_key)
        safety_car = openf1.get_safety_car_status(session_key)
        finished = openf1.get_race_finished(session)

        # Sort by position and take top 3
        podium = []
        for p in positions:
            if p.get("position") == 1:
                podium.append(p)

        for p in positions:
            if p.get("position") == 2:
                podium.append(p)

        for p in positions:
            if p.get("position") == 3:
                podium.append(p)

        return jsonify({
            "session_key": session_key,
            "session_name": session.get("session_name"),
            "race_finished": finished,
            "safety_car": safety_car,
            "podium": podium,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST /api/calculate-scores
# Called when a race finishes. Matches OpenF1 podium results to our DB drivers
# by last name, then scores every prediction for that race and updates totals.
#
# Scoring:
#   Correct P1: 3 pts | Correct P2: 2 pts | Correct P3: 1 pt | Safety car: 1 pt
@app.route("/api/calculate-scores", methods=["POST"])
def calculate_scores():
    try:
        session = openf1.get_latest_session()
        if not session:
            return jsonify({"error": "No session found"}), 404

        if not openf1.get_race_finished(session):
            return jsonify({"error": "Race has not finished yet"}), 400

        session_key = session["session_key"]
        positions = openf1.get_driver_positions(session_key)
        safety_car_result = openf1.get_safety_car_status(session_key)

        # Build a map of driver_number -> position for the podium
        podium_map = {}
        for p in positions:
            # 3. Only care about the top 3 finishers
            if p.get("position") in [1, 2, 3]:
                
                # 4. Map the driver's number to their position
                driver_id = p["driver_number"]
                rank = p["position"]
                
                podium_map[driver_id] = rank

        # Get OpenF1 driver details so we can match by last name to our DB
        f1_drivers = openf1.get_session_drivers(session_key)
        # Map driver_number -> last name (OpenF1 full_name is "First LAST")
        f1_last_names = {}
        for d in f1_drivers:
            full_name = d["full_name"]
            
            # Split the name into parts and grab the last part
            last_name = full_name.split()[-1]
            
            # Make the name uppercase (e.g., "HAMILTON")
            clean_name = last_name.upper()
            
            driver_num = d["driver_number"]
            f1_last_names[driver_num] = clean_name

        # Fetch all drivers from our DB
        db_drivers = supabase.table("driver").select("driver_id, last_name").execute().data
        # Map last name (uppercased) -> driver_id
        db_last_name_map = {d["last_name"].upper(): d["driver_id"] for d in db_drivers}

        # Resolve podium positions to our driver_ids
        def resolve_driver_id(position):
            for num, pos in podium_map.items():
                if pos == position:
                    last = f1_last_names.get(num)
                    return db_last_name_map.get(last)
            return None

        p1_id = resolve_driver_id(1)
        p2_id = resolve_driver_id(2)
        p3_id = resolve_driver_id(3)

        if not p1_id or not p2_id or not p3_id:
            return jsonify({"error": "Could not match all podium drivers to DB"}), 422

        # Find the race in our DB by matching the session date
        session_date = session.get("date_start", "")[:10]  # "YYYY-MM-DD"
        race_row = (
            supabase.table("race")
            .select("race_id")
            .eq("race_date", session_date)
            .execute()
            .data
        )
        if not race_row:
            return jsonify({"error": f"No race found in DB for date {session_date}"}), 404
        race_id = race_row[0]["race_id"]

        # Fetch all predictions for this race
        predictions = (
            supabase.table("prediction")
            .select("pred_id, user_id, p1_pick, p2_pick, p3_pick, safety_car_prediction")
            .eq("race_id", race_id)
            .execute()
            .data
        )

        for pred in predictions:
            points = 0
            if pred["p1_pick"] == p1_id:
                points += 3
            if pred["p2_pick"] == p2_id:
                points += 2
            if pred["p3_pick"] == p3_id:
                points += 1
            if pred["safety_car_prediction"] == safety_car_result:
                points += 1

            # Update points_earned on the prediction
            supabase.table("prediction").update({"points_earned": points}).eq("pred_id", pred["pred_id"]).execute()

            # Add to the user's total_points
            user = supabase.table("users").select("total_points").eq("user_id", pred["user_id"]).execute().data
            if user:
                new_total = user[0]["total_points"] + points
                supabase.table("users").update({"total_points": new_total}).eq("user_id", pred["user_id"]).execute()

        return jsonify({
            "message": f"Scores calculated for race_id {race_id}",
            "p1": p1_id, "p2": p2_id, "p3": p3_id,
            "safety_car": safety_car_result,
            "predictions_scored": len(predictions),
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # debug=True allows for live-reloading during development
    app.run(debug=True, port=5000)



