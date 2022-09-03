import pygame
import os


RANK_NAMES = ["1", "2", "3", "4", "5", "6", "7", "8"]
FILE_NAMES = ["a", "b", "c", "d", "e", "f", "g", "h"]
SQUARE_NAMES = [[f + r for f in FILE_NAMES] for r in RANK_NAMES[::-1]]
STANDARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"
PIECE_IMAGE = {}

for image_name in os.listdir("..\\images\\pieces"):
    color, piece_type = image_name[0], image_name[1]
    PIECE_IMAGE[piece_type[0] if color == 'b' else piece_type[0].upper()] = pygame.image.load(f"..\\images\\pieces\\{image_name}")
    
def coord_to_str(column: int, row: int) -> str:
    return SQUARE_NAMES[row][column]

def str_to_coord(pos: str):
    pos = pos.lower()
    col = FILE_NAMES.index(pos[0])
    row = RANK_NAMES[::-1].index(pos[1])
    return [col, row]


class Piece:
    def __init__(self, piece_symbol, pos=(0, 0)):
        self.image = PIECE_IMAGE[piece_symbol]
        self.img_rect = self.image.get_rect()
        self.rect = self.img_rect
        self.pos = pos
        self.piece_symbol = piece_symbol
        self.color = 'black'
        if piece_symbol.isupper():
            self.color = 'white'

    @property
    def isWhite(self) -> bool:
        return self.color == 'white'

    @property
    def isBlack(self) -> bool:
        return self.color == 'black'

    def render(self, screen, x, y) -> None:
        self.img_rect.x = x
        self.img_rect.y = y
        screen.blit(self.image, (x, y))

    def __bool__(self):
        return True

    def __str__(self) -> str:
        return self.piece_symbol


class Move:
    def __init__(self, from_square: tuple, to_square: tuple, promotion: str=None, capturing: Piece = None, 
                        castling: str = None, 
                        en_passant_target: tuple = None):
        self.from_square = from_square
        self.to_square = to_square
        self.promotion = promotion # piece symbol
        self.capturing = capturing
        self.castling = castling
        self.en_passant_target = en_passant_target

    def uci(self) -> str:
        if self.promotion:
            return coord_to_str(*self.from_square) + coord_to_str(*self.to_square) + self.promotion.lower()
        return coord_to_str(*self.from_square) + coord_to_str(*self.to_square)

    def __str__(self):
        return self.uci()


class Board:
    def __init__(self, fen: str=STANDARD_FEN, x: int = 0, y: int = 0):
        self.set_position(fen)
        self.x: int = x
        self.y: int = y
        self.move_log : Move = []
        self.gen_plegal_movesFunctions = {
            'p': self.gen_plegal_pawn_moves,
            'q': self.gen_plegal_queen_moves,
            'n': self.gen_plegal_knight_moves,
            'k': self.gen_plegal_king_moves,
            'b': self.gen_plegal_bishop_moves,
            'r': self.gen_plegal_rook_moves,
            '.': lambda x: x
        }
        self.plegal_moves = {True: (), False: ()} # True - white, False - black
        self.legal_moves = self.gen_legal_moves()
        self.flipped = False

    def set_position(self, fen: str) -> None:
        fen = fen.strip().split()
        if not self.fen_is_valid(fen):
            raise Exception("Invalid position")
        if fen == None:
            return
        self.grid = [[] for j in range(8)]
        self.white_to_move: bool = (fen[1] == 'w')
        self.half_moves: int = int(fen[4])
        self.full_moves: int = int(fen[5])
        self.en_passant_target: list[int, int] = str_to_coord(fen[3]) if fen[3] != '-' else None
        self.rights_to_castle_queen_side = {"white": False, "black": False}
        self.rights_to_castle_king_side = {"white": False, "black": False}
        self.castling_rights_log = []

        # piece placement
        for row, line in enumerate(fen[0].split("/")):
            col = 0
            for s in line:
                if s.isnumeric():
                    col += int(s)
                    self.grid[row] += ['.']*int(s)
                else:
                    p = Piece(s, pos=(col, row))
                    if p.piece_symbol == "K":
                        self.white_king = p
                    if p.piece_symbol == "k":
                        self.black_king = p
                    self.grid[row].append(Piece(s, pos=(col, row)))
                    col += 1
        
        # castling rights
        for s in fen[2]:
            if s == "q":
                self.rights_to_castle_queen_side['black'] = True
            elif s == "Q":
                self.rights_to_castle_queen_side['white'] = True
            elif s == "k":
                self.rights_to_castle_king_side['black'] = True
            elif s == "K":
                self.rights_to_castle_king_side['white'] = True

    def fen_is_valid(self, fen: list) -> bool:
        white_king_count: int = 0
        black_king_count: int = 0
        for row, line in enumerate(fen[0].split("/")):
            for s in line:
                if s.isnumeric(): continue
                white_king_count += int(s == "K")
                black_king_count += int(s == "k")
        if white_king_count != 1 or black_king_count != 1:
            return False
        return True

    def get_fen(self):
        fen = ""
        for row in self.grid:
            for spot in row:
                fen += str(spot)
            fen += '/'
        for i in range(8, 0, -1):
            fen = fen.replace("."*i, str(i))
        fen = fen[:-1] + ' '
        if self.white_to_move:
            fen += 'w'
        else:
            fen += 'b'
        fen += ' '
        cs = ''
        if self.rights_to_castle_king_side['white']:
            cs += 'K'
        if self.rights_to_castle_queen_side['white']:
            cs += 'Q'
        if self.rights_to_castle_king_side['black']:
            cs += 'k'
        if self.rights_to_castle_queen_side['black']:
            cs += 'q'
        fen += cs if cs != '' else '-'
        fen += ' '
        fen += coord_to_str(*self.en_passant_target) if self.en_passant_target else '-'
        fen += ' '
        fen += str(self.half_moves) + ' '
        fen += str(self.full_moves)
        
        return fen

    def square_is_empty(self, c, r):
        return self.grid[r][c] == '.'

    def square_is_attacked(self, c, r, color):
        """
            Checks if the empty square is attacked by piece of this color
            if the piece is pinned it doesn't mean it can attack a square
        """
        return (c, r) in map(lambda x: x.to_square, self.gen_plegal_moves(color, except_pieces=('k',)))

    def get_king(self, turn: bool) -> Piece:
            for row in self.grid:
                for spot in row:
                    if spot == '.': continue
                    if spot.piece_symbol.lower() == 'k' and ((spot.color == "white") == turn):
                        return spot

    def is_mate(self) -> bool:
        """ Checks if the side to move is in mate."""
        return self.is_check() and len(self.legal_moves) == 0

    def is_stalemate(self) -> bool:
        """ Checks if it's a stalemate"""
        return not self.is_check() and len(self.legal_moves) == 0

    def is_check(self) -> bool:
        """ Checks if the side to move is in check. """
        king = self.get_king(self.white_to_move)
        for move in self.gen_plegal_moves(not self.white_to_move, except_pieces=('k', )):
        # for move in self.plegal_moves[self.white_to_move]:
            if not move.capturing: continue
            if king.pos == move.to_square:
                return True
        return False

    def gen_legal_moves(self):
        self.plegal_moves[self.white_to_move] = list(self.gen_plegal_moves(self.white_to_move))
        self.plegal_moves[not self.white_to_move] = list(self.gen_plegal_moves(not self.white_to_move))
        moves = []
        for move in self.plegal_moves[self.white_to_move]:
            self.replace(move.from_square, move.to_square)
            if not self.is_check():
                moves.append(move)
            self.replace(move.to_square, move.from_square)
            if move.capturing:
                c, r = move.capturing.pos
                self.grid[r][c] = move.capturing
        return moves

    def gen_plegal_moves(self, turn, except_pieces = (None,)):
        moves = []
        for row in self.grid:
            for p in row:
                if p == '.': continue
                if p.isWhite !=turn: continue
                if p.piece_symbol.lower() in except_pieces: continue
                for m in self.gen_plegal_movesFunctions[str(p).lower()](p):
                    moves.append(m)
        return moves
    
    def gen_plegal_pawn_moves(self, pawn: Piece):
        pmoves = []
        c, r = pawn.pos
        dy = -1
        if not pawn.isWhite:
            dy = 1
        if r + dy >= 8 or r + dy < 0: return pmoves
        if self.grid[r + dy][c] == '.':
            # if white pawn is at 7th rank or black pawn is at 2nd rank
            if pawn.isWhite and r == 1 or not pawn.isWhite and r == 6:
                for promotion_type in ('q', 'r', 'n', 'b'):
                    pmoves.append(Move((c, r), (c, r + dy), promotion=promotion_type))
            else:
                pmoves.append(Move((c, r), (c, r + dy)))
            if 0 <= r + 2*dy <= 7:
                if (pawn.pos[1] in (1, 6)) and self.grid[r + 2*dy][c] == '.':
                    pmoves.append(Move((c, r), (c, r + dy*2)))
        for dx in (-1, 1):
            if not (0 <= r + dy <= 7 and 0 <= c + dx <= 7): continue
            if self.grid[r + dy][c + dx] != '.':
                if self.grid[r + dy][c + dx].isWhite != pawn.isWhite:
                    pmoves.append(Move((c, r), (c + dx, r + dy),capturing=self.grid[r + dy][c + dx]))
            if (c + dx, r + dy) == self.en_passant_target:
                pmoves.append(Move((c, r), (c + dx, r + dy), en_passant_target=self.en_passant_target))

        return pmoves

    def gen_plegal_bishop_moves(self, bishop: Piece):
        pmoves = []
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1))
        c, r = bishop.pos
        for dx, dy in directions:
            i = 1
            while 0 <= c + dx*i <= 7 and 0 <= r + dy*i <= 7:
                spot = self.grid[r + dy*i][c + dx*i]
                if spot == '.':
                    pmoves.append(Move((c, r), (c + dx*i, r + dy*i)))
                else:
                    if spot.isWhite != bishop.isWhite:
                        pmoves.append(Move((c, r), (c + dx*i, r + dy*i), capturing=spot))
                    break
                i += 1
        return pmoves

    def gen_plegal_knight_moves(self, knight: Piece):
        pmoves = []
        c, r = knight.pos
        for dy in (-2, -1, 1, 2):
            for dx in (-2, -1, 1, 2):
                if abs(dx) == abs(dy): continue
                if not (0 <= c + dx <= 7 and 0 <= r + dy <= 7): continue
                spot = self.grid[r + dy][c + dx]
                if spot == '.':
                    pmoves.append(Move((c,r), (c + dx, r + dy)))
                else:
                    if spot.isWhite != knight.isWhite:
                        pmoves.append(Move((c, r), (c + dx, r + dy), capturing=spot))
        return pmoves

    def gen_plegal_king_moves(self, king: Piece):
        pmoves = []
        c, r = king.pos
        directions = ((1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1))
        for dx, dy in directions:
            if not (0 <= c + dx <= 7 and 0 <= r + dy <= 7): continue
            spot = self.grid[r + dy][c + dx]
            if spot == '.':
                pmoves.append(Move((c,r), (c + dx, r + dy)))
            else:
                if spot.isWhite != king.isWhite:
                    pmoves.append(Move((c, r), (c + dx, r + dy), capturing=spot))

        opposite_king = self.get_king(not king.isWhite)
        for i in range(len(pmoves) - 1, -1, -1):
            mc, mr = pmoves[i].to_square
            kc, kr = opposite_king.pos
            if abs(kc - mc) <= 1 and abs(kr - mr) <= 1:
                pmoves.pop(i)

        # generating castle-moves
        if self.rights_to_castle_king_side[king.color] and not self.is_check(): # for castling to king side
            if all([self.square_is_empty(c + i, r) for i in (1, 2)]) \
            and all([not self.square_is_attacked(c + i, r, not king.isWhite) for i in (1, 2)]):
                pmoves.append(Move((c, r), (c + 2, r), castling='k'))
        if self.rights_to_castle_queen_side[king.color] and not self.is_check(): # for castling to queen side
            if all([self.square_is_empty(c - i, r) for i in (1,2,3)]) \
            and all([not self.square_is_attacked(c - i, r, not king.isWhite) for i in (1, 2)]):
                pmoves.append(Move((c, r), (c - 2, r), castling='q'))

        return pmoves

    def gen_plegal_rook_moves(self, rook: Piece):
        pmoves = []
        directions = ((1, 0), (-1, 0), (0, -1), (0, 1))
        c, r = rook.pos
        for dx, dy in directions:
            i = 1
            while 0 <= c + dx*i <= 7 and 0 <= r + dy*i <= 7:
                spot = self.grid[r + dy*i][c + dx*i]
                if spot == '.':
                    pmoves.append(Move((c, r), (c + dx*i, r + dy*i)))
                else:
                    if spot.isWhite != rook.isWhite:
                        pmoves.append(Move((c, r), (c + dx*i, r + dy*i), capturing=spot))
                    break
                i += 1
        return pmoves

    def gen_plegal_queen_moves(self, queen: Piece):
        pmoves = self.gen_plegal_bishop_moves(queen) + self.gen_plegal_rook_moves(queen)
        return pmoves

    def get_move_from_uci(self, uci) -> Move:
        from_s = str_to_coord(uci[:2].lower())
        to_s = str_to_coord(uci[2:4].lower())
        p = None if len(uci) <= 4 else uci[4]
        return Move(from_s, to_s, p, self.grid[to_s[1]][to_s[0]] != '.')

    def push(self, move: Move):
        self.en_passant_target = None
        if move.uci() not in map(lambda x: x.uci(), self.legal_moves):
            raise Exception(f"Invalid move {move.uci()}")
        self.castling_rights_log.append([self.rights_to_castle_king_side.copy(), self.rights_to_castle_queen_side.copy()])
        self.move_log.append(move)
        fcol, frow = move.from_square
        tcol, trow = move.to_square
        if move.en_passant_target:
            self.grid[frow][tcol] = '.'
        self.replace(move.from_square, move.to_square)
        self.half_moves += 1
        if not self.grid[trow][tcol].isWhite:
            self.full_moves += 1
        self.white_to_move = not self.white_to_move

        # if move is promotion
        if move.promotion:
            symbol = move.promotion if not self.grid[trow][tcol].isWhite else move.promotion.upper()
            self.grid[trow][tcol] = Piece(symbol, pos=move.to_square)

        # if move is castle-move
        if move.castling == 'q':
            self.replace((0, trow), (3, trow))
            self.grid[trow][3].pos = (3, trow)
        elif move.castling == 'k':
            self.replace((7, trow), (5, trow))
            self.grid[trow][5].pos = (5, trow)
        color = self.grid[trow][tcol].color
        if self.grid[trow][tcol].piece_symbol in ('K', 'k'):
            self.rights_to_castle_king_side[color] = False
            self.rights_to_castle_queen_side[color] = False
        if self.grid[trow][tcol].piece_symbol in ('R', 'r'):
            if fcol == 7:
                self.rights_to_castle_king_side[color] = False
            elif fcol == 0:
                self.rights_to_castle_queen_side[color] = False

        if abs(trow - frow) == 2:
            if self.grid[trow][tcol].piece_symbol == 'P':
                self.en_passant_target = (tcol, trow + 1)
            if self.grid[trow][tcol].piece_symbol == 'p':
                self.en_passant_target = (tcol, trow - 1)
        
        self.legal_moves = self.gen_legal_moves()
        

    def undo_last_move(self):
        if self.move_log == []:
            return
        self.en_passant_target = None
        move = self.move_log.pop()
        self.rights_to_castle_king_side, self.rights_to_castle_queen_side = self.castling_rights_log.pop()
        if move.en_passant_target:
            self.en_passant_target = move.en_passant_target
            symbol = 'P' if self.white_to_move else 'p'
            self.grid[move.from_square[1]][move.to_square[0]] = Piece(symbol, (move.to_square[0], move.from_square[1]))
        fcol, frow = move.to_square
        tcol, trow = move.from_square
        self.grid[trow][tcol] = self.grid[frow][fcol]
        self.grid[trow][tcol].pos = (tcol, trow)
        self.grid[frow][fcol] = '.' if not move.capturing else move.capturing
        self.half_moves -= 1
        if self.white_to_move:
            self.full_moves -= 1
        self.white_to_move = not self.white_to_move
        
        if move.promotion:
            symbol = 'P' if self.grid[trow][tcol].isWhite else 'p'
            self.grid[trow][tcol] = Piece(symbol, move.from_square)
        
        # if move is castle-move
        if move.castling == 'q':
            self.grid[trow][3].pos = (0, trow)
            self.replace((3, trow), (0, trow))
        elif move.castling == 'k':
            self.grid[trow][5].pos = (7, trow)
            self.replace((5, trow), (7, trow))

        self.legal_moves = self.gen_legal_moves()
    
    def replace(self, from_square, to_square):
        fcol, frow = from_square
        tcol, trow = to_square
        self.grid[trow][tcol] = '.'
        self.grid[trow][tcol], self.grid[frow][fcol] = self.grid[frow][fcol], self.grid[trow][tcol]
        self.grid[trow][tcol].pos = to_square

    def print_castling_info(self):
        for king in (self.get_king(True), self.get_king(False)):
            c, r = king.pos
            print(f"rights of {king} to castle to king side:", self.rights_to_castle_king_side[king.color])
            print(f"rights of {king} to castle to queen side:", self.rights_to_castle_queen_side[king.color])
            # if self.rights_to_castle_king_side[king.color] and not self.is_check(): # for castling to king side
            #     print(f"Empty king side: {king}", all([self.square_is_empty(c + i, r) for i in (1, 2)]))
            #     print(f"Not attacked king side: {king}", all([not self.square_is_attacked(c + i, r, not king.isWhite) for i in (1, 2)]))
            #     if all([self.square_is_empty(c + i, r) for i in (1, 2)]) \
            #     and all([not self.square_is_attacked(c + i, r, not king.isWhite) for i in (1, 2)]):
            #         print(f"King at {king.pos} can castle to king side")
                    
            # if self.rights_to_castle_queen_side[king.color] and not self.is_check(): # for castling to queen side
            #     print(f"Empty queen side: {king}", all([self.square_is_empty(c - i, r) for i in (1, 2, 3)]))
            #     print(f"Not attacked queen side: {king}", all([not self.square_is_attacked(c - i, r, not king.isWhite) for i in (1, 2)]))
            #     if all([self.square_is_empty(c - i, r) for i in (1,2,3)]) \
            #     and all([not self.square_is_attacked(c - i, r, not king.isWhite) for i in (1, 2)]):
            #         print(f"King at {king.pos} can castle to queen side")

    def __str__(self):
        res = ''
        for i, row in enumerate(self.grid):
            # res += f"{8 - i} |"
            for s in row:
                if type(s) != Piece:
                    res += f"{s} "
                else:
                    res += f"{s.piece_symbol} "
            res += "\n"
        # res += "   " + "-"*15 + '\n'
        # res += "   a b c d e f g h\n"
        return res    
