import pygame
from game.maze import CELL

SPEED = 3

class Player:
    def __init__(self, r, c):
        self.r = r
        self.c = c
        x = c*CELL + CELL//2
        y = r*CELL + CELL//2
        self.rect = pygame.Rect(x-10, y-10, 20, 20)
        self.color = (60,120,220)

    def move(self, keys, walls, rows, cols):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = SPEED

        # Wall-aware movement (check cell boundaries)
        new_rect = self.rect.move(dx, 0)
        if not self._hits_wall(new_rect, walls, rows, cols):
            self.rect = new_rect
        new_rect = self.rect.move(0, dy)
        if not self._hits_wall(new_rect, walls, rows, cols):
            self.rect = new_rect

    def _hits_wall(self, rect, walls, rows, cols):
        # Check corners of player rect against wall segments
        for px, py in [(rect.left, rect.top),(rect.right-1,rect.top),(rect.left,rect.bottom-1),(rect.right-1,rect.bottom-1)]:
            cr = py // CELL
            cc = px // CELL
            if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
                return True

        top_cell = rect.top // CELL
        bottom_cell = (rect.bottom - 1) // CELL
        left_cell = rect.left // CELL
        right_cell = (rect.right - 1) // CELL

        for col in range(left_cell, right_cell):
            for row in range(top_cell, bottom_cell + 1):
                if walls[row][col][2]:
                    return True

        for row in range(top_cell, bottom_cell):
            for col in range(left_cell, right_cell + 1):
                if walls[row][col][1]:
                    return True
        return False

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)
