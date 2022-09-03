import pygame
pygame.font.init()


class Button():
    def __init__(self, pos, size, elevation, text='', font=pygame.font.Font(None, 15),
                 border_radius=0, img=None):
        self.border_radius = border_radius
        self.elevation = elevation
        self.dynamic_elevation = elevation
        self.orginal_y_pos = pos[1]
        self.pressed = False

        self.img = img

        self.toprect = pygame.Rect(pos + size)
        self.top_color = "#757473"
        
        self.bottomrect = pygame.Rect(pos, (size[0], elevation))
        self.bottom_color = "#5C5C5C"
        
        self.text_surf = font.render(text, 1, "white")
        self.text_rect = self.text_surf.get_rect(center=self.toprect.center)
        
        self.hover = "#8C8B8A"
        
        

    def render(self, screen):
        # elevation logic
        self.toprect.y = self.orginal_y_pos - self.dynamic_elevation
        self.text_rect.center = self.toprect.center
        
        self.bottomrect.midtop = self.toprect.midtop
        self.bottomrect.height = self.toprect.height + self.dynamic_elevation
        
        pygame.draw.rect(screen, self.bottom_color, self.bottomrect, border_radius=self.border_radius)
        pygame.draw.rect(screen, self.top_color, self.toprect, border_radius=self.border_radius)
        screen.blit(self.text_surf, self.text_rect)
        if self.img:
            screen.blit(self.img, self.img.get_rect(center = self.toprect.center))

    def check_click(self):
        mouse_pos = pygame.mouse.get_pos()
        right_click = pygame.mouse.get_pressed()[0]
        if self.toprect.collidepoint(mouse_pos):
            self.top_color = self.hover
            if right_click and not self.pressed:
                self.dynamic_elevation = 0
                self.pressed = True
                return True
            if not right_click:
                self.pressed = False
                self.dynamic_elevation = self.elevation
        else:
            self.top_color = "#757473"
            self.dynamic_elevation = self.elevation
            
        