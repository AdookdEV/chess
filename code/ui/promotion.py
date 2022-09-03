from 

class PromotionMenu:
    def __init__(self, x, y, iswhite, board):
        self.x = x
        self.y = y if y + SQUARE_SIZE*4 <= board.y + SQUARE_SIZE*8 else y - abs(y + SQUARE_SIZE*4 - (board.y + SQUARE_SIZE*8))
        self.pieces_symbols = ['Q', 'N', 'R', 'B']
        self.iswhite = iswhite
        self.rect = pygame.Rect(self.x, self.y, SQUARE_SIZE, 4*SQUARE_SIZE)
        self.promotion_type = None
        if not iswhite:
            self.pieces_symbols = list(map(lambda x: x.lower(), self.pieces_symbols[::-1]))
    
    def result(self):
        return self.promotion_type

    def handle_events(self, event):
        mx, my = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mx, my):
                c, r = (mx - self.x) // SQUARE_SIZE, (my - self.y) // SQUARE_SIZE
                self.promotion_type = self.pieces_symbols[r].lower()
            else:
                self.promotion_type = '-'

    def render(self, screen):
        pygame.draw.rect(screen, 'white', self.rect, border_radius=5)
        for i, symbol in enumerate(self.pieces_symbols):
            screen.blit(PIECE_IMAGE[symbol], (self.x, self.y + i*SQUARE_SIZE))