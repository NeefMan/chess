import socket
import json
import time
import sys
# "18.218.245.80"
class Client:
    def __init__(self, main):
        self.main = main
        self.HOST = "18.218.245.80"
        self.PORT = 5000
        self.END_DELIMETER = "*&^%"
        self.running = True
        self.timeout_dur = 20


    def recieve_data(self, conn):
        full_packet = ""
        while True:
            packet = conn.recv(1024).decode()
            full_packet += packet
            if full_packet.endswith(self.END_DELIMETER):
                data = full_packet.split(self.END_DELIMETER)
                data = [json.loads(value) for value in data if value != self.END_DELIMETER and value != '']
                break
        return data

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
            for data in result:
                if "error" in data:
                    raise Exception
                elif "success" in data:
                    print(data["success"])
                else:
                    raise Exception
                return data
        except Exception as e:
            print(e)
            print("There was an error in connecting to the user")
            self.send_data_to_host(self.conn, {"task": "dc"})
            sys.exit(1)

    def disconnect(self):
        self.send_data_to_host(self.conn, {"task": "dc"})
        self.conn.close()
        print("Connection closed")
    
    def run_client(self):
        while self.running:
            self.conn.settimeout(None)
            send_data = {"username": self.username, "task": "check_move"}
            self.send_data_to_host(self.conn, send_data)
            recieved_data = self.recieve_data(self.conn)
            for data in recieved_data:
                move = data.get("move")
                if move:
                    selected_square, to_square = move
                    selected_square = tuple(selected_square)
                    to_square = tuple(to_square)
                    self.main.board.selected = selected_square
                    self.main.board.move(to_square)
                reset = data.get("reset")
                if reset:
                    self.main.board = self.main.create_board_instance()
                time.sleep(1)