import json
import ssl
import threading
import time

import requests
import websocket
import logging
import random

roomCode = "AXNX"
botName = "plsnokickIlearning"
slow = True
character_delay = 0.02


wordList = []
learningList = []



def load_words():
    with open("words.txt", "r") as f:
        for v in f:
            wordList.append(v.strip().lower())


def load_learning_words():
    with open("learning.txt", "r") as f:
        for v in f:
            learningList.append(v.strip().lower())


load_words()
load_learning_words()

def generate_user_token():
    digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-"
    user_token = ""
    for i in range(16):
        user_token += random.choice(digits)
    return user_token


def parse_response(response):
    return json.loads("{" + response.split("{", 1)[1])


def generate_word(key):
    try:
        done = False
        while not done:
            copy = wordList.copy()
            acceptable = []
            for word in copy:
                if key == word:
                    wordList.remove(word)
                elif key in word:
                    acceptable.append(word)
            sortedList = sorted(acceptable, key=len, reverse=True)
            done = True
            word = sortedList[len(sortedList) // 2]
            wordList.remove(word)
            if len(sortedList) > 1:
                return word
            else:
                print("No words")
    except IndexError:
        return


def join_game():
    wsg.recv()
    wsg.send("40")
    wsg.recv()
    wsg.send(f'42["joinGame","bombparty","{roomCode}","{user_token}"]')
    launch_data = wsg.recv()
    self_peer_id = launch_data.split('"selfPeerId":')[1].split(",")[0]
    word = ""
    previous_msg = ""
    print("Ready...")
    while True:
        wsg.send('42["joinRound"]')  # Join round
        msg = wsg.recv()
        if msg == "2":  # Keep-alive packet
            wsg.send("3")
            continue

        if "42[\"correctWord\"," in msg:  # Add word to learning file if not already in.
            prev_word = previous_msg.split(",")[-1].strip("]").strip("\"")
            if prev_word not in learningList:
                print("Adding " + prev_word)
                with open("learning.txt", 'a') as f:
                    f.write("\n" + prev_word)
                learningList.append(prev_word)
        previous_msg = msg  # Reset previous word for correctWord detection

        if msg.startswith("42"):  # If the packet starts with a gameData packet
            if ("nextTurn" in msg or "failWord" in msg) and self_peer_id + "," in msg or \
                    ("setMilestone" in msg and f"currentPlayerPeerId:{self_peer_id}" in msg):
                if "setMilestone" not in msg:  # Check if game started on bot
                    data = json.loads(msg.split("42")[1])
                    word = generate_word(data[2])
                else:
                    word = generate_word(msg.split('"syllable":"')[1].split("\"")[0])  # find syllable required
                    word = generate_word(word)

                if not word:  # If generate_word couldn't find a word to use
                    continue

                if slow:
                    current = ""
                    for i in word[:-1]:  # Type word letter by letter
                        current += i
                        wsg.send(f'42["setWord","{current}",false]')
                        wsg.recv()
                        time.sleep(character_delay)  # character delay
                    current += word[-1]
                    wsg.send(f'42["setWord","{current}",true]')  # Finalize word
                else:
                    wsg.send(f'42["setWord","{word}",true]')  # If not on slow mode just send the word in one packet
            elif ("setPlayerWord" not in msg) and ("nextTurn" not in msg) and ("correctWord" not in msg):
                print(msg)


def join_chat():
    wsc.recv()
    wsc.send("40")
    wsc.recv()
    wsc.send('420["joinRoom",{"roomCode":"_rc","userToken":"_ut","nickname":"_nn","language":"en-US"}]'.replace(
        "_ut", user_token).replace("_nn", botName).replace("_rc", roomCode))
    wsc.recv()
    prev = ""
    while True:
        msg = wsc.recv()
        if msg == "2":  # Keep-alive packet
            wsc.send("3")


wsg = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
server = requests.post("https://jklm.fun/api/joinRoom", json={"roomCode": roomCode})
server = server.json()['url'].replace(
    "https", "wss") + "/socket.io/?EIO=4&transport=websocket"
wsg.connect(server)

wsc = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
wsc.connect(server)

user_token = generate_user_token()
threading.Thread(target=join_chat, daemon=True).start()
print("Starting Chat Thread!")
time.sleep(1)
join_game()
