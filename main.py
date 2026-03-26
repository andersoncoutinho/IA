import math
import random
from collections import deque
from game2dboard import Board

# ─────────────────────────────────────────────
#  CONFIGURAÇÕES
# ─────────────────────────────────────────────
GRID_ROWS     = 20
GRID_COLS     = 20
MINIMAX_DEPTH = 2      # profundidade da busca Minimax
TIMER_MS      = 50    # ms entre cada meio-turno
MAX_TURNS     = 800     # limite de turnos antes de empate
HISTORY_SIZE  = 5      # quantos estados recentes guardar para anti-loop
LOOP_PENALTY  = 10    # penalidade por revisitar posição recente

# Valores das células (exibidos como texto no tabuleiro)
EMPTY    = None
WALL     = "wall.png"
FUGITIVE = "pacman.png"
PURSUER  = "perseguidor.png"
GOAL     = "portal.png"

FUGITIVE_CELL = (0, 0)
PURSUER_CELL  = (GRID_ROWS-1, GRID_COLS-1)

def generate_random_goal():
    forbidden = {FUGITIVE_CELL, PURSUER_CELL}

    # todas as células do grid
    all_cells = [
        (r, c)
        for r in range(GRID_ROWS)
        for c in range(GRID_COLS)
        if (r, c) not in forbidden
    ]

    # sorteia posições sem repetição
    return random.choice(all_cells)

WALLS = generate_random_goal()
GOAL_CELL = generate_random_goal()

# Movimentos: (Δrow, Δcol)
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Obstáculos
NUM_WALLS = 100
def generate_random_walls():
    forbidden = {FUGITIVE_CELL, PURSUER_CELL, GOAL_CELL}

    # todas as células do grid
    all_cells = [
        (r, c)
        for r in range(GRID_ROWS)
        for c in range(GRID_COLS)
        if (r, c) not in forbidden
    ]

    # sorteia posições sem repetição
    walls = set(random.sample(all_cells, NUM_WALLS))

    return walls
WALLS = generate_random_walls()


# ─────────────────────────────────────────────
#  ESTADO DO JOGO
# ─────────────────────────────────────────────
class GameState:
    def __init__(self, walls, fugitive, pursuer, goal):
        self.walls    = walls
        self.fugitive = fugitive   # (row, col)
        self.pursuer  = pursuer    # (row, col)
        self.goal     = goal       # (row, col)

    def clone(self):
        return GameState(self.walls, self.fugitive, self.pursuer, self.goal)

    def is_free(self, r, c):
        return (0 <= r < GRID_ROWS and
                0 <= c < GRID_COLS and
                (r, c) not in self.walls)

    def get_moves(self, pos):
        r, c = pos
        return [(r+dr, c+dc) for dr, dc in MOVES if self.is_free(r+dr, c+dc)]

    def fugitive_captured(self):
        return self.fugitive == self.pursuer

    def fugitive_escaped(self):
        return self.fugitive == self.goal

    def is_terminal(self):
        return self.fugitive_captured() or self.fugitive_escaped()


# ─────────────────────────────────────────────
#  HEURÍSTICA
# ─────────────────────────────────────────────
def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])
from collections import deque

def bfs_distance(start, goal, walls):
    queue = deque([(start, 0)])
    visited = {start}

    while queue:
        (r, c), d = queue.popleft()

        if (r, c) == goal:
            return d

        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if (0 <= nr < GRID_ROWS and
                0 <= nc < GRID_COLS and
                (nr, nc) not in walls and
                (nr, nc) not in visited):

                visited.add((nr, nc))
                queue.append(((nr, nc), d + 1))

    return math.inf


def evaluate(state: GameState,
             fugitive_history: deque = None,
             pursuer_history:  deque = None) -> float:
    if state.fugitive_captured():
        return -100000.0
    if state.fugitive_escaped():
        return +100000.0
    dist_pf = bfs_distance(state.pursuer,  state.fugitive, state.walls)
    dist_fg = bfs_distance(state.fugitive, state.goal, state.walls)
    score = 2.9 * dist_pf - 3.0 * dist_fg

    # Penaliza revisitar posições recentes (quebra loops)
    if fugitive_history and state.fugitive in fugitive_history:
        score -= LOOP_PENALTY
    if pursuer_history and state.pursuer in pursuer_history:
        score += LOOP_PENALTY   # para o Perseguidor, revisitar é ruim (MIN)

    return score


# ─────────────────────────────────────────────
#  MINIMAX COM PODA ALPHA-BETA
# ─────────────────────────────────────────────
def minimax(state, depth, is_maximizing,
            alpha=-math.inf, beta=math.inf,
            fugitive_history=None, pursuer_history=None):
    if depth == 0 or state.is_terminal():
        return evaluate(state, fugitive_history, pursuer_history)

    if is_maximizing:
        best = -math.inf
        for nxt in state.get_moves(state.fugitive):
            child = state.clone()
            child.fugitive = nxt
            val = minimax(child, depth-1, False, alpha, beta,
                          fugitive_history, pursuer_history)
            if fugitive_history and nxt in fugitive_history:
                val -= LOOP_PENALTY
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for nxt in state.get_moves(state.pursuer):
            child = state.clone()
            child.pursuer = nxt
            val = minimax(child, depth-1, True, alpha, beta,
                          fugitive_history, pursuer_history)
            best = min(best, val)
            beta = min(beta, best)
            if pursuer_history and nxt in pursuer_history:
                val += LOOP_PENALTY
            if beta <= alpha:
                break
        return best


# ─────────────────────────────────────────────
#  AGENTES
# ─────────────────────────────────────────────
class FugitiveAgent:
    def __init__(self):
        self.history = deque(maxlen=HISTORY_SIZE)  # posições recentes

    def choose_move(self, state):
        scored = []
        for nxt in state.get_moves(state.fugitive):
            child = state.clone()
            child.fugitive = nxt
            val = minimax(child, MINIMAX_DEPTH-1, False,
                          fugitive_history=self.history,
                          pursuer_history=None)
            scored.append((val, nxt))

        if not scored:
            return state.fugitive

        # Desempate aleatório: sorteia entre todos os movimentos com score máximo
        best_val = max(v for v, _ in scored)
        best_moves = [pos for v, pos in scored if v == best_val]
        chosen = random.choice(best_moves)

        self.history.append(chosen)
        return chosen

class PursuerAgent:
    def __init__(self):
        self.history = deque(maxlen=HISTORY_SIZE)

    def choose_move(self, state):
        scored = []
        for nxt in state.get_moves(state.pursuer):
            child = state.clone()
            child.pursuer = nxt
            val = minimax(child, MINIMAX_DEPTH-1, True,
                          fugitive_history=None,
                          pursuer_history=self.history)
            scored.append((val, nxt))

        if not scored:
            return state.pursuer

        # Desempate aleatório: sorteia entre todos os movimentos com score mínimo
        best_val = min(v for v, _ in scored)
        best_moves = [pos for v, pos in scored if v == best_val]
        chosen = random.choice(best_moves)

        self.history.append(chosen)
        return chosen


# ─────────────────────────────────────────────
#  JOGO COM game2dboard
# ─────────────────────────────────────────────
class ChaseGame:
    def __init__(self):
        self.board = Board(GRID_ROWS, GRID_COLS)

        # Propriedades globais do Board (API real do game2dboard)
        self.board.title        = "Jogo de Perseguição  |  F=Fugitivo(MAX)  P=Perseguidor(MIN)  G=Objetivo"
        self.board.cell_size    =40
        self.board.cell_color   = "lightyellow"
        self.board.margin_color = "slategray"
        self.board.grid_color   = "slategray"

        # Estado lógico
        self.state = GameState(
            walls    = WALLS,
            fugitive = FUGITIVE_CELL,
            pursuer  = PURSUER_CELL,
            goal     = GOAL_CELL,
        )
        self.fugitive_agent = FugitiveAgent()
        self.pursuer_agent  = PursuerAgent()
        self.turn           = 0
        self.turn_phase     = "fugitive"
        self.game_over      = False

        # Callbacks
        self.board.on_start = self._on_start
        self.board.on_timer = self._on_timer

    def _on_start(self):
        self._redraw_all()
        self.board.start_timer(TIMER_MS)

    def _on_timer(self):
        if self.game_over:
            return

        if self.turn_phase == "fugitive":
            n_moves = random.randint(1, 2)
            for step in range(n_moves):
                self.turn += 1
                prev = self.state.fugitive
                self.state.fugitive = self.fugitive_agent.choose_move(self.state)
                self._move_piece(prev, self.state.fugitive, FUGITIVE)
                self.board.title = (
                    f"Turno {self.turn}  |  "
                    f"Fugitivo {prev} → {self.state.fugitive}  |  "
                    f"Score: {evaluate(self.state, self.fugitive_agent.history, self.pursuer_agent.history):+.1f}"
                )
                if self._check_end():
                    return
                self.turn_phase = "pursuer"

        else:
            n_moves = random.randint(1, 2)
            for step in range(n_moves):
                prev = self.state.pursuer
                self.state.pursuer = self.pursuer_agent.choose_move(self.state)
                self._move_piece(prev, self.state.pursuer, PURSUER)
                self.board.title = (
                    f"Turno {self.turn}  |  "
                    f"Perseguidor {prev} → {self.state.pursuer}  |  "
                    f"Score: {evaluate(self.state, self.fugitive_agent.history, self.pursuer_agent.history):+.1f}"
                )
                if self._check_end():
                    return
                self.turn_phase = "fugitive"

                if self.turn >= MAX_TURNS:
                    self._finish("TEMPO ESGOTADO — EMPATE!")

    def _check_end(self):
        if self.state.fugitive_captured():
            self._finish("PERSEGUIDOR CAPTUROU O FUGITIVO!")
            return True
        if self.state.fugitive_escaped():
            self._finish("FUGITIVO ALCANCOU O OBJETIVO!")
            return True
        return False

    def _finish(self, msg):
        self.game_over = True
        self.board.title = f"{msg}  (Turnos: {self.turn}  |  Profundidade: {MINIMAX_DEPTH})"
        self._redraw_all()

    def _cell_value(self, r, c):
        """Retorna o valor correto para (r, c) dado o estado atual."""
        if (r, c) == self.state.goal:
            return GOAL
        if (r, c) in self.state.walls:
            return WALL
        if (r, c) == self.state.pursuer:
            return PURSUER
        if (r, c) == self.state.fugitive:
            return FUGITIVE
        return EMPTY

    def _redraw_all(self):
        """Redesenha o tabuleiro inteiro."""
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                self.board[r][c] = self._cell_value(r, c)

    def _move_piece(self, old_pos, new_pos, piece):
        """Move uma peça: restaura célula antiga e escreve na nova."""
        old_r, old_c = old_pos
        # Restaura a célula antiga (pode ser GOAL ou EMPTY)
        self.board[old_r][old_c] = self._cell_value(old_r, old_c)
        # Escreve na nova posição
        new_r, new_c = new_pos
        self.board[new_r][new_c] = piece

    def run(self):
        self.board.show()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    game = ChaseGame()
    game.run()