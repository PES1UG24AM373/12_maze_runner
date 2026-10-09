import random
from collections import deque

CELL = 40  # cell size in pixels

def generate_maze(cols, rows):
    """Recursive backtracker maze generation. Returns 2D grid of walls."""
    visited = [[False]*cols for _ in range(rows)]
    # walls: each cell has [N, S, E, W]
    walls = [[[True,True,True,True] for _ in range(cols)] for _ in range(rows)]
    
    def neighbors(r, c):
        dirs = [(-1,0,0,1),(1,0,1,0),(0,1,2,3),(0,-1,3,2)]  # dr,dc,wall_dir,opp_dir
        result = []
        for dr,dc,wd,od in dirs:
            nr,nc = r+dr,c+dc
            if 0<=nr<rows and 0<=nc<cols and not visited[nr][nc]:
                result.append((nr,nc,wd,od))
        return result

    stack = [(0,0)]
    visited[0][0] = True
    while stack:
        r,c = stack[-1]
        nbrs = neighbors(r,c)
        if nbrs:
            nr,nc,wd,od = random.choice(nbrs)
            walls[r][c][wd] = False
            walls[nr][nc][od] = False
            visited[nr][nc] = True
            stack.append((nr,nc))
        else:
            stack.pop()
    return walls

def find_shortest_path(walls, start, goal):
    rows = len(walls)
    cols = len(walls[0]) if rows else 0
    if not rows or not cols:
        return []
    if any(not (0 <= r < rows and 0 <= c < cols) for r, c in (start, goal)):
        return []

    directions = [(-1, 0, 0), (1, 0, 1), (0, 1, 2), (0, -1, 3)]
    previous = {start: None}
    queue = deque([start])

    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            break

        for dr, dc, wall_dir in directions:
            nr, nc = r + dr, c + dc
            neighbor = (nr, nc)
            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and not walls[r][c][wall_dir]
                and neighbor not in previous
            ):
                previous[neighbor] = (r, c)
                queue.append(neighbor)

    if goal not in previous:
        return []

    path = []
    cell = goal
    while cell is not None:
        path.append(cell)
        cell = previous[cell]
    return list(reversed(path))

def cell_rect(r, c, import_pygame=None):
    import pygame
    return pygame.Rect(c*CELL, r*CELL, CELL, CELL)
