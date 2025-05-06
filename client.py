import socket
import json
import time
import sys
# "18.218.245.80"
class Client:
    def __init__(self, main):
        self.main = main
        self.HOST = "127.0.0.1"
        self.PORT = 5000
        self.END_DELIMETER = "*&^%"
        self.running = True
        self.timeout_dur = 20


    def recieve_data(self, conn):
        full_packet = ""
        while True:
            packet = conn.recv(1024).decode()
            full_packet += packet
            if full_packet[len(full_packet)-len(self.END_DELIMETER):] == self.END_DELIMETER:
                break
        return json.loads(full_packet[:len(full_packet)-len(self.END_DELIMETER)])

    def send_data_to_host(self, conn, data):
        json_data = json.dumps(data)
        json_data += self.END_DELIMETER
        conn.sendall(json_data.encode())

    def initialize_client(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(self.timeout_dur)
        try:
            self.username = input("What is your username? ")
            self.to_user = input("Who would you like to connect to? ")
            self.conn.connect((self.HOST, self.PORT))
            print("Connected to server")
            self.send_data_to_host(self.conn, {"username": self.username, "task": "connect", "to_user": self.to_user})
            result = self.recieve_data(self.conn)
            if "error" in result:
                raise Exception
            elif "success" in result:
                print(result["success"])
            else:
                raise Exception
            return result
        except Exception as e:
            print(e)
            print("There was an error in connecting to the user")
            sys.exit(1)

    def disconnect(self):
        self.send_data_to_host(self.conn, {"task": "dc"})
        self.conn.close()
        print("Connection closed")
    
    def run_client(self):

        while self.running:
            self.conn.settimeout(None)
            data = {"username": self.username, "task": "check_move"}
            self.send_data_to_host(self.conn, data)
            data = self.recieve_data(self.conn)
            move = data.get("move")
            if move:
                selected_square, to_square = move
                selected_square = tuple(selected_square)
                to_square = tuple(to_square)
                self.main.board.selected = selected_square
                self.main.board.move(to_square)
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