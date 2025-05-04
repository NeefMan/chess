import socket
import threading
from collections import defaultdict
import json
import time

HOST = "0.0.0.0"
PORT = 5000
END_DELIMETER = "*&^%"
TIMEOUT_DUR = 15

moves = defaultdict(list)  # {"username": [(move, from_user, time_stamp)]}
users = {} # {"username": connection}
shutdown_event = threading.Event()  # Thread-safe shutdown flag

def send_data_to_host(conn, data):
    json_data = json.dumps(data)
    json_data += END_DELIMETER
    conn.sendall(json_data.encode())

def handle_task(data, conn):
    task = data["task"]
    username = data["username"]
    if task == "check_move":
        move = moves.get(username)
        send_data_to_host(conn, {"move": move})
        if move:
            moves[username] = None
    elif task == "move":
        print(f"(Move request) {data}")
        move = data["move"]
        to_user = data["to_user"]
        moves[to_user] = move
    elif task == "connect":
        to_user = data["to_user"]
        print(f"(Connect request) from user: {username} - to user: {to_user}")
        start_time = time.time()
        while to_user not in users:
            if time.time() - start_time > TIMEOUT_DUR:
                send_data_to_host(conn, {"error": f"Timeout error connecting to user: {to_user}"})
                return
            time.sleep(0.1)
        send_data_to_host(conn, {"success": f"Successfully connected to user: {to_user}"})
    elif task == "kill":
        shutdown_event.set()
        print(f"(Kill Request) Server shutting down...")

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

def handle_connection(conn, addr):
    with conn:
        print(f"Connected with {addr}")
        data = json.loads(recieve_data(conn))
        # register the user and move inbox
        username = data["username"]
        users[username] = conn
        moves["username"] = None
        while data["task"] != "dc":
            handle_task(data, conn)
            if shutdown_event.is_set():
                break
            data = json.loads(recieve_data(conn))
    users.pop(username, None)
    moves.pop(username, None)
    print(f"Disconnected from {addr}\n\n")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print("Server started.")
    while not shutdown_event.is_set():
        try:
            s.settimeout(1.0)  # Avoid blocking indefinitely on accept()
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr), daemon=True)
            thread.start()
        except socket.timeout:
            continue
    print("Server has been shut down.")
