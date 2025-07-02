import os
import zipfile
import requests
from io import BytesIO
from dotenv import load_dotenv
from dateutil import parser, tz
import datetime
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from fitparse import FitFile
cet = tz.gettz("Europe/Amsterdam")

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN") 
STRAVA_API_BASE = "https://www.strava.com/api/v3"
GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

def get_surfing_activities_garmin():
    try:
        client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        client.login()

        activities = client.get_activities(0, 5)

        surfing_activities = [a for a in activities if a["activityType"]["typeKey"].lower() == "stand_up_paddleboarding_v2"]

        return fitfiles(client, surfing_activities)
    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarminConnectAuthenticationError) as e:
        print(f"Error connecting to Garmin Connect: {e}")

def fitfiles(client, activities):
    fit_files = []
    for activity in activities:
        try:
            fit_file = client.download_activity(activity["activityId"], dl_fmt=client.ActivityDownloadFormat.ORIGINAL)
            fit_files.append(fit_file)
        except Exception as e:
            print(f"Error retrieving FIT file for activity {activity['activityId']}: {e}")

    return unzip(fit_files)

def unzip(fit_files):
    unzipped_files = []
    for ff in fit_files:
        with zipfile.ZipFile(BytesIO(ff)) as z:
            for name in z.namelist():
                if name.endswith(".fit"):
                    with z.open(name) as fit_file:
                        fit_data = fit_file.read()
                        fit_parsed = FitFile(BytesIO(fit_data))
                        unzipped_files.append(fit_parsed)
    return get_fields(unzipped_files)

def get_fields(fit_files):
    wanted_fields = ["time_created", "wavenum", "LRtxt1", "LRtxt2", "wavetime", "wavedistol", "wavetime2", "wavedist", "wavespd"]
    result = []

    for fit_file in fit_files:
        fields = {}
        for message in fit_file.get_messages():
            if(message.get_value("local_timestamp") is not None):
                fields["time_created"] = message.get_value("local_timestamp").astimezone(cet).isoformat()
                break
        for message in fit_file.get_messages():
            if (message.get_value("wavenum") is not None):
                fields["wavenum"] = message.get_value("wavenum")
                fields["numlefts"] = message.get_value("LRtxt1")
                fields["numrights"] = message.get_value("LRtxt2")
                fields["total_wave_time"] = message.get_value("wavetime")
                fields["total_wave_distance"] = message.get_value("wavedistol")
                fields["max_wave_time"] = message.get_value("wavetime2")
                fields["max_wave_distance"] = message.get_value("wavedist")
                fields["max_wave_speed"] = message.get_value("wavespd")
                break
        print(fields)
        result.append(fields)
    return result
                
    

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
    garmin_activities = get_surfing_activities_garmin()



    for strava_activity in strava_activities:
        if "suppen" in strava_activity["name"] and strava_activity["type"] == "StandUpPaddling":

            for garmin_activity in garmin_activities:
                print(garmin_activity["time_created"])
            #     if(strava_activity["start_date"] == garmin_activity["time_created"].astimezone(cet).isoformat()):
            #         print(f"Found matching Garmin activity for Strava activity {strava_activity['id']}: {garmin_activity}")
            
            # new_name = strava_activity["name"].replace("suppen", "Surfen")
            # new_type = "Surfing"
            # print(f"Updating activity {strava_activity['id']} to: {new_name}")
            # update_strava_activity(strava_token, strava_activity["id"], {"name": new_name, "type": new_type})


if __name__ == "__main__":
    main()
