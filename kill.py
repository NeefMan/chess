import socket
import json

HOST = "18.218.245.80"
PORT = 5000
END_DELIMETER = "*&^%"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    data = json.dumps({"username": "root", "task": "kill"}) + END_DELIMETER
    s.sendall(data.encode())