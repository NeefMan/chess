import pygame
import sys

class Game:
    def __init__(self):
        self.settings = Settings()
        self.board = Board(self.settings.colors["wheat"], self.settings.colors["brown"])
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.pawn = Pawn("images/pieces/white_pawn.png", 100, 100)

    def run(self):
        while self.running:
            self.screen.fill(self.settings.colors["white"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            
            self.display_board()
            self.screen.blit(self.pawn.image, (400,400))

            pygame.display.flip()
            self.clock.tick(self.settings.fps)

    def display_board(self):
        for key, value in self.board.squares.items():
            x, y = key
            color = value["color"]
            pygame.draw.rect(
                self.screen, 
                color, 
                pygame.rect.Rect(x+self.board.board_x, y+self.board.board_y, self.board.square_width, self.board.square_height)
                )


class Board:
    def __init__(self, light, dark):
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
        
        self.initialize_board()

    def initialize_board(self):
        color1 = self.board_color_light
        color2 = self.board_color_dark
        for y in range(0, self.board_height, self.square_height):
            for x in range(0, self.board_width, self.square_width):
                self.squares[(x,y)] = {}
                self.squares[(x,y)]["color"] = color1
                if x < self.board_width - self.square_width:
                    color1, color2 = color2, color1



class Piece:
    def __init__(self, image, desired_image_width, desired_image_height):
        self.image = pygame.transform.scale(pygame.image.load(image).convert_alpha(), (desired_image_width, desired_image_height))


class Pawn(Piece):
    def __init__(self, image, desired_image_width, desired_image_height):
        super().__init__(image, desired_image_width, desired_image_height)


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