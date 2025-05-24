import os
import requests
from garminconnect import Garmin
from dotenv import load_dotenv
from dateutil import parser, tz
from fitparse import FitFile
from datetime import timezone
cet = tz.gettz("Europe/Amsterdam")
import fitdecode

load_dotenv()

GARMIN_USERNAME = os.getenv("GARMIN_USERNAME")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN") 

STRAVA_API_BASE = "https://www.strava.com/api/v3"

def authorize_strava_with_write_scope():
    import webbrowser
    from urllib.parse import urlparse, parse_qs

    client_id = os.getenv("STRAVA_CLIENT_ID")
    redirect_uri = "http://localhost"
    scope = "activity:write"

    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={client_id}&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&approval_prompt=force"
        f"&scope={scope}"
    )

    print("Opening browser for Strava OAuth...")
    webbrowser.open(auth_url)
    redirected_url = input("Paste the full redirected URL here:\n")
    
    # Extract code from redirected URL
    code = parse_qs(urlparse(redirected_url).query).get("code", [None])[0]
    if not code:
        raise Exception("Authorization code not found.")
    return code

def exchange_strava_code_for_tokens(code):
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code"
    })
    response.raise_for_status()
    tokens = response.json()

    # Optional: Save to .env
    with open(".env", "a") as f:
        f.write(f"\nSTRAVA_ACCESS_TOKEN={tokens['access_token']}")
        f.write(f"\nSTRAVA_REFRESH_TOKEN={tokens['refresh_token']}")
        f.write(f"\nSTRAVA_EXPIRES_AT={tokens['expires_at']}")
    
    return tokens

def refresh_strava_access_token():
    STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
    STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

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

    if tokens["refresh_token"] != STRAVA_REFRESH_TOKEN:
        with open(".env", "r") as f:
            lines = f.readlines()

        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("STRAVA_REFRESH_TOKEN="):
                    f.write(f"STRAVA_REFRESH_TOKEN={tokens['refresh_token']}\n")
                else:
                    f.write(line)

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

from datetime import timezone

def find_matching_garmin_activity(strava_activity, garmin_activities, time_tolerance=120, distance_tolerance=100):
    strava_time = parser.parse(strava_activity["start_date_local"]).replace(tzinfo=cet)
    strava_distance = strava_activity.get("distance", 0)


    for garmin_activity in garmin_activities:
        garmin_time = parser.parse(garmin_activity["startTimeLocal"]).replace(tzinfo=cet)
        garmin_distance = garmin_activity.get("distance", 0)

        time_diff = abs((strava_time - garmin_time).total_seconds())
        distance_diff = abs(strava_distance - garmin_distance)

        if time_diff <= time_tolerance and distance_diff <= distance_tolerance:
            return garmin_activity
    
    return None


def main():
    garmin_client = authenticate_garmin()
    strava_token, new_refresh_token, expires_at = refresh_strava_access_token()

    garmin_activities = garmin_client.get_activities(0, 20)
    strava_activities = get_strava_activities(strava_token)

    for strava_activity in strava_activities:
        if "suppen" in strava_activity["name"] and strava_activity["type"] == "StandUpPaddling":
            
            new_name = strava_activity["name"].replace("suppen", "Surfen")
            new_type = "Surfing"
            print(f"Updating activity {strava_activity['id']} to: {new_name}")
            update_strava_activity(strava_token, strava_activity["id"], {"name": new_name, "type": new_type})
            
            # print(f"Updating sport type {strava_activity["type"]} to: {new_type}")
            # update_strava_activity(strava_token, strava_activity["id"], {"type": new_type})

            # matching_garmin_activity = find_matching_garmin_activity(strava_activity, garmin_activities)
            # if matching_garmin_activity:
            #     print(f"Matched Garmin activity ID: {matching_garmin_activity['activityId']}")
            #     activity_id = matching_garmin_activity["activityId"]
                # fit_data = garmin_client.download_activity(activity_id, dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL)
                # with open(f"{activity_id}.fit", "wb") as f:
                #     f.write(fit_data)
                
                # fitfile = FitFile(f"{activity_id}.fit")

                # for record in fitfile.get_messages("record"):
                #     for field in record:
                #         print(f"{field.name}: {field.value}")

                # with fitdecode.FitReader(f'{activity_id}.fit') as fit:
                #     for frame in fit:
                #         if frame.frame_type == fitdecode.FIT_FRAME_DATA:
                #             print(frame.name)
                #             for field in frame.fields:
                #                 print(f" * {field.name}: {field.value}")
            # else:
            #     print("No matching Garmin activity found...")
        


if __name__ == "__main__":
    code = authorize_strava_with_write_scope()
    tokens = exchange_strava_code_for_tokens(code)
    main()
