import requests

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
