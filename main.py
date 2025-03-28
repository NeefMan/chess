import pygame
import sys
import classic_piece_map

class Game:
    def __init__(self):
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
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_square = self.board.get_square_clicked(event.pos)
                    if self.board.selected and clicked_square:
                        self.board.move(clicked_square)
                        break
                    else:
                        self.board.set_selected_square(clicked_square)
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_f:
                        self.board.flipped = False if self.board.flipped else True
                    elif event.key == pygame.K_r:
                        self.board = self.create_board_instance()
                    elif event.key == pygame.K_q:
                        sys.exit()

            
            self.board.display_board(self.screen)

            pygame.display.flip()
            self.clock.tick(self.settings.fps)

    def create_board_instance(self):
        return Board(self, self.settings.colors["wheat"], self.settings.colors["brown"])
  

class Board:
    def __init__(self, main, light, dark):
        self.main = main

        # Board
        self.board_x = 0
        self.board_y = 0
        self.board_width = 800
        self.board_height = 800
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
        image_prefix = "images/test_pieces/"
        for key, value in imported_piece_map.piece_map.items():
            x, y = key
            x *= self.square_width
            y *= self.square_height

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
            
            piece_class, file_name = piece_name_abbreviation_map[value]
            self.squares[(x,y)]["piece"] = piece_class(value, f"images/pieces/{file_name}", self.square_width, self.square_height)
            self.squares[(x,y)]["piece"].x = x
            self.squares[(x,y)]["piece"].y = y
            

    def display_board(self, screen):
        for key, value in self.squares.items():
            x, y = key
            if self.flipped:
                x, y = self.flip_cords(x, y)
                x -= self.square_width
                y -= self.square_height
            color = value["color"]
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
    
    def set_selected_square(self, square):
        if square:
            self.selected = self.squares[square]["piece"]
            return
        self.selected = None

    def move(self, to_square):
        if to_square == (self.selected.x, self.selected.y):
            self.selected = None
            return False
        x, y = to_square
        self.squares[(self.selected.x, self.selected.y)]["piece"] = None
        self.selected.x = x
        self.selected.y = y
        self.squares[to_square]["piece"] = self.selected
        self.selected = None
        return True



class Piece:
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        self.image = pygame.transform.scale(pygame.image.load(image).convert_alpha(), (desired_image_width, desired_image_height))
        self.color = piece
        self.x = None
        self.y = None
        self.recursive_move = False

class Pawn(Piece):
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        super().__init__(piece, image, desired_image_width, desired_image_height)
        self.move_set = [ # non_capture, capture (only)
            (0,2,True),
            (0,1,True),
            (-1,1,False,True),
            (1,1,False,True)
        ]

class Bishop(Piece):
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        super().__init__(piece, image, desired_image_width, desired_image_height)
        self.recursive_move = True
        self.move_set = [
            (-1,-1),
            (-1,1),
            (1,1),
            (1,-1)
        ]

class Knight(Piece):
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        super().__init__(piece, image, desired_image_width, desired_image_height)
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
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        super().__init__(piece, image, desired_image_width, desired_image_height)
        self.recursive_move = True
        self.move_set = [
            (-1,0),
            (1,0),
            (0,1),
            (0,-1)
        ]

class Queen(Piece):
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        super().__init__(piece, image, desired_image_width, desired_image_height)
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
    def __init__(self, piece, image, desired_image_width, desired_image_height):
        super().__init__(piece, image, desired_image_width, desired_image_height)
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
        self.screen_width = 800
        self.screen_height = 800
        self.colors = {
            "brown": (184,139,74),
            "wheat": (227,193,111),
            "white": (255,255,255),
        }
        self.fps = 30


if __name__ == "__main__":
    main = Game()
    main.run()