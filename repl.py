import pygame
from game_engine import WizardGame

def main():
    pygame.init()
    game = WizardGame()
    game.run()

if __name__ == "__main__":
    main()