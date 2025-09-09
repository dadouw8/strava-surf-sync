import time
import os
import zipfile
import requests
from io import BytesIO
from dotenv import load_dotenv
from dateutil import parser, tz
from datetime import datetime, timedelta
from dateutil import parser
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

def get_garmin_api():
    api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
    api.login()
    print(f"Succesfully logged into Garmin Connect, date:{datetime.today()}")

    return api

def get_surfing_activities_garmin(api):
    activities = api.get_activities(0, 5)

    surfing_activities = [a for a in activities if a["activityType"]["typeKey"].lower() == "stand_up_paddleboarding_v2"]

    return fitfiles(api, surfing_activities)

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
                local_time = message.get_value("local_timestamp")
                local_time = local_time.replace(tzinfo=cet)
                utc_time = local_time.astimezone(tz.UTC)
                fields["time_created"] = utc_time           
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


def get_strava_activities(access_token, per_page=10):
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
    garmin_api = get_garmin_api()
    exception_thrown = False

    while True:
        try:
            strava_token, new_refresh_token, expires_at = refresh_strava_access_token()
            strava_activities = get_strava_activities(strava_token)
            garmin_activities = get_surfing_activities_garmin(garmin_api)

            exception_thrown = False

            for strava_activity in strava_activities:
                if "suppen" in strava_activity["name"] and strava_activity["type"] == "StandUpPaddling":
                    for garmin_activity in garmin_activities:
                        tolerance = timedelta(seconds=20)
                        strava_date = parser.isoparse(strava_activity["start_date"])
                        strava_time = strava_date.astimezone(tz.UTC)
                        garmin_time = garmin_activity["time_created"].astimezone(tz.UTC)
                        if abs(garmin_time - strava_time) <= tolerance:
                            print(f"Found matching Garmin activity for Strava activity {strava_activity['id']}: {garmin_activity}")
                            description = (
                                f"Number Of Total Waves: {garmin_activity['wavenum']}\n"
                                f"Number Of Lefts: {garmin_activity['numlefts']}\n"
                                f"Number Of Rights: {garmin_activity['numrights']}\n"
                                f"Total Wave Time: {garmin_activity['total_wave_time']} minutes.sec\n"
                                f"Total Wave Distance: {garmin_activity['total_wave_distance']} meters\n"
                                f"Max Wave Time: {garmin_activity['max_wave_time']} seconds\n"
                                f"Max Wave Distance: {garmin_activity['max_wave_distance']} meters\n"
                                f"Max Speed: {garmin_activity['max_wave_speed']} km/h"
                            )
                            new_name = strava_activity["name"].replace("suppen", "Surfen")
                            new_type = "Surfing"
                            print(f"Updating activity {strava_activity['id']} to: {new_name}")
                            update_strava_activity(strava_token, strava_activity["id"], {
                                "name": new_name,
                                "type": new_type,
                                "description": description
                            })
                            break

                        time.sleep(300)
        except Exception as e:
            if (exception_thrown == True):
                return
            else:
                exception_thrown = True
            print(f"Exception caught: {e}, re-logging into Garmin...")
            garmin_api = get_garmin_api()
            time.sleep(10)
            


if __name__ == "__main__":
    main()
