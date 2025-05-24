import os
import requests
from dotenv import load_dotenv
from dateutil import parser, tz
from fitparse import FitFile
from datetime import timezone
cet = tz.gettz("Europe/Amsterdam")
import fitdecode

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN") 

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

    return tokens["access_token"], tokens["refresh_token"], tokens["expires_at"]


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

def main():
    strava_token, new_refresh_token, expires_at = refresh_strava_access_token()
    strava_activities = get_strava_activities(strava_token)

    for strava_activity in strava_activities:
        if "suppen" in strava_activity["name"] and strava_activity["type"] == "StandUpPaddling":
            
            new_name = strava_activity["name"].replace("suppen", "Surfen")
            new_type = "Surfing"
            print(f"Updating activity {strava_activity['id']} to: {new_name}")
            update_strava_activity(strava_token, strava_activity["id"], {"name": new_name, "type": new_type})


if __name__ == "__main__":
    main()
