import os
import requests
from garminconnect import Garmin
from dotenv import load_dotenv
from dateutil import parser
from fitparse import FitFile

load_dotenv()

GARMIN_USERNAME = os.getenv("GARMIN_USERNAME")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN") 

STRAVA_API_BASE = "https://www.strava.com/api/v3"

def refresh_strava_access_token():
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    tokens = response.json()
    access_token = tokens["access_token"]

    return access_token

def get_strava_activities(access_token, per_page=30):
    url = f"{STRAVA_API_BASE}/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": per_page}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def update_strava_activity(access_token, activity_id, data):
    url = f"{STRAVA_API_BASE}/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def authenticate_garmin():
    client = Garmin(GARMIN_USERNAME, GARMIN_PASSWORD)
    client.login()
    return client

def update_strava_activity(access_token, activity_id, data):
    url = f"{STRAVA_API_BASE}/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def find_matching_garmin_activity(strava_activity, garmin_activities, time_tolerance=120, distance_tolerance=100):
    strava_time = parser.parse(strava_activity["start_date_local"])
    strava_distance = strava_activity.get("distance", 0)

    for garmin_activity in garmin_activities:
        garmin_time = parser.parse(garmin_activity["startTimeLocal"])
        garmin_distance = garmin_activity.get("distance", 0)

        time_diff = abs((strava_time - garmin_time).total_seconds())
        distance_diff = abs(strava_distance - garmin_distance)

        if time_diff <= time_tolerance and distance_diff <= distance_tolerance:
            return garmin_activity
    
    return None


def main():
    garmin_client = authenticate_garmin()
    strava_token = refresh_strava_access_token()

    garmin_activities = garmin_client.get_activities(0, 20)
    strava_activities = get_strava_activities(strava_token)

    for strava_activity in strava_activities:
        if "suppen" in strava_activity["name"] and strava_activity["type"] == "Stand Up Paddling":
            new_name = strava_activity["name"].replace("suppen", "Surfen")
            print(f"Updating activity {strava_activity['id']} to: {new_name}")
            update_strava_activity(strava_token, strava_activity["id"], {"name": new_name})

            new_type = "Surfing"
            print(f"Updating sport type {strava_activity["type"]} to: {new_type}")
            update_strava_activity(strava_token, strava_activity["id"], {"type": new_type})

            matching_garmin_activity = find_matching_garmin_activity(strava_activity, garmin_activities)
            if matching_garmin_activity:
                print(f"Matched Garmin activity ID: {matching_garmin_activity['activityId']}")
            else:
                print("No matching Garmin activity found...")
        
            


if __name__ == "__main__":
    main()
