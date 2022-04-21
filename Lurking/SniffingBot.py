import json
import ssl
import threading
import time

import requests
import websocket
import random

botName = "LurkBot"
file_name = "lurking.txt"


def run(roomCode):
    def load_learning_words():
        with open(file_name, "r") as f:
            for v in f:
                learningList.append(v.strip().lower())

    def generate_user_token():
        digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-"
        user_token_ = ""
        for i in range(16):
            user_token_ += random.choice(digits)
        return user_token_

    wordList = []
    learningList = []

    load_learning_words()

    def join_game():
        wsg.recv()  # Get initial packet
        wsg.send("40")  # initialize communication
        wsg.recv()
        wsg.send(f'42["joinGame","bombparty","{roomCode}","{user_token}"]')  # Join Game
        wsg.recv()
        previous_msg = ""
        while True:
            msg = wsg.recv()
            if msg == "2":  # Keep-alive packet
                wsg.send("3")
                continue

            if "42[\"correctWord\"," in msg:  # Add word to lurking list if it's correct and not already inside list.
                prev_word = previous_msg.split(",")[-1].strip("]").strip("\"")
                load_learning_words()  # Reload list for other instances of LurkBot
                if prev_word not in learningList:
                    print("Adding " + prev_word)
                    with open(file_name, 'a') as f:
                        f.write("\n" + prev_word)
                    learningList.append(prev_word)
            previous_msg = msg

    def join_chat():
        # Needed for game session
        wsc.recv()  # Get initial packet
        wsc.send("40")  # initialize communication
        wsc.recv()
        wsc.send('420["joinRoom",{"roomCode":"_rc","userToken":"_ut","nickname":"_nn","language":"en-US"}]'.replace(
            "_ut", user_token).replace("_nn", botName).replace("_rc", roomCode))  # Join room
        wsc.recv()
        while True:
            msg = wsc.recv()
            if msg == "2":  # Keep-alive packet
                wsc.send("3")

    wsg = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})  # Initialize game socket
    server = requests.post("https://jklm.fun/api/joinRoom", json={"roomCode": roomCode})
    server = server.json()['url'].replace(
        "https", "wss") + "/socket.io/?EIO=4&transport=websocket"  # Get websocket url
    wsg.connect(server)  # Connect game socket

    wsc = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})  # Initialize chat socket
    wsc.connect(server)  # Connect chat socket

    user_token = generate_user_token()  # Generate user token (16 random characters) to link chat/game socket
    threading.Thread(target=join_chat, daemon=True).start()  # Launch chat socket in another thread
    time.sleep(1)  # Sleep to make sure chat initializes
    join_game()  # Join Game socket
