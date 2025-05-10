import pygame
import sys
import classic_piece_map
from client import Client
import threading
import time

class Game:
    def __init__(self):
        self.client = Client(self)
        self.client_result = self.client.initialize_client()
        thread = threading.Thread(target=self.client.run_client, daemon=True)
        thread.start()

        self.settings = Settings()

        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))

        self.board = self.create_board_instance()

        self.clock = pygame.time.Clock()

        self.running = True

    def run(self):
        while self.running:
            self.screen.fill(self.settings.colors["white"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.disconnect()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.board.turn:
                    clicked_square = self.board.get_square_clicked(event.pos)
                    if self.board.selected and clicked_square:
                        self.board.move(clicked_square, user_move=True)
                        break
                    elif clicked_square and self.board.squares[clicked_square]["piece"]:
                        self.board.selected = clicked_square
                        self.board.valid_moves = self.board.compute_valid_moves(self.board.squares[clicked_square]["piece"])
                    else:
                        self.board.selected = None
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_f:
                        self.board.flipped = not self.board.flipped
                    elif event.key == pygame.K_r:
                        self.client.send_data_to_host(self.client.conn, {"username": self.client.username, "task": "reset", "to_user": self.client.to_user})
                        self.board = self.create_board_instance()
                    elif event.key == pygame.K_q:
                        self.client.disconnect()
                        sys.exit()

            
            self.board.display_board(self.screen)

            pygame.display.flip()
            self.clock.tick(self.settings.fps)

    def create_board_instance(self):
        board = Board(self, self.settings.colors["wheat"], self.settings.colors["brown"], self.client, self.settings.colors["selected_yellow"])
        board.turn = self.client_result["turn"]
        board.flipped = not self.client_result["turn"]
        board.color = "w" if board.turn else "b"
        return board
        
  

class Board:
    def __init__(self, main, light, dark, client, highlighted_color):
        self.main = main
        self.client = client
        self.turn = None
        self.valid_moves = set()
        self.color = None

        # Board
        self.board_x = 0
        self.board_y = 0
        self.board_width = 700
        self.board_height = 700
        self.board_rows = 8
        self.board_collums = 8
        self.board_color_light = light
        self.board_color_dark = dark

        # Square
        self.square_width = self.board_width // self.board_collums
        self.square_height = self.board_height // self.board_rows
        self.squares = {} # (x, y) : {color, piece[None]}
        self.selected = None
        self.flipped = False # Whether board is displayed from black or whites pov
        self.square_color_highlighted = highlighted_color
        
        self.initialize_board()
        self.initalize_pieces(classic_piece_map)

    def initialize_board(self):
        color1 = self.board_color_light
        color2 = self.board_color_dark
        for y in range(0, self.square_height*self.board_rows, self.square_height):
            for x in range(0, self.square_width*self.board_collums, self.square_width):
                self.squares[(x,y)] = {}
                self.squares[(x,y)]["color"] = color1
                self.squares[(x,y)]["piece"] = None
                if x < (self.square_width * self.board_collums) - self.square_width:
                    color1, color2 = color2, color1
    
    def initalize_pieces(self, imported_piece_map):
        piece_name_abbreviation_map = {
            "wp": (Pawn, "white_pawn.png"),
            "bp": (Pawn, "black_pawn.png"),
            "wb": (Bishop, "white_bishop.png"),
            "bb": (Bishop, "black_bishop.png"),
            "wk": (Knight, "white_knight.png"),
            "bk": (Knight, "black_knight.png"),
            "wr": (Rook, "white_rook.png"),
            "br": (Rook, "black_rook.png"),
            "wq": (Queen, "white_queen.png"),
            "bq": (Queen, "black_queen.png"),
            "wki": (King, "white_king.png"),
            "bki": (King, "black_king.png")
            }
        
        for key, value in imported_piece_map.piece_map.items():
            x, y = key
            x *= self.square_width
            y *= self.square_height
            
            piece_class, file_name = piece_name_abbreviation_map[value]
            self.squares[(x,y)]["piece"] = piece_class(value, f"images/pieces/{file_name}", self.square_width, self.square_height, x, y)
            

    def display_board(self, screen):
        for key, value in self.squares.items():
            x, y = key
            color = self.square_color_highlighted if self.selected == (x,y) else value["color"]
            if self.flipped:
                x, y = self.flip_cords(x, y)
                x -= self.square_width
                y -= self.square_height
            pygame.draw.rect(
                screen, 
                color, 
                pygame.rect.Rect(x+self.board_x, y+self.board_y, self.square_width, self.square_height)
                )
            
            piece = value["piece"]
            if piece:
                screen.blit(piece.image, (x+self.board_x,y+self.board_y))

    def get_square_clicked(self, pos):
        x, y = pos
        square_size = self.board_width / self.board_collums
        x -= self.board_x
        y -= self.board_y
        if self.flipped:
            x, y = self.flip_cords(x, y)
        
        x = int(x / square_size) * self.square_width
        y = int(y / square_size) * self.square_height
        if x < 0 or x > self.board_width-self.square_width or y < 0 or y > self.board_height-self.square_height:
            return None
        return (x,y)
    
    def flip_cords(self, x, y):
        return (self.board_width-x, self.board_height-y)

    def move(self, to_square, user_move=False):
        x, y = to_square

        if to_square == self.selected:
            self.selected = None
            self.valid_moves = set()
            return False

        selected_piece = self.squares[self.selected]["piece"]

        if selected_piece.piece_name[-1] == "p" and selected_piece.first_move:
            selected_piece.first_move = False
            selected_piece.move_set.remove((0,2,True))
        else:
            self.compute_valid_moves(selected_piece)
        
        if to_square not in self.valid_moves and user_move: return False

        if user_move:
            # send a move request to the server
            data = {"username": self.client.username, "task": "move", "to_user": self.client.to_user, "move": (self.selected, to_square)}
            thread = threading.Thread(target=self.client.send_data_to_host, args=(self.client.conn, data), daemon=True)
            thread.start()

        self.squares[self.selected]["piece"] = None # remove the selected piece from the squares map

        # set the pieces new cords to the to_square cords
        selected_piece.x, selected_piece.y = x, y
        # add the piece to the square map at the to_square cords
        self.squares[to_square]["piece"] = selected_piece
        self.selected = None
        self.turn = not self.turn
        return True
    
    def get_piece_at_coord(self, coord):
        return self.squares[coord]["piece"]
    
    def get_piece_color(self, piece):
        return piece.piece_name[0]
    
    def compute_valid_moves(self, from_piece):
        valid_moves = set()
        from_piece_color = self.get_piece_color(from_piece)
        if from_piece_color != self.color:
            return valid_moves
        for move in from_piece.move_set:
            x, y = from_piece.x, from_piece.y
            x_i, y_i, non_capture, capture_only = (*move, False, False, False, False)[:4]
            # Swap increment direction if color white move because different side of board has a different direction for forward
            x_i = -x_i if from_piece_color == "w" else x_i
            y_i = -y_i if from_piece_color == "w" else y_i
            x_i *= self.square_width
            y_i *= self.square_height
            while True:
                x += x_i
                y += y_i

                # break if x or y exceeds the boarder
                if (x > self.square_width*(self.board_collums-1)+self.board_x or x < 0+self.board_x 
                    or y > self.square_height*(self.board_rows-1)+self.board_y or y < 0+self.board_y): 
                    break
                # break if piece at x, y is a piece of the same color
                to_piece = self.get_piece_at_coord((x, y))
                if to_piece and self.get_piece_color(from_piece) == self.get_piece_color(to_piece): 
                    break
                # add move to valid_moves then break if piece at x, y is of a different color and the move is not non_capture only
                if to_piece and self.get_piece_color(from_piece) != self.get_piece_color(to_piece) and not non_capture:
                    valid_moves.add((x, y))
                    break
                # add move to valid_moves if space is open (maybe base case) and move is not capture_only
                if not to_piece and not capture_only:
                    valid_moves.add((x, y))

                if not from_piece.recursive_move:
                    break
        return valid_moves


class Piece:
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        self.image = pygame.transform.scale(pygame.image.load(image).convert_alpha(), (desired_image_width, desired_image_height))
        self.piece_name = piece_name
        self.x = x
        self.y = y
        self.recursive_move = False
        self.move_set = []
            
class Pawn(Piece):
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        super().__init__(piece_name, image, desired_image_width, desired_image_height, x, y)
        self.move_set = [ # non_capture, capture_only
            (0,2,True),
            (0,1,True),
            (-1,1,False,True),
            (1,1,False,True)
        ]
        self.first_move = True

class Bishop(Piece):
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        super().__init__(piece_name, image, desired_image_width, desired_image_height, x, y)
        self.recursive_move = True
        self.move_set = [
            (-1,-1),
            (-1,1),
            (1,1),
            (1,-1)
        ]

class Knight(Piece):
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        super().__init__(piece_name, image, desired_image_width, desired_image_height, x, y)
        self.move_set = [
            (-1,2),
            (-1,-2),
            (-2,1),
            (-2,-1),
            (1,2),
            (1,-2),
            (2,1),
            (2,-1)
        ]

class Rook(Piece):
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        super().__init__(piece_name, image, desired_image_width, desired_image_height, x, y)
        self.recursive_move = True
        self.move_set = [
            (-1,0),
            (1,0),
            (0,1),
            (0,-1)
        ]

class Queen(Piece):
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        super().__init__(piece_name, image, desired_image_width, desired_image_height, x, y)
        self.recursive_move = True
        self.move_set = [
            (-1,0),
            (1,0),
            (0,1),
            (0,-1),
            (-1,-1),
            (-1,1),
            (1,1),
            (1,-1)

        ]

class King(Piece):
    def __init__(self, piece_name, image, desired_image_width, desired_image_height, x, y):
        super().__init__(piece_name, image, desired_image_width, desired_image_height, x, y)
        self.move_set = [
            (-1,0),
            (1,0),
            (0,1),
            (0,-1),
            (-1,-1),
            (-1,1),
            (1,1),
            (1,-1)
        ]


import socket
import json


class Settings:
    def __init__(self):
        self.screen_width = 700
        self.screen_height = 700
        self.colors = {
            "brown": (184,139,74),
            "wheat": (227,193,111),
            "white": (255,255,255),
            "selected_yellow": (219,219,83),
        }
        self.fps = 30


if __name__ == "__main__":
    main = Game()
    main.run()