# strava-surf-sync
I use this to change the sup activity from sup to surfing and then add some extra data from the garmin connect app about the surfing I did. I also make all activities that are not surfing public via this.


I am currently running into an issue. 
The github actions IP is not authorized to login into garmin connect. So, if I want to do things with garmin connect, I will have to make some changes. There are a few possible solutions.
I could use a VPN to make sure I have a trusted IP, but this can get kinda complex I think.
So, I think I am going to use a raspberry pi to run this script every 15 minutes. This will be a lot easier to implement.