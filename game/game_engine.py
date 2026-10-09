import pygame
import json
import math
import time
from pathlib import Path
from game.maze import generate_maze, find_shortest_path
from game.player import Player

FPS = 60
BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
DIFFICULTIES = {"Easy": (10, 8), "Medium": (15, 13), "Hard": (20, 18)}
WIDTH, HEIGHT = 850, 820
HUD_HEIGHT = 60
BOARD_HEIGHT = HEIGHT - HUD_HEIGHT

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
        self.difficulty = None
        self.selecting = True
        button_width, button_height = 320, 66
        first_button_y = 300
        self.difficulty_buttons = {
            name: pygame.Rect(
                (WIDTH - button_width) // 2,
                first_button_y + index * 88,
                button_width,
                button_height,
            )
            for index, name in enumerate(DIFFICULTIES)
        }

    def start_game(self, difficulty):
        self.difficulty = difficulty
        self.cols, self.rows = DIFFICULTIES[difficulty]
        self.cell_size = min(WIDTH // self.cols, BOARD_HEIGHT // self.rows)
        self.maze_width = self.cols * self.cell_size
        self.maze_height = self.rows * self.cell_size
        self.maze_origin = (
            (WIDTH - self.maze_width) // 2,
            (BOARD_HEIGHT - self.maze_height) // 2,
        )
        self.selecting = False
        self.reset()

    def reset(self):
        self.walls = generate_maze(self.cols, self.rows)
        self.player = Player(0, 0, self.cell_size, self.maze_origin)
        self.path = find_shortest_path(
            self.walls, (0, 0), (self.rows - 1, self.cols - 1)
        )
        exit_padding = max(4, self.cell_size // 8)
        self.exit_rect = pygame.Rect(
            self.maze_origin[0] + (self.cols - 1) * self.cell_size + exit_padding,
            self.maze_origin[1] + (self.rows - 1) * self.cell_size + exit_padding,
            self.cell_size - 2 * exit_padding,
            self.cell_size - 2 * exit_padding,
        )
        self.elapsed = 0
        self.won = False
        self.leaderboards = self._load_leaderboards()
        self.leaderboard = self.leaderboards[self.difficulty]
        self.new_time_rank = None
        self.start_time = time.perf_counter()

    def _load_leaderboards(self):
        try:
            with self.leaderboard_path.open(encoding="utf-8") as leaderboard_file:
                entries = json.load(leaderboard_file)
        except (OSError, UnicodeError, json.JSONDecodeError):
            entries = {}

        if isinstance(entries, list):
            entries = {"Medium": entries}
        if not isinstance(entries, dict):
            entries = {}

        leaderboards = {}
        for difficulty in DIFFICULTIES:
            scores = []
            difficulty_entries = entries.get(difficulty, [])
            if isinstance(difficulty_entries, list):
                for entry in difficulty_entries:
                    if isinstance(entry, bool) or not isinstance(entry, (int, float)):
                        continue
                    try:
                        score = float(entry)
                    except (OverflowError, ValueError):
                        continue
                    if math.isfinite(score) and score >= 0:
                        scores.append(score)
            leaderboards[difficulty] = sorted(scores)[:5]
        return leaderboards

    def _record_completion(self):
        score = round(self.elapsed, 3)
        leaderboards = self._load_leaderboards()
        leaderboard = leaderboards[self.difficulty]
        rank = next(
            (index for index, entry in enumerate(leaderboard) if score <= entry),
            len(leaderboard),
        )
        leaderboard.insert(rank, score)
        self.new_time_rank = rank + 1 if rank < 5 else None
        self.leaderboard = leaderboard[:5]
        leaderboards[self.difficulty] = self.leaderboard
        self.leaderboards = leaderboards

        with self.leaderboard_path.open("w", encoding="utf-8") as leaderboard_file:
            json.dump(self.leaderboards, leaderboard_file, indent=2)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if self.selecting:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for difficulty, button in self.difficulty_buttons.items():
                        if button.collidepoint(event.pos):
                            self.start_game(difficulty)
                            break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_h:
                    self.show_path = not self.show_path
        return True

    def update(self):
        if self.selecting or self.won:
            return
        previous_cell = (
            (self.player.rect.centery - self.maze_origin[1]) // self.cell_size,
            (self.player.rect.centerx - self.maze_origin[0]) // self.cell_size,
        )
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, self.rows, self.cols)
        current_cell = (
            (self.player.rect.centery - self.maze_origin[1]) // self.cell_size,
            (self.player.rect.centerx - self.maze_origin[0]) // self.cell_size,
        )
        if current_cell != previous_cell:
            self.path = find_shortest_path(
                self.walls, current_cell, (self.rows - 1, self.cols - 1)
            )
        self.elapsed = time.perf_counter() - self.start_time
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True
            self._record_completion()

    def draw_maze(self):
        wall_w = max(2, self.cell_size // 14)
        origin_x, origin_y = self.maze_origin
        for r in range(self.rows):
            for c in range(self.cols):
                x = origin_x + c * self.cell_size
                y = origin_y + r * self.cell_size
                cell_size = self.cell_size
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x+cell_size,y), wall_w)
                if w[1]: pygame.draw.line(self.screen, WALL_COLOR, (x,y+cell_size), (x+cell_size,y+cell_size), wall_w)
                if w[2]: pygame.draw.line(self.screen, WALL_COLOR, (x+cell_size,y), (x+cell_size,y+cell_size), wall_w)
                if w[3]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x,y+cell_size), wall_w)

    def draw(self):
        if self.selecting:
            self.draw_difficulty_select()
        else:
            self.draw_game()
        pygame.display.flip()

    def draw_difficulty_select(self):
        self.screen.fill(BG)
        title = self.big_font.render("MAZE RUNNER", True, WALL_COLOR)
        prompt = self.font.render("Choose a difficulty", True, WALL_COLOR)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 190))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 245))

        mouse_pos = pygame.mouse.get_pos()
        for difficulty, button in self.difficulty_buttons.items():
            hovered = button.collidepoint(mouse_pos)
            color = (60, 120, 220) if hovered else (30, 30, 50)
            pygame.draw.rect(self.screen, color, button, border_radius=6)
            cols, rows = DIFFICULTIES[difficulty]
            label = self.font.render(
                f"{difficulty}  {cols} x {rows}", True, (245, 245, 240)
            )
            self.screen.blit(
                label,
                (button.centerx - label.get_width() // 2,
                 button.centery - label.get_height() // 2),
            )

    def draw_game(self):
        self.screen.fill(BG)
        if self.show_path:
            path_square = pygame.Surface(
                (self.cell_size, self.cell_size), pygame.SRCALPHA
            )
            path_square.fill((30, 170, 220, 90))
            for r, c in self.path:
                self.screen.blit(
                    path_square,
                    (
                        self.maze_origin[0] + c * self.cell_size,
                        self.maze_origin[1] + r * self.cell_size,
                    ),
                )
        self.draw_maze()
        pygame.draw.rect(self.screen, EXIT_COLOR, self.exit_rect, border_radius=4)
        exit_font = pygame.font.SysFont(
            "monospace", max(10, self.cell_size // 4), bold=True
        )
        ex_label = exit_font.render("EXIT", True, (20,80,20))
        self.screen.blit(
            ex_label,
            (self.exit_rect.centerx - ex_label.get_width() // 2,
             self.exit_rect.centery - ex_label.get_height() // 2),
        )
        self.player.draw(self.screen)

        fog = pygame.Surface(
            (self.maze_width, self.maze_height), pygame.SRCALPHA
        )
        fog.fill((0, 0, 0, 255))
        player_center = (
            self.player.rect.centerx - self.maze_origin[0],
            self.player.rect.centery - self.maze_origin[1],
        )
        pygame.draw.circle(
            fog, (0, 0, 0, 0), player_center, 3 * self.cell_size
        )
        self.screen.blit(fog, self.maze_origin)

        hud = pygame.Rect(0, BOARD_HEIGHT, WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, (30,30,50), hud)
        time_surf = self.font.render(
            f"Time: {self.elapsed:.1f}s   {self.difficulty}   R: New Maze   H: Hint",
            True,
            (200,200,200),
        )
        self.screen.blit(time_surf, (10, BOARD_HEIGHT + 18))

        if self.won:
            overlay = pygame.Surface((WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            self.screen.blit(overlay, (0,0))
            msg = self.big_font.render(f"Solved in {self.elapsed:.1f}s!", True, (80,240,80))
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, BOARD_HEIGHT//2 - 150))
            heading = self.font.render("BEST TIMES", True, (200,200,200))
            self.screen.blit(heading, (WIDTH//2 - heading.get_width()//2, BOARD_HEIGHT//2 - 95))
            for index, score in enumerate(self.leaderboard):
                rank = index + 1
                color = (80,240,80) if rank == self.new_time_rank else (220,220,220)
                label = f"{rank}. {score:.3f}s"
                if rank == self.new_time_rank:
                    label += "  NEW"
                entry = self.font.render(label, True, color)
                y = BOARD_HEIGHT//2 - 55 + index*32
                self.screen.blit(entry, (WIDTH//2 - entry.get_width()//2, y))
            sub = self.font.render("Press R for a new maze", True, (200,200,200))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, BOARD_HEIGHT//2 + 145))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
