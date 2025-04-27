import socket
import json
import time

class Client:
    def __init__(self):
        self.HOST = "18.218.245.80"
        self.PORT = 5000
        self.END_DELIMETER = "*&^%"
        self.running = True


    def recieve_data(self, conn):
        full_packet = ""
        while True:
            packet = conn.recv(1024).decode()
            full_packet += packet
            if full_packet[len(full_packet)-len(self.END_DELIMETER):] == self.END_DELIMETER:
                break
        return full_packet[:len(full_packet)-len(self.END_DELIMETER)]

    def send_data_to_host(self, conn, data):
        json_data = json.dumps(data)
        json_data += self.END_DELIMETER
        conn.sendall(json_data.encode())
    
    def create_connection(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.conn = s
            s.connect((self.HOST, self.PORT))
            print("Connected")
            #username = input("What is your username? ")
            while self.running:
                time.sleep(1)
                """data = {}
                task = input("Would you like to view your inbox (vi), or send a message (sm), or disconnect (dc): ")
                data["task"] = task
                data["username"] = username
                if task == "vi":
                    self.send_data_to_host(s, data)
                    inbox = json.loads(self.recieve_data(s))
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

                self.send_data_to_host(s, data)"""
            self.send_data_to_host(self.conn, {"task": "dc"})
        print("Connection closed")