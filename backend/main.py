from flask import Flask, jsonify, request
from flask_cors import CORS
from database import supabase
import openf1
import random
import jolpica

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "F1 Prediction Game!"

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "online", "team": "StormForge", "active": True}), 200

@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    try:
        response = supabase.table("driver").select("driver_id, first_name, last_name, team_id").order("driver_id").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/races', methods=['GET'])
def get_races():
    try:
        response = supabase.table("race").select("race_id, location, race_date, season_year").order("race_id").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/race-info', methods=['GET'])
def get_race_info():
    race_id = request.args.get('race_id')
    if not race_id:
        return jsonify({"error": "race_id query param is required"}), 400
    try:
        race_row = supabase.table("race").select("race_id, location, race_date, season_year").eq("race_id", race_id).execute().data
        if not race_row:
            return jsonify({"error": "Race not found"}), 404
        race = race_row[0]

        season_races = supabase.table("race").select("race_id").eq("season_year", race["season_year"]).order("race_date").execute().data
        round_num = next((i + 1 for i, r in enumerate(season_races) if r["race_id"] == race["race_id"]), None)

        drivers = supabase.table("driver").select("driver_id, first_name, last_name, team_id").order("last_name").execute().data
        teams = supabase.table("team").select("team_id, team_name").execute().data
        team_map = {t["team_id"]: t["team_name"] for t in teams}

        return jsonify({
            "details": {
                "race_id": race["race_id"],
                "season": race["season_year"],
                "round": round_num,
                "location": race["location"],
                "date": race["race_date"],
            },
            "entry_list": [
                {
                    "driver_id": d["driver_id"],
                    "first_name": d["first_name"],
                    "last_name": d["last_name"],
                    "team_name": team_map.get(d["team_id"], "Unknown"),
                }
                for d in drivers
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent-races', methods=['GET'])
def get_recent_races():
    try:
        response = supabase.table("race").select("race_id, location, race_date, season_year").order("race_date", desc=True).limit(10).execute()
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

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        response = supabase.table("users").select("username, total_points").order("total_points", desc=True).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        preds = supabase.table("prediction").select("pred_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned").order("pred_id").execute().data
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

@app.route('/api/user_predictions/<user_id>', methods=['GET'])
def get_user_predictions(user_id):
    try:
        response = supabase.table("prediction").select("pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned").eq("user_id", user_id).order("pred_id").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        existing = supabase.table("prediction").select("pred_id").eq("user_id", user_id).eq("race_id", race_id).execute().data
        if existing:
            return jsonify({"error": "You have already submitted a prediction for this race."}), 409

        response = supabase.table("prediction").insert({
            "user_id": user_id,
            "race_id": race_id,
            "p1_pick": p1_pick,
            "p2_pick": p2_pick,
            "p3_pick": p3_pick,
            "safety_car_prediction": safety_car_prediction,
            "points_earned": -1
        }).execute()

        return jsonify({"message": "Prediction inserted successfully", "data": response.data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route("/api/sign-up", methods=["POST"])
def signup():
    content = request.json or {}
    email = content.get('email', '').strip().lower()
    try:
        existing = supabase.table("users").select("email", count="exact").eq("email", email).execute()
        if existing.count > 0:
            return jsonify({"message": "User already exists"}), 409
        response = supabase.table("users").insert(content).execute()
        return jsonify({"message": "Signed up successfully!", "data": response.data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    content = request.json or {}
    email = content.get("email", "").lower()
    password = content.get("password", "").lower()
    try:
        response = supabase.table("users").select("user_id, username").eq("email", email).eq("password", password).execute()
        if response.data:
            return jsonify({"message": "Logged in successfully!", "body": response.data[0]}), 201
        return jsonify({"error": "No such user exists"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/live-race", methods=["GET"])
def live_race():
    try:
        session = openf1.get_latest_session()
        if not session:
            return jsonify({"error": "No active session found"}), 404

        session_key = session["session_key"]
        positions = openf1.get_driver_positions(session_key)
        podium = sorted([p for p in positions if p.get("position") in [1, 2, 3]], key=lambda x: x["position"])

        return jsonify({
            "session_key": session_key,
            "session_name": session.get("session_name"),
            "race_finished": openf1.get_race_finished(session),
            "safety_car": openf1.get_safety_car_status(session_key),
            "podium": podium,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def score_prediction(p1_pick, p2_pick, p3_pick, sc_pick, p1_id, p2_id, p3_id, sc_actual):
    podium = {p1_id, p2_id, p3_id}
    score = 0
    for pick, correct in [(p1_pick, p1_id), (p2_pick, p2_id), (p3_pick, p3_id)]:
        if pick == correct:
            score += 100
        elif pick in podium:
            score += 50
    if sc_pick == sc_actual:
        score += 50
    return score


@app.route('/api/race_results', methods=['GET'])
def get_race_results():
    current_user_id = request.args.get('id')
    race_id = request.args.get('race')

    if not current_user_id or not race_id:
        return jsonify({"error": "id and race query params are required"}), 400

    try:
        all_drivers = supabase.table("driver").select("driver_id, first_name, last_name").execute().data
        driver_map = {d["driver_id"]: f"{d['first_name']} {d['last_name']}" for d in all_drivers}

        # Use stored race result if it exists, otherwise generate and save one
        result_row = supabase.table("race_result").select("p1_driver, p2_driver, p3_driver, safety_car_result").eq("race_id", race_id).execute().data
        if result_row:
            p1_id = result_row[0]["p1_driver"]
            p2_id = result_row[0]["p2_driver"]
            p3_id = result_row[0]["p3_driver"]
            actual_safety_car = result_row[0]["safety_car_result"]
        else:
            p1, p2, p3 = random.sample(all_drivers, 3)
            actual_safety_car = random.choice([True, False])
            p1_id, p2_id, p3_id = p1["driver_id"], p2["driver_id"], p3["driver_id"]
            supabase.table("race_result").insert({
                "race_id": race_id,
                "p1_driver": p1_id,
                "p2_driver": p2_id,
                "p3_driver": p3_id,
                "safety_car_result": actual_safety_car
            }).execute()

        pred_rows = supabase.table("prediction").select("pred_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned").eq("user_id", current_user_id).eq("race_id", race_id).execute().data
        if not pred_rows:
            return jsonify({"error": "You have not submitted a prediction for this race."}), 404

        pred = pred_rows[0]
        username_row = supabase.table("users").select("username, total_points").eq("user_id", current_user_id).execute().data
        username = username_row[0]["username"] if username_row else "You"

        if pred["points_earned"] == -1:
            user_score = score_prediction(pred["p1_pick"], pred["p2_pick"], pred["p3_pick"], pred["safety_car_prediction"], p1_id, p2_id, p3_id, actual_safety_car)
            supabase.table("prediction").update({"points_earned": user_score}).eq("pred_id", pred["pred_id"]).execute()
            current_total = (username_row[0]["total_points"] or 0) if username_row else 0
            supabase.table("users").update({"total_points": current_total + user_score}).eq("user_id", current_user_id).execute()
        else:
            user_score = pred["points_earned"]

        user_result = {
            "username": username,
            "prediction": {
                "p1": driver_map.get(pred["p1_pick"]),
                "p2": driver_map.get(pred["p2_pick"]),
                "p3": driver_map.get(pred["p3_pick"]),
                "safety_car": pred["safety_car_prediction"]
            },
            "score": user_score
        }

        bot_names = ["RaceFan99", "SpeedDemon", "PitWall", "TurboGuy", "ApexHunter", "GridWatcher", "SlipstreamKing"]
        leaderboard = [user_result]
        for name in bot_names:
            picks = random.sample(all_drivers, 3)
            bot_sc = random.choice([True, False])
            bot_score = score_prediction(picks[0]["driver_id"], picks[1]["driver_id"], picks[2]["driver_id"], bot_sc, p1_id, p2_id, p3_id, actual_safety_car)
            leaderboard.append({
                "username": name,
                "prediction": {
                    "p1": f"{picks[0]['first_name']} {picks[0]['last_name']}",
                    "p2": f"{picks[1]['first_name']} {picks[1]['last_name']}",
                    "p3": f"{picks[2]['first_name']} {picks[2]['last_name']}",
                    "safety_car": bot_sc
                },
                "score": bot_score
            })

        leaderboard.sort(key=lambda x: x["score"], reverse=True)

        return jsonify({
            "actual_race": {
                "p1": driver_map.get(p1_id),
                "p2": driver_map.get(p2_id),
                "p3": driver_map.get(p3_id),
                "safety_car": actual_safety_car
            },
            "user_result": user_result,
            "leaderboard": leaderboard
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

        podium_map = {p["driver_number"]: p["position"] for p in positions if p.get("position") in [1, 2, 3]}
        f1_drivers = openf1.get_session_drivers(session_key)
        f1_last_names = {d["driver_number"]: d["full_name"].split()[-1].upper() for d in f1_drivers}
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

        session_date = session.get("date_start", "")[:10]
        race_row = supabase.table("race").select("race_id").eq("race_date", session_date).execute().data
        if not race_row:
            return jsonify({"error": f"No race found in DB for date {session_date}"}), 404
        race_id = race_row[0]["race_id"]

        predictions = supabase.table("prediction").select("pred_id, user_id, p1_pick, p2_pick, p3_pick, safety_car_prediction").eq("race_id", race_id).execute().data
        for pred in predictions:
            points = score_prediction(pred["p1_pick"], pred["p2_pick"], pred["p3_pick"], pred["safety_car_prediction"], p1_id, p2_id, p3_id, safety_car_result)
            supabase.table("prediction").update({"points_earned": points}).eq("pred_id", pred["pred_id"]).execute()
            user_row = supabase.table("users").select("total_points").eq("user_id", pred["user_id"]).execute().data
            if user_row:
                supabase.table("users").update({"total_points": (user_row[0]["total_points"] or 0) + points}).eq("user_id", pred["user_id"]).execute()

        return jsonify({"message": f"Scores calculated for race_id {race_id}", "predictions_scored": len(predictions)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calculate-scores/history", methods=["POST"])
def calculate_scores_history():
    content = request.json or {}
    race_id = content.get("race_id")
    if not race_id:
        return jsonify({"error": "race_id is required"}), 400

    try:
        result_row = supabase.table("race_result").select("p1_driver, p2_driver, p3_driver").eq("race_id", race_id).execute().data
        if not result_row:
            return jsonify({"error": f"No stored result found for race_id {race_id}"}), 404

        p1_id = result_row[0]["p1_driver"]
        p2_id = result_row[0]["p2_driver"]
        p3_id = result_row[0]["p3_driver"]

        predictions = supabase.table("prediction").select("pred_id, user_id, p1_pick, p2_pick, p3_pick, safety_car_prediction").eq("race_id", race_id).execute().data
        for pred in predictions:
            points = score_prediction(pred["p1_pick"], pred["p2_pick"], pred["p3_pick"], pred["safety_car_prediction"], p1_id, p2_id, p3_id, None)
            supabase.table("prediction").update({"points_earned": points}).eq("pred_id", pred["pred_id"]).execute()
            user_row = supabase.table("users").select("total_points").eq("user_id", pred["user_id"]).execute().data
            if user_row:
                supabase.table("users").update({"total_points": (user_row[0]["total_points"] or 0) + points}).eq("user_id", pred["user_id"]).execute()

        return jsonify({"message": f"Historical scores calculated for race_id {race_id}", "predictions_scored": len(predictions)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calculate-scores/pending", methods=["POST"])
def calculate_scores_pending():
    from collections import defaultdict
    try:
        unscored = supabase.table("prediction").select("pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction").eq("points_earned", -1).execute().data
        if not unscored:
            return jsonify({"message": "No pending predictions to score.", "predictions_scored": 0}), 200

        result_map = {r["race_id"]: r for r in supabase.table("race_result").select("race_id, p1_driver, p2_driver, p3_driver, safety_car_result").execute().data}

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
            sc = result.get("safety_car_result")

            for pred in preds:
                points = score_prediction(pred["p1_pick"], pred["p2_pick"], pred["p3_pick"], pred["safety_car_prediction"], p1_id, p2_id, p3_id, sc)
                supabase.table("prediction").update({"points_earned": points}).eq("pred_id", pred["pred_id"]).execute()
                user_row = supabase.table("users").select("total_points").eq("user_id", pred["user_id"]).execute().data
                if user_row:
                    supabase.table("users").update({"total_points": (user_row[0]["total_points"] or 0) + points}).eq("user_id", pred["user_id"]).execute()
                total_scored += 1

        msg = f"Scored {total_scored} prediction(s)."
        if races_no_result:
            msg += f" {len(races_no_result)} race(s) have no result stored yet."
        return jsonify({"message": msg, "predictions_scored": total_scored}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predictions/<int:pred_id>", methods=["DELETE"])
def delete_prediction(pred_id):
    try:
        pred_row = supabase.table("prediction").select("user_id, points_earned").eq("pred_id", pred_id).execute().data
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
        existing_rows = supabase.table("race").select("race_date, season_year").execute().data
        existing = {(row["race_date"], str(row["season_year"])) for row in existing_rows}

        to_insert = [
            {"location": race["location"], "race_date": race["date"], "season_year": race["season"]}
            for race in recent
            if (race["date"], str(race["season"])) not in existing
        ]

        if to_insert:
            supabase.table("race").insert(to_insert).execute()
            print(f"[seed] Inserted {len(to_insert)} new race(s).")
        else:
            print("[seed] No new races to insert.")
    except Exception as e:
        print(f"[seed] Warning: could not seed recent races — {e}")


def insert_teams_and_drivers():
    try:
        entries = jolpica.get_current_season_drivers()

        existing_teams = supabase.table("team").select("team_id, team_name").execute().data
        existing_team_names = {row["team_name"] for row in existing_teams}
        new_team_names = {e["team_name"] for e in entries if e["team_name"]} - existing_team_names

        if new_team_names:
            supabase.table("team").insert([{"team_name": name} for name in new_team_names]).execute()
            print(f"[seed] Inserted {len(new_team_names)} new team(s): {', '.join(new_team_names)}")
        else:
            print("[seed] No new teams to insert.")

        all_teams = supabase.table("team").select("team_id, team_name").execute().data
        team_name_to_id = {row["team_name"]: row["team_id"] for row in all_teams}

        existing_drivers = supabase.table("driver").select("first_name, last_name").execute().data
        existing_driver_keys = {(row["first_name"], row["last_name"]) for row in existing_drivers}

        to_insert_drivers = [
            {"first_name": e["first_name"], "last_name": e["last_name"], "team_id": team_name_to_id.get(e["team_name"])}
            for e in entries
            if (e["first_name"], e["last_name"]) not in existing_driver_keys
        ]

        if to_insert_drivers:
            supabase.table("driver").insert(to_insert_drivers).execute()
            print(f"[seed] Inserted {len(to_insert_drivers)} new driver(s).")
        else:
            print("[seed] No new drivers to insert.")
    except Exception as e:
        print(f"[seed] Warning: could not seed teams/drivers — {e}")


def insert_race_results():
    try:
        all_races = supabase.table("race").select("race_id, race_date, season_year").execute().data
        existing_ids = {row["race_id"] for row in supabase.table("race_result").select("race_id").execute().data}
        db_drivers = supabase.table("driver").select("driver_id, last_name").execute().data
        last_name_to_id = {d["last_name"].upper(): d["driver_id"] for d in db_drivers}

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
                p1_id = last_name_to_id.get(next((p["last_name"] for p in podium if p["position"] == 1), "").upper())
                p2_id = last_name_to_id.get(next((p["last_name"] for p in podium if p["position"] == 2), "").upper())
                p3_id = last_name_to_id.get(next((p["last_name"] for p in podium if p["position"] == 3), "").upper())
                if not p1_id or not p2_id or not p3_id:
                    print(f"[seed] race_id {race['race_id']}: could not match all podium drivers to DB — skipping.")
                    continue
                supabase.table("race_result").insert({
                    "race_id": race["race_id"],
                    "p1_driver": p1_id,
                    "p2_driver": p2_id,
                    "p3_driver": p3_id,
                    "safety_car_result": random.choice([True, False]),
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
    app.run(debug=True, port=5000)
