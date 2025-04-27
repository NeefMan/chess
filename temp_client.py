import socket
import json

HOST = "18.218.245.80"
PORT = 5000
END_DELIMETER = "*&^%"

def recieve_data(conn):
    full_packet = ""
    while True:
        packet = conn.recv(1024).decode()
        full_packet += packet
        if full_packet[len(full_packet)-len(END_DELIMETER):] == END_DELIMETER:
            break
    return full_packet[:len(full_packet)-len(END_DELIMETER)]

def send_data_to_host(conn, data):
    json_data = json.dumps(data)
    json_data += END_DELIMETER
    conn.sendall(json_data.encode())

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    username = input("What is your username? ")
    running = True
    while running:
        data = {}
        task = input("Would you like to view your inbox (vi), or send a message (sm), or disconnect (dc): ")
        data["task"] = task
        data["username"] = username
        if task == "vi":
            send_data_to_host(s, data)
            inbox = json.loads(recieve_data(s))
            print(inbox)
            continue
        elif task == "sm":
            to_user = input("Who do you want to send a message to? ")
            message = input("What is the message? ")
            data["to_user"] = to_user
            data["message"] = message
        elif task == "dc":
            running = False
        else:
            print("task invalid")
            continue

        send_data_to_host(s, data)