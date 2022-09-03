import pygame
pygame.init()
from config import *
from scene import *


def Render_Text(what, color, where, window):
    font = pygame.font.Font(None, 30)
    text = font.render(what, 1, pygame.Color(color))
    window.blit(text, where)

def main():
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Chess")
    main_clock = pygame.time.Clock()

    manager = SceneManager()
    manager.go_to(GameScene())
    
    while True:
        screen.fill('black')
        main_clock.tick(MAX_FPS)
        manager.scene.handle_events()
        manager.scene.update()
        manager.scene.render(screen)
        
        
        Render_Text(str(int(main_clock.get_fps())), (255, 255, 255), (0, 0), screen)
        pygame.display.update()
        

if __name__ == "__main__":
    main()