import socket
import threading
from collections import defaultdict
import json
import time
import random

HOST = "0.0.0.0"
PORT = 5000
END_DELIMETER = "*&^%"
TIMEOUT_DUR = 15

user_data = {} # {"username": {"connection": connection, "move": None, "turn": "not_set", "addr": addr, "timestamp": timestamp}}
shutdown_event = threading.Event()  # Thread-safe shutdown flag

def send_data_to_host(conn, data):
    json_data = json.dumps(data)
    json_data += END_DELIMETER
    conn.sendall(json_data.encode())

def set_turns(user1, user2):
    #randomly pick the first user, then set their turn to True
    users = [user1, user2]
    first = random.choice(users)
    second = user2 if first == user1 else user1

    user_data[first]["turn"] = True
    user_data[second]["turn"] = False

def handle_task(data, conn):
    task = data["task"]
    username = data["username"]
    if task == "check_move":
        move = user_data.get(username, {}).get("move")
        send_data_to_host(conn, {"move": move})
        if move:
            user_data[username]["move"] = None
    elif task == "move":
        print(f"(Move request) {data}")
        move = data["move"]
        to_user = data["to_user"]
        user_data[to_user]["move"] = move
    elif task == "connect":
        to_user = data["to_user"]
        print(f"(Connect request) from user: {username} - to user: {to_user}")
        start_time = time.time()
        while to_user not in user_data:
            if time.time() - start_time > TIMEOUT_DUR:
                send_data_to_host(conn, {"error": f"Timeout error connecting to user: {to_user}"})
                return
            time.sleep(0.1)
        if user_data[username]["timestamp"] < user_data[to_user]["timestamp"]:
            set_turns(username, to_user)
        while user_data[username]["turn"] == "not_set":
            time.sleep(1)
        send_data_to_host(conn, {"success": f"Successfully connected to user: {to_user}", "turn": user_data[username]["turn"]})
    elif task == "kill":
        shutdown_event.set()
        print(f"(Kill Request) Server shutting down...")
    elif task == "reset":
        to_user = data["to_user"]
        print(f"(Reset Board Request) from: {username} to: {to_user}")
        send_data_to_host(user_data[to_user]["connection"],  {"reset": True})

def recieve_data(conn):
    full_packet = ""
    conn.settimeout(1.0)  # timeout every 1 second
    while True:
        try:
            packet = conn.recv(1024).decode()
            # <-- NEW: if peer closed, treat it like a "disconnect" task
            if packet == "":
                print("Packet blank because the user disconnected")
                return json.dumps({"task": "dc"})
            full_packet += packet
            if full_packet.endswith(END_DELIMETER):
                break
        except socket.timeout:
            if shutdown_event.is_set():
                return json.dumps({"task": "dc"})
            # else keep looping
    return full_packet[:-len(END_DELIMETER)]

"""def recieve_data(self, conn):
    full_packet = ""
    while True:
        packet = conn.recv(1024).decode()
        full_packet += packet
        if full_packet[len(full_packet)-len(self.END_DELIMETER):] == self.END_DELIMETER:
            data = full_packet.split(self.END_DELIMETER)
            data = [json.loads(value) for value in data if value != self.END_DELIMETER and value != '']
            break
    return data"""

def register_user(conn, username, timestamp, addr):
    user_data[username] = {}
    user_data[username]["connection"] = conn
    user_data[username]["move"] = None
    user_data[username]["turn"] = "not_set"
    user_data[username]["timestamp"] = timestamp
    user_data[username]["addr"] = addr

def handle_connection(conn, addr, timestamp):
    with conn:
        print(f"Connected with {addr}")
        data = json.loads(recieve_data(conn))
        username = data["username"]
        register_user(conn, username, timestamp, addr)
        while data["task"] != "dc":
            handle_task(data, conn)
            if shutdown_event.is_set():
                break
            data = json.loads(recieve_data(conn))
    user_data.pop(username, None)
    print(f"Disconnected from {addr}\n\n")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print("Server started.")
    while not shutdown_event.is_set():
        try:
            s.settimeout(1.0)  # Avoid blocking indefinitely on accept()
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr, time.time()), daemon=True)
            thread.start()
        except socket.timeout:
            continue
    print("Server has been shut down.")
