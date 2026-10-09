import pygame
from game.maze import CELL

SPEED = 3

class Player:
    def __init__(self, r, c, cell_size=CELL, origin=(0, 0)):
        self.r = r
        self.c = c
        self.cell_size = cell_size
        self.origin = origin
        self.speed = max(2, round(SPEED * cell_size / CELL))
        size = max(10, cell_size // 2)
        x = origin[0] + c * cell_size + cell_size // 2
        y = origin[1] + r * cell_size + cell_size // 2
        self.rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        self.color = (60,120,220)

    def move(self, keys, walls, rows, cols):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = self.speed

        # Wall-aware movement (check cell boundaries)
        new_rect = self.rect.move(dx, 0)
        if not self._hits_wall(new_rect, walls, rows, cols):
            self.rect = new_rect
        new_rect = self.rect.move(0, dy)
        if not self._hits_wall(new_rect, walls, rows, cols):
            self.rect = new_rect

    def _hits_wall(self, rect, walls, rows, cols):
        origin_x, origin_y = self.origin
        # Check corners of player rect against wall segments
        for px, py in [(rect.left, rect.top),(rect.right-1,rect.top),(rect.left,rect.bottom-1),(rect.right-1,rect.bottom-1)]:
            cr = (py - origin_y) // self.cell_size
            cc = (px - origin_x) // self.cell_size
            if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
                return True

        top_cell = (rect.top - origin_y) // self.cell_size
        bottom_cell = (rect.bottom - 1 - origin_y) // self.cell_size
        left_cell = (rect.left - origin_x) // self.cell_size
        right_cell = (rect.right - 1 - origin_x) // self.cell_size

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
