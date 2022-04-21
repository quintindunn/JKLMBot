import threading
import time

import requests
from SniffingBot import run as r

request = requests.get("https://jklm.fun/api/rooms").json()  # Get all rooms
valid_rooms = []
for room in request['publicRooms']:
    if room['gameId'] == 'bombparty' and 'details' in room and room['details'] == "English":
        valid_rooms.append(room)  # add room to list of rooms if room is playing `bombparty` and is in English

for room in valid_rooms:
    print(room["roomCode"])
    threading.Thread(target=r, args=[room["roomCode"]], daemon=True).start()  # run lurkbot in another thread
    time.sleep(10)  # sleep to bypass Error: 429

while True:
    pass  # loop to keep threads alive
