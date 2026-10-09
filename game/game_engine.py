import pygame
import json
import math
import time
from pathlib import Path
from game.maze import generate_maze, find_shortest_path, CELL
from game.player import Player

FPS = 60
BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
COLS, ROWS = 15, 13

WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 60

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Runner")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 36, bold=True)
        self.show_path = False
        self.leaderboard_path = Path(__file__).resolve().parent.parent / "leaderboard.json"
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        self.path = find_shortest_path(self.walls, (0, 0), (ROWS - 1, COLS - 1))
        self.exit_rect = pygame.Rect((COLS-1)*CELL+5, (ROWS-1)*CELL+5, CELL-10, CELL-10)
        self.elapsed = 0
        self.won = False
        self.leaderboard = self._load_leaderboard()
        self.new_time_rank = None
        self.start_time = time.perf_counter()

    def _load_leaderboard(self):
        try:
            with self.leaderboard_path.open(encoding="utf-8") as leaderboard_file:
                entries = json.load(leaderboard_file)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(entries, list):
            return []

        scores = []
        for entry in entries:
            if isinstance(entry, bool) or not isinstance(entry, (int, float)):
                continue
            try:
                score = float(entry)
            except (OverflowError, ValueError):
                continue
            if math.isfinite(score) and score >= 0:
                scores.append(score)
        return sorted(scores)[:5]

    def _record_completion(self):
        score = round(self.elapsed, 3)
        leaderboard = self._load_leaderboard()
        rank = next(
            (index for index, entry in enumerate(leaderboard) if score <= entry),
            len(leaderboard),
        )
        leaderboard.insert(rank, score)
        self.new_time_rank = rank + 1 if rank < 5 else None
        self.leaderboard = leaderboard[:5]

        with self.leaderboard_path.open("w", encoding="utf-8") as leaderboard_file:
            json.dump(self.leaderboard, leaderboard_file, indent=2)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                self.show_path = not self.show_path
        return True

    def update(self):
        if self.won:
            return
        previous_cell = (
            self.player.rect.centery // CELL,
            self.player.rect.centerx // CELL,
        )
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)
        current_cell = (
            self.player.rect.centery // CELL,
            self.player.rect.centerx // CELL,
        )
        if current_cell != previous_cell:
            self.path = find_shortest_path(
                self.walls, current_cell, (ROWS - 1, COLS - 1)
            )
        self.elapsed = time.perf_counter() - self.start_time
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True
            self._record_completion()

    def draw_maze(self):
        wall_w = 3
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c*CELL, r*CELL
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x+CELL,y), wall_w)
                if w[1]: pygame.draw.line(self.screen, WALL_COLOR, (x,y+CELL), (x+CELL,y+CELL), wall_w)
                if w[2]: pygame.draw.line(self.screen, WALL_COLOR, (x+CELL,y), (x+CELL,y+CELL), wall_w)
                if w[3]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x,y+CELL), wall_w)

    def draw(self):
        self.screen.fill(BG)
        if self.show_path:
            path_square = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            path_square.fill((30, 170, 220, 90))
            for r, c in self.path:
                self.screen.blit(path_square, (c * CELL, r * CELL))
        self.draw_maze()
        pygame.draw.rect(self.screen, EXIT_COLOR, self.exit_rect, border_radius=4)
        ex_label = self.font.render("EXIT", True, (20,80,20))
        self.screen.blit(ex_label, (self.exit_rect.x+2, self.exit_rect.y+4))
        self.player.draw(self.screen)

        fog = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        fog.fill((0, 0, 0, 255))
        pygame.draw.circle(fog, (0, 0, 0, 0), self.player.rect.center, 3 * CELL)
        self.screen.blit(fog, (0, 0))

        hud = pygame.Rect(0, ROWS*CELL, WIDTH, 60)
        pygame.draw.rect(self.screen, (30,30,50), hud)
        time_surf = self.font.render(f"Time: {self.elapsed:.1f}s   R = New Maze", True, (200,200,200))
        self.screen.blit(time_surf, (10, ROWS*CELL+18))

        if self.won:
            overlay = pygame.Surface((WIDTH, ROWS*CELL), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            self.screen.blit(overlay, (0,0))
            msg = self.big_font.render(f"Solved in {self.elapsed:.1f}s!", True, (80,240,80))
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, ROWS*CELL//2 - 150))
            heading = self.font.render("BEST TIMES", True, (200,200,200))
            self.screen.blit(heading, (WIDTH//2 - heading.get_width()//2, ROWS*CELL//2 - 95))
            for index, score in enumerate(self.leaderboard):
                rank = index + 1
                color = (80,240,80) if rank == self.new_time_rank else (220,220,220)
                label = f"{rank}. {score:.3f}s"
                if rank == self.new_time_rank:
                    label += "  NEW"
                entry = self.font.render(label, True, color)
                y = ROWS*CELL//2 - 55 + index*32
                self.screen.blit(entry, (WIDTH//2 - entry.get_width()//2, y))
            sub = self.font.render("Press R for a new maze", True, (200,200,200))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, ROWS*CELL//2 + 145))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
