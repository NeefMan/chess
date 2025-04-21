import socket
import threading
from collections import defaultdict
import json

HOST = "18.218.245.80"
PORT = 5000
END_DELIMETER = "*&^%"

inbox = defaultdict(list)  # {"username": [(message, from_user)]}
shutdown_event = threading.Event()  # Thread-safe shutdown flag

def handle_data(data, conn):
    task = data["task"]
    username = data["username"]
    if task == "sm":
        to_user = data["to_user"]
        message = data["message"]
        inbox[to_user].append((message, username))
        print(f"(Message Request) From: {username} - To: {to_user} - Message: {message}")
    elif task == "vi":
        user_inbox = inbox.get(username)
        conn.sendall((json.dumps(user_inbox) + END_DELIMETER).encode())
        print(f"(View inbox request) For user: {username} - Inbox: {user_inbox}")
    elif task == "kill":
        shutdown_event.set()
        print(f"(Kill Request) Server shutting down...")

def recieve_data(conn):
    full_packet = ""
    conn.settimeout(1.0)  # timeout every 1 second
    while True:
        try:
            packet = conn.recv(1024).decode()
            full_packet += packet
            if full_packet.endswith(END_DELIMETER):
                break
        except socket.timeout:
            if shutdown_event.is_set():
                print("shutdown event is set")
                return json.dumps({"task": "dc"})
    return full_packet[:-len(END_DELIMETER)]


def handle_connection(conn, addr):
    with conn:
        print(f"Connected with {addr}")
        data = json.loads(recieve_data(conn))
        while data["task"] != "dc":
            handle_data(data, conn)
            if shutdown_event.is_set():
                break
            data = json.loads(recieve_data(conn))
    print(f"Disconnected from {addr}\n\n")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print("Server started.")
    while not shutdown_event.is_set():
        try:
            s.settimeout(1.0)  # Avoid blocking indefinitely on accept()
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr))
            thread.start()
        except socket.timeout:
            continue
    print("Server has been shut down.")
