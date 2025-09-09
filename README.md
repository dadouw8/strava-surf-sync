# strava-surf-sync
I use this to change the sup activity from sup to surfing and then add some extra data from the garmin connect app about the surfing I did. I also make all activities that are not surfing public via this.


I am currently running into an issue. 
The github actions IP is not authorized to login into garmin connect. So, if I want to do things with garmin connect, I will have to make some changes. There are a few possible solutions.
I could use a VPN to make sure I have a trusted IP, but this can get kinda complex I think.
So, I think I am going to use a raspberry pi to run this script every 30 minutes. This will be a lot easier to implement.

I have run into an issue. Every week or so Garmin sends me an email that I have to reset my password for Garmin Connect and this is because I am logging into Garmin Connect every 30 minutes on the raspberry pi.
So I think I am going to solve this by having the script run constantly on the raspberry pi so that the tokens from the login won't be lost.
And then I will have the script wait for 30 minutes by doing time.sleep(1800).
I can even make these 30 minutes shorter now, which I will do. I am going to make it wait 5 minutes instead of 30.
The raspberry pi can easily handle this, but I don't want it to overheat.