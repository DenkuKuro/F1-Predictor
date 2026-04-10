import requests
from datetime import date

BASE_URL = "https://api.jolpi.ca/ergast/f1"


def get_season_races(season_year):
    # Returns all races in a season with their round numbers and dates.
    response = requests.get(f"{BASE_URL}/{season_year}.json")
    response.raise_for_status()
    return response.json()["MRData"]["RaceTable"]["Races"]


def get_round_by_date(season_year, race_date):
    # Returns the Jolpica round number for a race matching the given date (YYYY-MM-DD).
    for race in get_season_races(season_year):
        if race["date"] == race_date:
            return int(race["round"])
    return None


def get_recent_races(n=10):
    # Returns up to n most recent completed races, most recent first.
    today = date.today().isoformat()
    current_year = date.today().year
    races = []

    for year in [current_year, current_year - 1]:
        try:
            season_races = get_season_races(year)
            past_races = [r for r in season_races if r["date"] <= today]
            for race in reversed(past_races):
                races.append({
                    "season": year,
                    "round": int(race["round"]),
                    "name": race["raceName"],
                    "location": race["Circuit"]["Location"]["locality"],
                    "country": race["Circuit"]["Location"]["country"],
                    "date": race["date"],
                })
                if len(races) >= n:
                    break
        except Exception:
            pass
        if len(races) >= n:
            break

    return races


def get_current_season_drivers():
    # Returns all drivers in the current season with their team name, from driver standings.
    current_year = date.today().year
    response = requests.get(f"{BASE_URL}/{current_year}/driverStandings.json")
    response.raise_for_status()
    lists = response.json()["MRData"]["StandingsTable"]["StandingsLists"]
    if not lists:
        return []
    entries = []
    for standing in lists[0]["DriverStandings"]:
        driver = standing["Driver"]
        team = standing["Constructors"][0]["name"] if standing["Constructors"] else None
        entries.append({
            "first_name": driver["givenName"],
            "last_name": driver["familyName"],
            "team_name": team,
        })
    return entries


def get_race_details(season_year, round_num):
    # Returns race metadata: name, circuit, location, session schedule. No results.
    response = requests.get(f"{BASE_URL}/{season_year}/{round_num}.json")
    response.raise_for_status()
    races = response.json()["MRData"]["RaceTable"]["Races"]
    if not races:
        return None
    race = races[0]
    sessions = {}
    for key in ["FirstPractice", "SecondPractice", "ThirdPractice", "SprintQualifying", "Sprint", "Qualifying"]:
        if key in race:
            sessions[key] = {"date": race[key]["date"], "time": race[key].get("time")}
    return {
        "season": int(race["season"]),
        "round": int(race["round"]),
        "name": race["raceName"],
        "circuit": race["Circuit"]["circuitName"],
        "locality": race["Circuit"]["Location"]["locality"],
        "country": race["Circuit"]["Location"]["country"],
        "date": race["date"],
        "time": race.get("time"),
        "sessions": sessions,
    }


def get_race_entry_list(season_year, round_num):
    # Returns drivers and constructors for a race sorted by car number. No positions or points.
    response = requests.get(f"{BASE_URL}/{season_year}/{round_num}/results.json")
    response.raise_for_status()
    races = response.json()["MRData"]["RaceTable"]["Races"]
    if not races:
        return []
    entries = []
    for result in races[0]["Results"]:
        entries.append({
            "car_number": int(result["Driver"]["permanentNumber"]),
            "code": result["Driver"]["code"],
            "first_name": result["Driver"]["givenName"],
            "last_name": result["Driver"]["familyName"],
            "nationality": result["Driver"]["nationality"],
            "team": result["Constructor"]["name"],
            "team_nationality": result["Constructor"]["nationality"],
        })
    entries.sort(key=lambda e: e["car_number"])
    return entries


def get_race_results(season_year, round_num):
    # Returns the top 3 finishing drivers for a given season/round.
    response = requests.get(f"{BASE_URL}/{season_year}/{round_num}/results.json")
    response.raise_for_status()
    races = response.json()["MRData"]["RaceTable"]["Races"]
    if not races:
        return []

    results = races[0]["Results"]
    podium = []
    for result in results:
        pos = int(result["position"])
        if pos > 3:
            break
        podium.append({
            "position": pos,
            "last_name": result["Driver"]["familyName"].upper(),
            "first_name": result["Driver"]["givenName"],
        })
    return podium
