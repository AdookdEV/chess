import pygame


class Player:
    def __init__(self, turn: bool, is_human: bool = False):
        self.is_human = is_human
        self.turn = turn
        
    def make_move(self, move):
        if self.is_human:
            pass