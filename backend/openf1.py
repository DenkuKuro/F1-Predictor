import requests
from datetime import datetime, timezone

BASE_URL = "https://api.openf1.org/v1"


def get_latest_session():
    response = requests.get(f"{BASE_URL}/sessions", params={"session_type": "Race"})
    response.raise_for_status()
    sessions = response.json()
    if not sessions:
        return None
    return sessions[-1] # Last one is the latest one


def get_driver_positions(session_key):
    # Returns the latest race position for each driver in the given session.
    response = requests.get(f"{BASE_URL}/position", params={"session_key": session_key})
    response.raise_for_status()
    entries = response.json()

    # Keep only the latest position entry per driver
    latest = {}
    for entry in entries:
        num = entry["driver_number"]
        if num not in latest or entry["date"] > latest[num]["date"]:
            latest[num] = entry

    return list(latest.values())


def get_safety_car_status(session_key):
    # Returns True if a safety car was deployed
    response = requests.get(
        f"{BASE_URL}/race_control",
        params={"session_key": session_key, "category": "SafetyCar"},
    )
    response.raise_for_status()
    events = response.json()
    return len(events) > 0


def get_session_drivers(session_key):
    # Returns driver info for all drivers in the given session.
    response = requests.get(f"{BASE_URL}/drivers", params={"session_key": session_key})
    response.raise_for_status()
    return response.json()


def get_race_finished(session):
    # Returns True if the race session has ended.
    session_key = session["session_key"]

    response = requests.get(
        f"{BASE_URL}/race_control",
        params={"session_key": session_key, "flag": "CHEQUERED"},
    )
    response.raise_for_status()
    if response.json():
        return True

    return False
