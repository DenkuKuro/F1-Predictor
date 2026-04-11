from flask import Flask, jsonify, request
from flask_cors import CORS
from database import supabase
import openf1
import random
import jolpica

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

# A GET route to retrieve non-spoiler race info (details + entry list) from the DB
# Query param: race_id
@app.route('/api/race-info', methods=['GET'])
def get_race_info():
    race_id = request.args.get('race_id')
    if not race_id:
        return jsonify({"error": "race_id query param is required"}), 400
    try:
        race_row = (
            supabase.table("race")
            .select("race_id, location, race_date, season_year")
            .eq("race_id", race_id)
            .execute()
            .data
        )
        if not race_row:
            return jsonify({"error": "Race not found"}), 404
        race = race_row[0]

        # Compute round number by ordering all races in this season by date
        season_races = (
            supabase.table("race")
            .select("race_id")
            .eq("season_year", race["season_year"])
            .order("race_date")
            .execute()
            .data
        )
        round_num = next(
            (i + 1 for i, r in enumerate(season_races) if r["race_id"] == race["race_id"]),
            None
        )

        details = {
            "race_id": race["race_id"],
            "season": race["season_year"],
            "round": round_num,
            "location": race["location"],
            "date": race["race_date"],
        }

        # Fetch all drivers joined to their team names
        drivers = (
            supabase.table("driver")
            .select("driver_id, first_name, last_name, team_id")
            .order("last_name")
            .execute()
            .data
        )
        teams = supabase.table("team").select("team_id, team_name").execute().data
        team_map = {t["team_id"]: t["team_name"] for t in teams}

        entry_list = [
            {
                "driver_id": d["driver_id"],
                "first_name": d["first_name"],
                "last_name": d["last_name"],
                "team_name": team_map.get(d["team_id"], "Unknown"),
            }
            for d in drivers
        ]

        return jsonify({"details": details, "entry_list": entry_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A GET route to retrieve the 10 most recent races from the database
@app.route('/api/recent-races', methods=['GET'])
def get_recent_races():
    try:
        response = (
            supabase
            .table("race")
            .select("race_id, location, race_date, season_year")
            .order("race_date", desc=True)
            .limit(10)
            .execute()
        )
        # Reshape to match the keys the frontend already expects from the old Jolpica response
        races = [
            {
                "race_id": row["race_id"],
                "season": row["season_year"],
                "name": row["location"],
                "location": row["location"],
                "date": row["race_date"],
            }
            for row in response.data
        ]
        return jsonify(races), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A GET route to retrieve users sorted by total points descending
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        response = (
            supabase.table("users")
            .select("username, total_points")
            .order("total_points", desc=True)
            .execute()
        )
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A GET route to retrieve all predictions stored in the database, enriched with names
@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        preds = (
            supabase.table("prediction")
            .select("pred_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned")
            .order("pred_id")
            .execute()
            .data
        )

        races = supabase.table("race").select("race_id, location, race_date").execute().data
        race_map = {r["race_id"]: f"{r['location']} — {r['race_date']}" for r in races}

        drivers = supabase.table("driver").select("driver_id, first_name, last_name").execute().data
        driver_map = {d["driver_id"]: f"{d['first_name']} {d['last_name']}" for d in drivers}

        enriched = [
            {
                "pred_id": p["pred_id"],
                "race_name": race_map.get(p["race_id"], f"Race #{p['race_id']}"),
                "p1_pick": driver_map.get(p["p1_pick"], f"Driver #{p['p1_pick']}"),
                "p2_pick": driver_map.get(p["p2_pick"], f"Driver #{p['p2_pick']}"),
                "p3_pick": driver_map.get(p["p3_pick"], f"Driver #{p['p3_pick']}"),
                "safety_car_prediction": p["safety_car_prediction"],
                "points_earned": p["points_earned"],
            }
            for p in preds
        ]

        return jsonify(enriched), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# A GET route to retrieve all predictions stored in the database
@app.route('/api/user_predictions/<user_id>', methods=['GET'])
def get_user_predictions(user_id):
    try:
        response = (
            supabase
            .table("prediction")
            .select("pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned")
            .eq("user_id", user_id)
            .order("pred_id")
            .execute()
        )
        print(response)
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
        # Reject duplicate predictions for the same user + race
        existing = (
            supabase.table("prediction")
            .select("pred_id")
            .eq("user_id", user_id)
            .eq("race_id", race_id)
            .execute()
            .data
        )
        if existing:
            return jsonify({"error": "You have already submitted a prediction for this race."}), 409

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
                "points_earned": -1
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
    if check_user_exists(content.get('email', '').strip()) is False:
        try:
            response = supabase.table("users").insert(content).execute()
            return jsonify({"message": "Signed up successfully!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": "User already exists"}), 409
    
# A POST route to log in user and add it to the database
@app.route("/api/login", methods=["POST"])
def login():
    content = request.json or {}
    email = content.get("email", "").lower()
    password = content.get("password", "").lower()
    try:
        response = (
            supabase.table("users")
            .select("user_id, username")
            .eq("email", email)
            .eq("password", password)
            .execute()
        )
        if response.data:
            return jsonify({"message": "Logged in successfully!", "body": response.data[0]}), 201
        return jsonify({"error": "No such user exists"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
# Helper: shared scoring logic used by both calculate-scores routes.
# Takes resolved p1/p2/p3 driver_ids, safety_car_result, and the race_id.
# Updates points_earned on each prediction and total_points on each user.
def _apply_scores(race_id, p1_id, p2_id, p3_id, safety_car_result):
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
        if safety_car_result is not None and pred["safety_car_prediction"] == safety_car_result:
            points += 1

        supabase.table("prediction").update({"points_earned": points}).eq("pred_id", pred["pred_id"]).execute()

        user = supabase.table("users").select("total_points").eq("user_id", pred["user_id"]).execute().data
        if user:
            new_total = user[0]["total_points"] + points
            supabase.table("users").update({"total_points": new_total}).eq("user_id", pred["user_id"]).execute()

    return len(predictions)

@app.route('/api/race_results', methods=['GET'])
def get_race_results():
    # 1. Get the current user ID from the query parameter to exclude them from "other users"
    current_user_id = request.args.get('id')
    
    try:
        # 2. Fetch all available drivers and users from the DB
        all_drivers = supabase.table("driver").select("driver_id, first_name, last_name").execute().data
        all_users = supabase.table("users").select("user_id, username").execute().data

        if not all_drivers or not all_users:
            return jsonify({"error": "Insufficient data in database"}), 400

        # 3. Randomly generate the "Actual Race" results (Top 3)
        # We use random.sample to ensure no duplicate drivers in the podium
        actual_podium = random.sample(all_drivers, 3)
        p1_actual = actual_podium[0]
        p2_actual = actual_podium[1]
        p3_actual = actual_podium[2]
        
        # Simulate a random safety car outcome
        actual_safety_car = random.choice([True, False])

        # 4. Generate predictions for other users and calculate scores
        user_results = []
        
        for user in all_users:
            # Skip the user making the request
            if str(user["user_id"]) == str(current_user_id):
                continue

            # Give this user 3 random driver picks
            user_picks = random.sample(all_drivers, 3)
            user_sc_pred = random.choice([True, False])

            # Calculate score based on your rules: P1=3, P2=2, P3=1, SC=1
            score = 0
            if user_picks[0]["driver_id"] == p1_actual["driver_id"]: score += 300
            if user_picks[1]["driver_id"] == p2_actual["driver_id"]: score += 200
            if user_picks[2]["driver_id"] == p3_actual["driver_id"]: score += 100
            if user_sc_pred == actual_safety_car: score += 10

            user_results.append({
                "username": user["username"],
                "prediction": {
                    "p1": f"{user_picks[0]['first_name']} {user_picks[0]['last_name']}",
                    "p2": f"{user_picks[1]['first_name']} {user_picks[1]['last_name']}",
                    "p3": f"{user_picks[2]['first_name']} {user_picks[2]['last_name']}",
                    "safety_car": user_sc_pred
                },
                "score": score
            })

        # 5. Sort the users list by score (Descending)
        user_results.sort(key=lambda x: x["score"], reverse=True)

        # 6. Return the final JSON structure
        return jsonify({
            "actual_race": {
                "p1": f"{p1_actual['first_name']} {p1_actual['last_name']}",
                "p2": f"{p2_actual['first_name']} {p2_actual['last_name']}",
                "p3": f"{p3_actual['first_name']} {p3_actual['last_name']}",
                "safety_car": actual_safety_car
            },
            "leaderboard": user_results
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

        # Build driver_number -> position map for top 3
        podium_map = {
            p["driver_number"]: p["position"]
            for p in positions
            if p.get("position") in [1, 2, 3]
        }

        # Map driver_number -> last name from OpenF1 (full_name is "First LAST")
        f1_drivers = openf1.get_session_drivers(session_key)
        f1_last_names = {d["driver_number"]: d["full_name"].split()[-1].upper() for d in f1_drivers}

        # Map last name -> driver_id from our DB
        db_drivers = supabase.table("driver").select("driver_id, last_name").execute().data
        db_last_name_map = {d["last_name"].upper(): d["driver_id"] for d in db_drivers}

        def resolve_driver_id(position):
            for num, pos in podium_map.items():
                if pos == position:
                    return db_last_name_map.get(f1_last_names.get(num))
            return None

        p1_id = resolve_driver_id(1)
        p2_id = resolve_driver_id(2)
        p3_id = resolve_driver_id(3)

        if not p1_id or not p2_id or not p3_id:
            return jsonify({"error": "Could not match all podium drivers to DB"}), 422

        # Find the matching race in our DB by session date
        session_date = session.get("date_start", "")[:10]
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

        count = _apply_scores(race_id, p1_id, p2_id, p3_id, safety_car_result)

        return jsonify({
            "message": f"Scores calculated for race_id {race_id}",
            "p1": p1_id, "p2": p2_id, "p3": p3_id,
            "safety_car": safety_car_result,
            "predictions_scored": count,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST /api/calculate-scores/history
# Scores predictions for a historical race using stored results from the race_result table.
# Expects JSON body: { "race_id": <int> }
@app.route("/api/calculate-scores/history", methods=["POST"])
def calculate_scores_history():
    content = request.json or {}
    race_id = content.get("race_id")

    if not race_id:
        return jsonify({"error": "race_id is required"}), 400

    try:
        result_row = (
            supabase.table("race_result")
            .select("p1_driver, p2_driver, p3_driver")
            .eq("race_id", race_id)
            .execute()
            .data
        )
        if not result_row:
            return jsonify({"error": f"No stored result found for race_id {race_id}"}), 404

        p1_id = result_row[0]["p1_driver"]
        p2_id = result_row[0]["p2_driver"]
        p3_id = result_row[0]["p3_driver"]

        count = _apply_scores(race_id, p1_id, p2_id, p3_id, safety_car_result=None)

        return jsonify({
            "message": f"Historical scores calculated for race_id {race_id}",
            "p1": p1_id, "p2": p2_id, "p3": p3_id,
            "safety_car": "not available",
            "predictions_scored": count,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST /api/calculate-scores/pending
# Scores all predictions where points_earned == -1 (not yet calculated).
# Reads race_result from the DB, compares picks, sets points_earned, += user total.
@app.route("/api/calculate-scores/pending", methods=["POST"])
def calculate_scores_pending():
    from collections import defaultdict
    try:
        unscored = (
            supabase.table("prediction")
            .select("pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick")
            .eq("points_earned", -1)
            .execute()
            .data
        )

        if not unscored:
            return jsonify({"message": "No pending predictions to score.", "predictions_scored": 0}), 200

        result_map = {
            r["race_id"]: r
            for r in supabase.table("race_result").select("race_id, p1_driver, p2_driver, p3_driver").execute().data
        }

        by_race = defaultdict(list)
        for pred in unscored:
            by_race[pred["race_id"]].append(pred)

        total_scored = 0
        races_no_result = []

        for race_id, preds in by_race.items():
            result = result_map.get(race_id)
            if not result:
                races_no_result.append(race_id)
                continue

            p1_id = result["p1_driver"]
            p2_id = result["p2_driver"]
            p3_id = result["p3_driver"]

            for pred in preds:
                points = 0
                if pred["p1_pick"] == p1_id:
                    points += 3
                if pred["p2_pick"] == p2_id:
                    points += 2
                if pred["p3_pick"] == p3_id:
                    points += 1

                supabase.table("prediction").update({"points_earned": points}).eq("pred_id", pred["pred_id"]).execute()

                user_row = supabase.table("users").select("total_points").eq("user_id", pred["user_id"]).execute().data
                if user_row:
                    supabase.table("users").update({
                        "total_points": (user_row[0]["total_points"] or 0) + points
                    }).eq("user_id", pred["user_id"]).execute()

                total_scored += 1

        msg = f"Scored {total_scored} prediction(s)."
        if races_no_result:
            msg += f" {len(races_no_result)} race(s) have no result stored yet."
        return jsonify({"message": msg, "predictions_scored": total_scored}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# DELETE /api/predictions/<pred_id>
# Removes a prediction and -= its earned points from the user's total_points.
# If points_earned is -1 (never scored), nothing is subtracted.
@app.route("/api/predictions/<int:pred_id>", methods=["DELETE"])
def delete_prediction(pred_id):
    try:
        pred_row = (
            supabase.table("prediction")
            .select("user_id, points_earned")
            .eq("pred_id", pred_id)
            .execute()
            .data
        )
        if not pred_row:
            return jsonify({"error": "Prediction not found"}), 404

        user_id = pred_row[0]["user_id"]
        points_earned = pred_row[0]["points_earned"]

        supabase.table("prediction").delete().eq("pred_id", pred_id).execute()

        if points_earned > 0:
            user_row = supabase.table("users").select("total_points").eq("user_id", user_id).execute().data
            if user_row:
                supabase.table("users").update({
                    "total_points": max(0, (user_row[0]["total_points"] or 0) - points_earned)
                }).eq("user_id", user_id).execute()

        return jsonify({"message": "Prediction deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def insert_recent_races():
    try:
        recent = jolpica.get_recent_races(n=10)

        # Fetch all existing (race_date, season_year) pairs in one query
        existing_rows = (
            supabase
            .table("race")
            .select("race_date, season_year")
            .execute()
            .data
        )
        existing = {(row["race_date"], str(row["season_year"])) for row in existing_rows}

        to_insert = []
        for race in recent:
            key = (race["date"], str(race["season"]))
            if key not in existing:
                to_insert.append({
                    "location": race["location"],
                    "race_date": race["date"],
                    "season_year": race["season"],
                })

        if to_insert:
            supabase.table("race").insert(to_insert).execute()
            print(f"[seed] Inserted {len(to_insert)} new race(s) into the database.")
        else:
            print("[seed] No new races to insert.")

    except Exception as e:
        print(f"[seed] Warning: could not seed recent races — {e}")


def insert_teams_and_drivers():
    try:
        entries = jolpica.get_current_season_drivers()

        # --- Teams ---
        existing_teams = supabase.table("team").select("team_id, team_name").execute().data
        existing_team_names = {row["team_name"] for row in existing_teams}

        new_team_names = {e["team_name"] for e in entries if e["team_name"]} - existing_team_names
        if new_team_names:
            supabase.table("team").insert([{"team_name": name} for name in new_team_names]).execute()
            print(f"[seed] Inserted {len(new_team_names)} new team(s): {', '.join(new_team_names)}")
        else:
            print("[seed] No new teams to insert.")

        # Refresh full team map after inserts
        all_teams = supabase.table("team").select("team_id, team_name").execute().data
        team_name_to_id = {row["team_name"]: row["team_id"] for row in all_teams}

        # --- Drivers ---
        existing_drivers = supabase.table("driver").select("first_name, last_name").execute().data
        existing_driver_keys = {(row["first_name"], row["last_name"]) for row in existing_drivers}

        to_insert_drivers = []
        for entry in entries:
            key = (entry["first_name"], entry["last_name"])
            if key not in existing_driver_keys:
                to_insert_drivers.append({
                    "first_name": entry["first_name"],
                    "last_name": entry["last_name"],
                    "team_id": team_name_to_id.get(entry["team_name"]),
                })

        if to_insert_drivers:
            supabase.table("driver").insert(to_insert_drivers).execute()
            print(f"[seed] Inserted {len(to_insert_drivers)} new driver(s).")
        else:
            print("[seed] No new drivers to insert.")

    except Exception as e:
        print(f"[seed] Warning: could not seed teams/drivers — {e}")


def insert_race_results():
    try:
        all_races = (
            supabase.table("race")
            .select("race_id, race_date, season_year")
            .execute()
            .data
        )
        existing_ids = {
            row["race_id"]
            for row in supabase.table("race_result").select("race_id").execute().data
        }
        db_drivers = supabase.table("driver").select("driver_id, last_name").execute().data
        last_name_to_id = {d["last_name"].upper(): d["driver_id"] for d in db_drivers}

        # Pre-fetch the round schedule per season (one API call per season, not per race)
        season_schedules = {}
        for race in all_races:
            year = race["season_year"]
            if year not in season_schedules:
                try:
                    season_races = jolpica.get_season_races(year)
                    season_schedules[year] = {r["date"]: int(r["round"]) for r in season_races}
                except Exception as e:
                    print(f"[seed] Could not fetch {year} schedule: {e}")
                    season_schedules[year] = {}

        inserted = 0
        for race in all_races:
            if race["race_id"] in existing_ids:
                continue
            round_num = season_schedules.get(race["season_year"], {}).get(race["race_date"])
            if not round_num:
                print(f"[seed] No Jolpica round for race_id {race['race_id']} ({race['race_date']}) — skipping.")
                continue
            try:
                podium = jolpica.get_race_results(race["season_year"], round_num)
                if len(podium) < 3:
                    print(f"[seed] Incomplete podium for race_id {race['race_id']} — skipping.")
                    continue
                p1_last = next((p["last_name"] for p in podium if p["position"] == 1), "")
                p2_last = next((p["last_name"] for p in podium if p["position"] == 2), "")
                p3_last = next((p["last_name"] for p in podium if p["position"] == 3), "")
                p1_id = last_name_to_id.get(p1_last)
                p2_id = last_name_to_id.get(p2_last)
                p3_id = last_name_to_id.get(p3_last)
                unmatched = [n for n, i in [(p1_last, p1_id), (p2_last, p2_id), (p3_last, p3_id)] if not i]
                if unmatched:
                    print(f"[seed] race_id {race['race_id']}: could not match driver(s) {unmatched} to DB — skipping.")
                    continue
                supabase.table("race_result").insert({
                    "race_id": race["race_id"],
                    "p1_driver": p1_id,
                    "p2_driver": p2_id,
                    "p3_driver": p3_id,
                }).execute()
                inserted += 1
            except Exception as e:
                print(f"[seed] race_id {race['race_id']}: unexpected error — {e}")
                continue

        print(f"[seed] Race results: inserted {inserted} new result(s).")
    except Exception as e:
        print(f"[seed] Warning: could not seed race results — {e}")


insert_recent_races()
insert_teams_and_drivers()
insert_race_results()


if __name__ == '__main__':
    # debug=True allows for live-reloading during development
    app.run(debug=True, port=5000)



