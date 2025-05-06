import socket
import json

HOST = "127.0.0.1"
PORT = 5000
END_DELIMETER = "*&^%"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    data = json.dumps({"username": "root", "task": "kill"}) + END_DELIMETER
    s.sendall(data.encode())