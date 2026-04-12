from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_conn
import jolpica
import random
from collections import defaultdict

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "F1 Prediction Game!"

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "online", "team": "CMPT354", "active": True}), 200

@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT driver_id, first_name, last_name, team_id FROM driver ORDER BY driver_id")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{"driver_id": r[0], "first_name": r[1], "last_name": r[2], "team_id": r[3]} for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/races', methods=['GET'])
def get_races():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT race_id, location, race_date, season_year FROM race ORDER BY race_id")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{"race_id": r[0], "location": r[1], "race_date": str(r[2]), "season_year": r[3]} for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/race-info', methods=['GET'])
def get_race_info():
    race_id = request.args.get('race_id')
    if not race_id:
        return jsonify({"error": "race_id query param is required"}), 400
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT race_id, location, race_date, season_year FROM race WHERE race_id = %s", (race_id,))
        race_row = cur.fetchone()
        if not race_row:
            cur.close(); conn.close()
            return jsonify({"error": "Race not found"}), 404

        race = {"race_id": race_row[0], "location": race_row[1], "race_date": race_row[2], "season_year": race_row[3]}

        cur.execute("SELECT race_id FROM race WHERE season_year = %s ORDER BY race_date", (race["season_year"],))
        season_race_ids = [r[0] for r in cur.fetchall()]
        round_num = next((i + 1 for i, rid in enumerate(season_race_ids) if rid == race["race_id"]), None)

        cur.execute("""
            SELECT d.driver_id, d.first_name, d.last_name, t.team_name
            FROM driver d
            LEFT JOIN team t ON d.team_id = t.team_id
            ORDER BY d.last_name
        """)
        driver_rows = cur.fetchall()
        cur.close(); conn.close()

        return jsonify({
            "details": {
                "race_id": race["race_id"],
                "season": race["season_year"],
                "round": round_num,
                "location": race["location"],
                "date": str(race["race_date"]),
            },
            "entry_list": [
                {"driver_id": d[0], "first_name": d[1], "last_name": d[2], "team_name": d[3] or "Unknown"}
                for d in driver_rows
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent-races', methods=['GET'])
def get_recent_races():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT race_id, location, race_date, season_year FROM race ORDER BY race_date DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{
            "race_id": r[0], "season": r[3], "name": r[1], "location": r[1], "date": str(r[2]),
        } for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT username, total_points FROM users ORDER BY total_points DESC NULLS LAST")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{"username": r[0], "total_points": r[1]} for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.pred_id,
                   r.location || ' — ' || r.race_date AS race_name,
                   d1.first_name || ' ' || d1.last_name AS p1_pick,
                   d2.first_name || ' ' || d2.last_name AS p2_pick,
                   d3.first_name || ' ' || d3.last_name AS p3_pick,
                   p.safety_car_prediction,
                   p.points_earned
            FROM prediction p
            JOIN race   r  ON p.race_id = r.race_id
            JOIN driver d1 ON p.p1_pick = d1.driver_id
            JOIN driver d2 ON p.p2_pick = d2.driver_id
            JOIN driver d3 ON p.p3_pick = d3.driver_id
            ORDER BY p.pred_id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{
            "pred_id": r[0], "race_name": r[1],
            "p1_pick": r[2], "p2_pick": r[3], "p3_pick": r[4],
            "safety_car_prediction": r[5], "points_earned": r[6],
        } for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user_predictions/<user_id>', methods=['GET'])
def get_user_predictions(user_id):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick,
                   safety_car_prediction, points_earned
            FROM prediction
            WHERE user_id = %s
            ORDER BY pred_id
        """, (user_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{
            "pred_id": r[0], "user_id": r[1], "race_id": r[2],
            "p1_pick": r[3], "p2_pick": r[4], "p3_pick": r[5],
            "safety_car_prediction": r[6], "points_earned": r[7],
        } for r in rows]), 200
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
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT pred_id FROM prediction WHERE user_id = %s AND race_id = %s", (user_id, race_id))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"error": "You have already submitted a prediction for this race."}), 409

        cur.execute("""
            INSERT INTO prediction (user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned)
            VALUES (%s, %s, %s, %s, %s, %s, -1)
            RETURNING pred_id
        """, (user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"message": "Prediction inserted successfully", "data": [{"pred_id": new_id}]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/teams', methods=['POST'])
def insert_team():
    content = request.json or {}
    team_name = content.get('team_name', '').strip()
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO team (team_name) VALUES (%s) RETURNING team_id", (team_name,))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"message": "Team inserted", "data": [{"team_id": new_id}]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sign-up", methods=["POST"])
def signup():
    content = request.json or {}
    email = content.get('email', '').strip().lower()
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        if cur.fetchone()[0] > 0:
            cur.close(); conn.close()
            return jsonify({"message": "User already exists"}), 409

        username = content.get('username', '').strip()
        password = content.get('password', '').strip()
        cur.execute(
            "INSERT INTO users (email, username, password) VALUES (%s, %s, %s) RETURNING user_id, username",
            (email, username, password)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"message": "Signed up successfully!", "data": [{"user_id": row[0], "username": row[1]}]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    content = request.json or {}
    email = content.get("email", "").lower()
    password = content.get("password", "").lower()
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE email = %s AND password = %s", (email, password))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            return jsonify({"message": "Logged in successfully!", "body": {"user_id": row[0], "username": row[1]}}), 201
        return jsonify({"error": "No such user exists"}), 500
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
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("SELECT driver_id, first_name, last_name FROM driver")
        all_drivers = [{"driver_id": r[0], "first_name": r[1], "last_name": r[2]} for r in cur.fetchall()]
        driver_map = {d["driver_id"]: f"{d['first_name']} {d['last_name']}" for d in all_drivers}

        # Use stored race result if it exists, otherwise generate and save one
        cur.execute(
            "SELECT p1_driver, p2_driver, p3_driver, safety_car_result FROM race_result WHERE race_id = %s",
            (race_id,)
        )
        result_row = cur.fetchone()
        if result_row:
            p1_id, p2_id, p3_id, actual_safety_car = result_row
        else:
            p1, p2, p3 = random.sample(all_drivers, 3)
            actual_safety_car = random.choice([True, False])
            p1_id, p2_id, p3_id = p1["driver_id"], p2["driver_id"], p3["driver_id"]
            cur.execute("""
                INSERT INTO race_result (race_id, p1_driver, p2_driver, p3_driver, safety_car_result)
                VALUES (%s, %s, %s, %s, %s)
            """, (race_id, p1_id, p2_id, p3_id, actual_safety_car))
            conn.commit()

        cur.execute("""
            SELECT pred_id, p1_pick, p2_pick, p3_pick, safety_car_prediction, points_earned
            FROM prediction
            WHERE user_id = %s AND race_id = %s
        """, (current_user_id, race_id))
        pred_row = cur.fetchone()
        if not pred_row:
            cur.close(); conn.close()
            return jsonify({"error": "You have not submitted a prediction for this race."}), 404

        pred = {
            "pred_id": pred_row[0], "p1_pick": pred_row[1], "p2_pick": pred_row[2],
            "p3_pick": pred_row[3], "safety_car_prediction": pred_row[4], "points_earned": pred_row[5],
        }

        cur.execute("SELECT username, total_points FROM users WHERE user_id = %s", (current_user_id,))
        user_row = cur.fetchone()
        username = user_row[0] if user_row else "You"

        if pred["points_earned"] == -1:
            user_score = score_prediction(
                pred["p1_pick"], pred["p2_pick"], pred["p3_pick"],
                pred["safety_car_prediction"], p1_id, p2_id, p3_id, actual_safety_car
            )
            cur.execute("UPDATE prediction SET points_earned = %s WHERE pred_id = %s", (user_score, pred["pred_id"]))
            current_total = (user_row[1] or 0) if user_row else 0
            cur.execute("UPDATE users SET total_points = %s WHERE user_id = %s", (current_total + user_score, current_user_id))
            conn.commit()
        else:
            user_score = pred["points_earned"]

        cur.close(); conn.close()

        user_result = {
            "username": username,
            "prediction": {
                "p1": driver_map.get(pred["p1_pick"]),
                "p2": driver_map.get(pred["p2_pick"]),
                "p3": driver_map.get(pred["p3_pick"]),
                "safety_car": pred["safety_car_prediction"],
            },
            "score": user_score,
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
                    "safety_car": bot_sc,
                },
                "score": bot_score,
            })

        leaderboard.sort(key=lambda x: x["score"], reverse=True)

        return jsonify({
            "actual_race": {
                "p1": driver_map.get(p1_id),
                "p2": driver_map.get(p2_id),
                "p3": driver_map.get(p3_id),
                "safety_car": actual_safety_car,
            },
            "user_result": user_result,
            "leaderboard": leaderboard,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calculate-scores/history", methods=["POST"])
def calculate_scores_history():
    content = request.json or {}
    race_id = content.get("race_id")
    if not race_id:
        return jsonify({"error": "race_id is required"}), 400
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT p1_driver, p2_driver, p3_driver FROM race_result WHERE race_id = %s", (race_id,))
        result_row = cur.fetchone()
        if not result_row:
            cur.close(); conn.close()
            return jsonify({"error": f"No stored result found for race_id {race_id}"}), 404

        p1_id, p2_id, p3_id = result_row
        cur.execute("""
            SELECT pred_id, user_id, p1_pick, p2_pick, p3_pick, safety_car_prediction
            FROM prediction WHERE race_id = %s
        """, (race_id,))
        predictions = cur.fetchall()

        for pred_id, user_id, p1_pick, p2_pick, p3_pick, sc in predictions:
            points = score_prediction(p1_pick, p2_pick, p3_pick, sc, p1_id, p2_id, p3_id, None)
            cur.execute("UPDATE prediction SET points_earned = %s WHERE pred_id = %s", (points, pred_id))
            cur.execute("SELECT total_points FROM users WHERE user_id = %s", (user_id,))
            user_row = cur.fetchone()
            if user_row:
                cur.execute("UPDATE users SET total_points = %s WHERE user_id = %s", ((user_row[0] or 0) + points, user_id))

        conn.commit()
        cur.close(); conn.close()
        return jsonify({"message": f"Historical scores calculated for race_id {race_id}", "predictions_scored": len(predictions)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calculate-scores/pending", methods=["POST"])
def calculate_scores_pending():
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT pred_id, user_id, race_id, p1_pick, p2_pick, p3_pick, safety_car_prediction
            FROM prediction WHERE points_earned = -1
        """)
        unscored = cur.fetchall()

        if not unscored:
            cur.close(); conn.close()
            return jsonify({"message": "No pending predictions to score.", "predictions_scored": 0}), 200

        cur.execute("SELECT race_id, p1_driver, p2_driver, p3_driver, safety_car_result FROM race_result")
        result_map = {r[0]: r for r in cur.fetchall()}

        by_race = defaultdict(list)
        for pred in unscored:
            by_race[pred[2]].append(pred)

        total_scored = 0
        races_no_result = []

        for race_id, preds in by_race.items():
            result = result_map.get(race_id)
            if not result:
                races_no_result.append(race_id)
                continue
            _, p1_id, p2_id, p3_id, sc = result
            for pred in preds:
                pred_id, user_id, _, p1_pick, p2_pick, p3_pick, pred_sc = pred
                points = score_prediction(p1_pick, p2_pick, p3_pick, pred_sc, p1_id, p2_id, p3_id, sc)
                cur.execute("UPDATE prediction SET points_earned = %s WHERE pred_id = %s", (points, pred_id))
                cur.execute("SELECT total_points FROM users WHERE user_id = %s", (user_id,))
                user_row = cur.fetchone()
                if user_row:
                    cur.execute("UPDATE users SET total_points = %s WHERE user_id = %s", ((user_row[0] or 0) + points, user_id))
                total_scored += 1

        conn.commit()
        cur.close(); conn.close()

        msg = f"Scored {total_scored} prediction(s)."
        if races_no_result:
            msg += f" {len(races_no_result)} race(s) have no result stored yet."
        return jsonify({"message": msg, "predictions_scored": total_scored}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predictions/<int:pred_id>", methods=["DELETE"])
def delete_prediction(pred_id):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT pred_id FROM prediction WHERE pred_id = %s", (pred_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"error": "Prediction not found"}), 404
        cur.execute("DELETE FROM prediction WHERE pred_id = %s", (pred_id,))
        conn.commit()
        cur.close(); conn.close()
        # total_points is decremented automatically by the DB trigger
        # (trg_subtract_points_on_delete — see schema_extras.sql)
        return jsonify({"message": "Prediction deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── DIVISION: leaderboard filtered by races ────────────────────────────────
@app.route("/api/leaderboard/division", methods=["GET"])
def get_leaderboard_division():
    race_ids_param = request.args.get("race_ids", "").strip()

    if not race_ids_param:
        return get_leaderboard()

    try:
        race_ids = [int(r) for r in race_ids_param.split(",") if r.strip()]
    except ValueError:
        return jsonify({"error": "Invalid race_ids parameter"}), 400

    if not race_ids:
        return get_leaderboard()

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        # Division query — users who have a prediction for EVERY selected race.
        # Equivalent to: users U such that there is no selected race R for which
        # U has no prediction.
        placeholders = ", ".join(["%s"] * len(race_ids))
        sql = f"""
            SELECT u.username, u.total_points
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1
                FROM (SELECT unnest(ARRAY[{placeholders}]::int[]) AS race_id) AS selected_races
                WHERE NOT EXISTS (
                    SELECT 1 FROM prediction p
                    WHERE p.user_id = u.user_id
                      AND p.race_id = selected_races.race_id
                )
            )
            ORDER BY u.total_points DESC NULLS LAST
        """
        cur.execute(sql, race_ids)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{"username": r[0], "total_points": r[1]} for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── AGGREGATION (no GROUP BY): overall prediction stats ───────────────────
@app.route("/api/stats/prediction-summary", methods=["GET"])
def get_prediction_summary():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*)                          AS total_predictions,
                   COUNT(DISTINCT user_id)           AS total_users,
                   MIN(points_earned)                AS min_points,
                   MAX(points_earned)                AS max_points,
                   ROUND(AVG(points_earned), 1)      AS avg_points
            FROM prediction
            WHERE points_earned >= 0
        """)
        row = cur.fetchone()
        cur.close(); conn.close()

        if not row or row[0] == 0:
            return jsonify({"total_predictions": 0, "total_users": 0,
                            "min_points": 0, "max_points": 0, "avg_points": 0.0}), 200

        return jsonify({
            "total_predictions": int(row[0]),
            "total_users":       int(row[1]),
            "min_points":        int(row[2]) if row[2] is not None else 0,
            "max_points":        int(row[3]) if row[3] is not None else 0,
            "avg_points":        float(row[4]) if row[4] is not None else 0.0,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── AGGREGATION WITH GROUP BY + JOIN: predictions grouped by user ──────────
@app.route("/api/predictions/grouped", methods=["GET"])
def get_predictions_grouped():
    user_id = request.args.get("user_id")
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        # GROUP BY query — aggregate stats per user (filtered to user_id if provided)
        if user_id:
            cur.execute("""
                SELECT u.user_id,
                       u.username,
                       COUNT(p.pred_id)                                                          AS prediction_count,
                       COALESCE(SUM(CASE WHEN p.points_earned >= 0 THEN p.points_earned END), 0) AS total_earned,
                       ROUND(AVG(CASE WHEN p.points_earned >= 0 THEN p.points_earned END), 1)    AS avg_points
                FROM users u
                LEFT JOIN prediction p ON u.user_id = p.user_id
                WHERE u.user_id = %s
                GROUP BY u.user_id, u.username
            """, (user_id,))
        else:
            cur.execute("""
                SELECT u.user_id,
                       u.username,
                       COUNT(p.pred_id)                                                          AS prediction_count,
                       COALESCE(SUM(CASE WHEN p.points_earned >= 0 THEN p.points_earned END), 0) AS total_earned,
                       ROUND(AVG(CASE WHEN p.points_earned >= 0 THEN p.points_earned END), 1)    AS avg_points
                FROM users u
                LEFT JOIN prediction p ON u.user_id = p.user_id
                GROUP BY u.user_id, u.username
                ORDER BY total_earned DESC NULLS LAST
            """)
        user_rows = cur.fetchall()

        # JOIN query — individual predictions with all names resolved via SQL JOINs
        if user_id:
            cur.execute("""
                SELECT p.pred_id,
                       p.user_id,
                       r.location                                    AS race_name,
                       r.race_date,
                       d1.first_name || ' ' || d1.last_name         AS p1_driver,
                       d2.first_name || ' ' || d2.last_name         AS p2_driver,
                       d3.first_name || ' ' || d3.last_name         AS p3_driver,
                       p.safety_car_prediction,
                       p.points_earned
                FROM prediction p
                JOIN race   r  ON p.race_id  = r.race_id
                JOIN driver d1 ON p.p1_pick  = d1.driver_id
                JOIN driver d2 ON p.p2_pick  = d2.driver_id
                JOIN driver d3 ON p.p3_pick  = d3.driver_id
                WHERE p.user_id = %s
                ORDER BY r.race_date
            """, (user_id,))
        else:
            cur.execute("""
                SELECT p.pred_id,
                       p.user_id,
                       r.location                                    AS race_name,
                       r.race_date,
                       d1.first_name || ' ' || d1.last_name         AS p1_driver,
                       d2.first_name || ' ' || d2.last_name         AS p2_driver,
                       d3.first_name || ' ' || d3.last_name         AS p3_driver,
                       p.safety_car_prediction,
                       p.points_earned
                FROM prediction p
                JOIN race   r  ON p.race_id  = r.race_id
                JOIN driver d1 ON p.p1_pick  = d1.driver_id
                JOIN driver d2 ON p.p2_pick  = d2.driver_id
                JOIN driver d3 ON p.p3_pick  = d3.driver_id
                ORDER BY p.user_id, r.race_date
            """)
        pred_rows = cur.fetchall()
        cur.close(); conn.close()

        preds_by_user = defaultdict(list)
        for row in pred_rows:
            preds_by_user[row[1]].append({
                "pred_id":               row[0],
                "race_name":             f"{row[2]} — {row[3]}",
                "p1_pick":               row[4],
                "p2_pick":               row[5],
                "p3_pick":               row[6],
                "safety_car_prediction": row[7],
                "points_earned":         row[8],
            })

        result = []
        for row in user_rows:
            uid, username, pred_count, total_earned, avg_points = row
            result.append({
                "user_id":          uid,
                "username":         username,
                "prediction_count": int(pred_count),
                "total_earned":     int(total_earned),
                "avg_points":       float(avg_points) if avg_points is not None else None,
                "predictions":      preds_by_user.get(uid, []),
            })

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── CASCADE: delete user account (predictions cascade automatically) ───────
@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"error": "User not found"}), 404
        # The FK constraint prediction.user_id → users(user_id) ON DELETE CASCADE
        # automatically deletes all predictions belonging to this user.
        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"message": "Account deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def insert_recent_races():
    try:
        recent = jolpica.get_recent_races(n=10)
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT race_date, season_year FROM race")
        existing = {(str(r[0]), str(r[1])) for r in cur.fetchall()}
        to_insert = [
            (race["location"], race["date"], race["season"])
            for race in recent
            if (race["date"], str(race["season"])) not in existing
        ]
        if to_insert:
            cur.executemany("INSERT INTO race (location, race_date, season_year) VALUES (%s, %s, %s)", to_insert)
            conn.commit()
            print(f"[seed] Inserted {len(to_insert)} new race(s).")
        else:
            print("[seed] No new races to insert.")
        cur.close(); conn.close()
    except Exception as e:
        print(f"[seed] Warning: could not seed recent races — {e}")


def insert_teams_and_drivers():
    try:
        entries = jolpica.get_current_season_drivers()
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("SELECT team_name FROM team")
        existing_team_names = {r[0] for r in cur.fetchall()}
        new_team_names = {e["team_name"] for e in entries if e["team_name"]} - existing_team_names

        if new_team_names:
            cur.executemany("INSERT INTO team (team_name) VALUES (%s)", [(n,) for n in new_team_names])
            conn.commit()
            print(f"[seed] Inserted {len(new_team_names)} new team(s): {', '.join(new_team_names)}")
        else:
            print("[seed] No new teams to insert.")

        cur.execute("SELECT team_id, team_name FROM team")
        team_name_to_id = {r[1]: r[0] for r in cur.fetchall()}

        cur.execute("SELECT first_name, last_name FROM driver")
        existing_driver_keys = {(r[0], r[1]) for r in cur.fetchall()}

        to_insert_drivers = [
            (e["first_name"], e["last_name"], team_name_to_id.get(e["team_name"]))
            for e in entries
            if (e["first_name"], e["last_name"]) not in existing_driver_keys
        ]
        if to_insert_drivers:
            cur.executemany("INSERT INTO driver (first_name, last_name, team_id) VALUES (%s, %s, %s)", to_insert_drivers)
            conn.commit()
            print(f"[seed] Inserted {len(to_insert_drivers)} new driver(s).")
        else:
            print("[seed] No new drivers to insert.")

        cur.close(); conn.close()
    except Exception as e:
        print(f"[seed] Warning: could not seed teams/drivers — {e}")


def insert_race_results():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT race_id, race_date, season_year FROM race")
        all_races = [{"race_id": r[0], "race_date": str(r[1]), "season_year": r[2]} for r in cur.fetchall()]
        cur.execute("SELECT race_id FROM race_result")
        existing_ids = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT driver_id, last_name FROM driver")
        last_name_to_id = {r[1].upper(): r[0] for r in cur.fetchall()}

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
                cur.execute("""
                    INSERT INTO race_result (race_id, p1_driver, p2_driver, p3_driver, safety_car_result)
                    VALUES (%s, %s, %s, %s, %s)
                """, (race["race_id"], p1_id, p2_id, p3_id, random.choice([True, False])))
                conn.commit()
                inserted += 1
            except Exception as e:
                print(f"[seed] race_id {race['race_id']}: unexpected error — {e}")
                continue

        cur.close(); conn.close()
        print(f"[seed] Race results: inserted {inserted} new result(s).")
    except Exception as e:
        print(f"[seed] Warning: could not seed race results — {e}")


insert_recent_races()
insert_teams_and_drivers()
insert_race_results()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
