import sys
import pygame
from ui.button import Button
from config import *
from Chess import *
from functools import reduce



HIHGLIGHT_SQUARE = pygame.image.load("../images/highlight_square.png")
MOVE_IMAGE =  pygame.image.load("../images/move.png")
TARGET_SQUARE = pygame.image.load("../images/target.png")
MAIN_MENU_BG_IMAGE = pygame.image.load("../images/main_menu.png")
RANK_NAMES = ["1", "2", "3", "4", "5", "6", "7", "8"]
FILE_NAMES = ["a", "b", "c", "d", "e", "f", "g", "h"]
MENU_FONT = pygame.font.Font("../fonts/Segoe-UI-Bold.ttf", 20)

CAPTURING_SOUND = pygame.mixer.Sound("../audio/capturing.mp3")
CASTLING_SOUND = pygame.mixer.Sound("../audio/castling.mp3")
MOVE_SOUND = pygame.mixer.Sound("../audio/move.mp3")
PROMOTION_SOUND = pygame.mixer.Sound("../audio/promotion.mp3")
CHECK_SOUND = pygame.mixer.Sound("../audio/check.mp3")

ARROW_IMG = pygame.image.load("../images/arrow.png")
FLAG_IMG = pygame.image.load("../images/white_flag.png")

def Render_Text(what, color, where, window, size=15):
    font = pygame.font.Font(None, size)
    text = font.render(what, 1, pygame.Color(color))
    window.blit(text, where)

def get_text(text, color, size=15, font = None):
    if not font:
        font = pygame.font.Font(font, size)
    text = font.render(text, 1, pygame.Color(color))
    return text

RANKS = [get_text(r, 'grey', size=25) for r in RANK_NAMES]
FILES = [get_text(f, 'grey', size=25) for f in FILE_NAMES]

def flip_coordinates(x, y):
    return 7 - x, 7 - y


class Scene(object):
    def __init__(self):
        self.manager = None
        self.game_window = pygame.display.get_surface()

    def render(self, screen):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def handle_events(self, events):
        raise NotImplementedError


class MainMenuScene(Scene):
    def __init__(self):
        super(MainMenuScene, self).__init__()
        self.vs_computer_button = Button((200, 221), (250, 50), 4, text='VS COMPUTER', font=MENU_FONT, border_radius=8)
        self.two_player_online_button = Button((200, 298), (250, 50), 4, text='VS PLAYER ONLINE', font=MENU_FONT, border_radius=8)
        self.two_player_offline_button = Button((200, 376), (250, 50), 4, text='VS PLAYER OFFLINE', font=MENU_FONT, border_radius=8)
        self.bg_image = MAIN_MENU_BG_IMAGE

    def render(self, screen):
        # screen.fill('black')
        screen.blit(self.bg_image, (0, 0))
        self.vs_computer_button.render(screen)
        self.two_player_online_button.render(screen)
        self.two_player_offline_button.render(screen)

    def update(self):
        self.vs_computer_button.check_click()
        self.two_player_online_button.check_click()
        if self.two_player_offline_button.check_click():
            self.manager.go_to(GameScene())

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        

class SceneManager(object):
    def __init__(self):
        self.go_to(MainMenuScene())

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self


class PromotionBox:
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


class WinnerBox:
    def __init__(self, x=151, y=251, winner=None):
        self.bg = pygame.image.load('../images/winner_menu_bg.png')
        self.winner = winner
        self.x = x
        self.y = y
        
        self.text_color = "#144757"
        text = f"{winner} won" if winner else "Draw"
        self.text_surf = get_text(text, self.text_color, size=18, font=MENU_FONT)
        
        self.back_to_menu = Button((self.x + 22, self.y+ 74), (80, 25), 1, border_radius=5, text="Menu")
        self.rematch = Button((self.x + 135, self.y+ 74), (80, 25), 1, border_radius=5, text='Rematch')
        
    def render(self, screen):
        screen.blit(self.bg, (self.x, self.y))
        self.back_to_menu.render(screen)
        self.rematch.render(screen)
        screen.blit(self.text_surf, (self.x + 70, self.y + 20))


class GameScene(Scene):
    def __init__(self, white_is_human=True, black_is_human=True):
        super(GameScene, self).__init__()
        # self.board = Board(fen="8/2P5/2KP4/5k2/5pp1/8/8/8 b - - 0 1", x=30, y=75)
        self.board = Board(x=30, y=75)
        self.selected_piece = None
        self.check = False
        self.mate = False
        self.stalemate = False
        self.is_promotion = False
        self.board_img = pygame.image.load("..\\images\\board.jpg")
        self.promotion_menu = None
        self.drag_piece = False
        self.clicks_on_selpiece = 0
        self.piece_move = []
        self.flip_board = False
        self.game_over = False
        self.winner = None # w/b/s
        self.winner_menu = None
        
        self.white_is_human = white_is_human
        self.black_is_human = black_is_human
        
        self.give_up_button = Button((553, 409), (53, 56), 3, border_radius=2, img=FLAG_IMG)
        self.undo_button = Button((553, 479), (53, 56), 3, border_radius=2, img=ARROW_IMG)

    def render_coordinates(self, screen):
        ranks = RANKS.copy() if self.flip_board else RANKS.copy()[::-1]
        files = FILES.copy() if not self.flip_board else FILES.copy()[::-1]
        for i, r in enumerate(ranks):
            x = self.board.x - 20
            y = self.board.y + i*SQUARE_SIZE + 25
            screen.blit(r, (x, y))
        for i, f in enumerate(files):
            x = self.board.x + i*SQUARE_SIZE + 25
            y = self.board.y + 480 + 5
            screen.blit(f, (x, y))
        
    def render_board(self, screen):
        screen.blit(self.board_img, (self.board.x, self.board.y))

    def render_pieces(self, screen):
        pieces = list(filter(lambda x: x != '.', reduce(lambda x, y: x + y, self.board.grid)))
        pieces = sorted(pieces, key=lambda x: int(x == self.selected_piece))
        for piece in pieces:
            j, i = piece.pos
            if self.flip_board:
                j, i = flip_coordinates(j, i)
            x = self.board.x + j*SQUARE_SIZE
            y = self.board.y + i*SQUARE_SIZE
            if self.selected_piece == piece and self.drag_piece:
                mx, my = pygame.mouse.get_pos()
                x = mx - SQUARE_SIZE // 2
                y = my - SQUARE_SIZE // 2
                x = min(self.board.x + 480 - SQUARE_SIZE, max(self.board.x, x))
                y = min(self.board.y + 480 - SQUARE_SIZE, max(self.board.y, y))
            piece.render(screen, x, y)

    def render_move(self, screen, move):
        c, r = move.to_square
        if self.flip_board:
            c, r = flip_coordinates(c, r)
        x = c*SQUARE_SIZE  + self.board.x
        y = r*SQUARE_SIZE + self.board.y
        if move.capturing:
            screen.blit(TARGET_SQUARE, (x, y))
        else:
            screen.blit(MOVE_IMAGE, (x, y))

    def render_board_moves(self, screen):
        if self.selected_piece and self.drag_piece:
            mx, my = pygame.mouse.get_pos()
            x = (mx - self.board.x) - (mx - self.board.x)%SQUARE_SIZE + self.board.x
            y = (my - self.board.y) - (my - self.board.y)%SQUARE_SIZE + self.board.y
            x = min(self.board.x + 480 - SQUARE_SIZE, max(self.board.x, x))
            y = min(self.board.y + 480 - SQUARE_SIZE, max(self.board.y, y))
            pygame.draw.rect(screen, 'grey', (x, y, SQUARE_SIZE, SQUARE_SIZE), 3)
        for move in self.board.legal_moves:
            c, r = move.from_square
            if self.selected_piece == self.board.grid[r][c]:
                self.render_move(screen, move)

    def highlight_last_move(self, screen):
        if self.board.move_log == []: return
        c1, r1 = self.board.move_log[-1].from_square
        c2, r2 = self.board.move_log[-1].to_square
        if self.flip_board:
            c1, r1 = flip_coordinates(c1, r1)
            c2, r2 = flip_coordinates(c2, r2)
        x1, y1 = c1*SQUARE_SIZE + self.board.x, r1*SQUARE_SIZE + self.board.y
        x2, y2 = c2*SQUARE_SIZE + self.board.x, r2*SQUARE_SIZE + self.board.y
        screen.blit(HIHGLIGHT_SQUARE, (x1, y1))
        screen.blit(HIHGLIGHT_SQUARE, (x2, y2))
        

    def render(self, screen):
        screen.fill(COLORS["bg"])
        self.render_coordinates(screen)
        self.render_board(screen)
        self.highlight_last_move(screen)
        if self.selected_piece:
            c, r = self.selected_piece.pos
            if self.flip_board:
                c, r = flip_coordinates(c, r)
            x = c*SQUARE_SIZE  + self.board.x
            y = r*SQUARE_SIZE  + self.board.y
            screen.blit(HIHGLIGHT_SQUARE, (x, y)) # highlight selected piece
            self.render_board_moves(screen)
        self.render_pieces(screen)
        if self.is_promotion:
            self.promotion_menu.render(screen)
        self.give_up_button.render(screen)
        self.undo_button.render(screen)
        if self.winner_menu:
            self.winner_menu.render(screen)


    def make_move(self, from_square, to_square, promotion=None):
        if self.game_over:
            self.reset_state()
            return
        play = False
        for move in self.board.legal_moves:
            if (move.to_square, move.from_square, move.promotion) == (to_square, from_square, promotion):
                self.board.push(move)
                play = True
                break
        self.reset_state()
        if play:
            self.play_sound(move)
        

    def board_mouse_event_handler(self, event, mx, my):
        if self.is_promotion: return
        if not(0 < mx - self.board.x < 8*SQUARE_SIZE and 0 < my - self.board.y < 8*SQUARE_SIZE): return
        col_idx = (mx - self.board.x) // SQUARE_SIZE
        row_idx = (my - self.board.y) // SQUARE_SIZE
        if self.flip_board:
            col_idx, row_idx = flip_coordinates(col_idx, row_idx)
        spot = self.board.grid[row_idx][col_idx] if self.board.grid[row_idx][col_idx] != '.' else None
        if not self.selected_piece:
            self.piece_move = []
        if event.type == pygame.MOUSEBUTTONDOWN:
            if spot and spot.isWhite == self.board.white_to_move:
                self.selected_piece = spot
            else:
                if self.selected_piece:
                    self.piece_move = [self.selected_piece.pos, (col_idx, row_idx)]
        if event.type == pygame.MOUSEBUTTONUP:
            if self.selected_piece and spot != self.selected_piece:
                self.piece_move = [self.selected_piece.pos, (col_idx, row_idx)]
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.selected_piece and self.selected_piece.img_rect.collidepoint((mx, my)):
                self.drag_piece = True
            else:
                self.drag_piece = False
        if event.type == pygame.MOUSEBUTTONUP:
             self.drag_piece = False
    
    def play_sound(self, move):
            if self.check:
                CHECK_SOUND.play()
            elif move.promotion:
                PROMOTION_SOUND.play()
            elif move.castling:
                CASTLING_SOUND.play()
            elif move.capturing:
                CAPTURING_SOUND.play()
            else:
                MOVE_SOUND.play()
    
    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if self.white_is_human and self.board.white_to_move or \
            self.black_is_human and not self.board.white_to_move:
                self.board_mouse_event_handler(event, mx, my)
            else:
                if not self.white_is_human and self.board.white_to_move or not self.black_is_human and not self.board.white_to_move:
                    pass
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.board.print_castling_info()
                if event.key == pygame.K_f:
                    pass
                    # print(get_engine_move(fen=self.board.get_fen()))
                if event.key == pygame.K_x:
                    self.flip_board = not self.flip_board   

            if self.is_promotion:
                self.promotion_menu.handle_events(event)

    def reset_state(self):
        self.check = self.board.is_check()
        self.mate = self.board.is_mate()
        self.stalemate = self.board.is_stalemate()
        self.selected_piece = None
        self.is_promotion = False
        self.piece_move = []
        self.promotion_menu = None

    def update(self):
        promotion_type = None
        
        # making move
        if len(self.piece_move) == 2:
            row = self.piece_move[1][1]
            col = self.piece_move[1][0]
            if self.flip_board:
                col, row = flip_coordinates(col, row)
            if self.selected_piece and self.selected_piece.piece_symbol in ("p", "P") \
            and row in (0, 7) and not self.is_promotion and abs(self.piece_move[0][1] - self.piece_move[1][1]) == 1:
                x, y = self.board.x + col*SQUARE_SIZE, self.board.y + row*SQUARE_SIZE
                self.promotion_menu = PromotionBox(x, y, self.board.white_to_move, self.board)
                self.is_promotion = True
            if self.is_promotion:
                promotion_type = self.promotion_menu.result()
            if not self.is_promotion or promotion_type:
                self.make_move(*self.piece_move, promotion = promotion_type)

        if self.give_up_button.check_click():
            self.game_over = True
            self.winner = 'White' if not self.board.white_to_move else 'Black'
        if self.undo_button.check_click() and not self.game_over:
            if self.board.move_log != []:
                    self.play_sound(self.board.move_log[-1])
                    self.board.undo_last_move()
                    self.reset_state()

        if self.mate:
            self.winner = 'White' if not self.board.white_to_move else 'Black'
            self.game_over = True
        elif self.stalemate:
            self.winner = None
            self.game_over = True
        if self.game_over:
            self.winner_menu = WinnerBox(winner=self.winner)
            
        if self.winner_menu:
            if self.winner_menu.back_to_menu.check_click():
                self.manager.go_to(MainMenuScene())
            if self.winner_menu.rematch.check_click():
                self.manager.go_to(GameScene())
