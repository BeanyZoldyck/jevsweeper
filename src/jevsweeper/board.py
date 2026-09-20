from __future__ import annotations

from dataclasses import dataclass

HIDDEN = "."
EMPTY = " "
FLAG = "F"
MINE = "*"
REVEALED_EMPTY = frozenset({EMPTY, "1", "2", "3", "4", "5", "6", "7", "8"})


def default_mine_count(rows: int, cols: int) -> int:
    if (rows, cols) == (9, 9):
        return 10
    if (rows, cols) == (16, 16):
        return 40
    if (rows, cols) in ((16, 30), (30, 16)):
        return 99
    return max(1, round(rows * cols * 0.16))


@dataclass
class Board:
    grid: list[list[str]]
    mines: int | None = None

    def __post_init__(self) -> None:
        if not self.grid:
            raise ValueError("board is empty")
        width = len(self.grid[0])
        if any(len(row) != width for row in self.grid):
            raise ValueError("board rows must be the same length")
        if self.mines is None:
            self.mines = default_mine_count(self.rows, self.cols)

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    @classmethod
    def from_text(cls, text: str, mines: int | None = None) -> Board:
        lines = [list(line) for line in text.strip("\n").splitlines() if line]
        return cls(lines, mines)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        cells: list[tuple[int, int]] = []
        for d_row in (-1, 0, 1):
            for d_col in (-1, 0, 1):
                if d_row == 0 and d_col == 0:
                    continue
                n_row, n_col = row + d_row, col + d_col
                if self.in_bounds(n_row, n_col):
                    cells.append((n_row, n_col))
        return cells

    def at(self, row: int, col: int) -> str:
        return self.grid[row][col]

    def hidden_cells(self) -> list[tuple[int, int]]:
        return [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == HIDDEN
        ]

    def is_opening(self) -> bool:
        return all(cell in {HIDDEN, FLAG} for row in self.grid for cell in row)

    def has_mine(self) -> bool:
        return any(cell == MINE for row in self.grid for cell in row)

    def frontier_cells(self) -> list[tuple[int, int]]:
        cells: list[tuple[int, int]] = []
        for row, col in self.hidden_cells():
            if any(self.at(n_row, n_col) in REVEALED_EMPTY for n_row, n_col in self.neighbors(row, col)):
                cells.append((row, col))
        return cells

    def candidate_cells(self) -> list[tuple[int, int]]:
        frontier = self.frontier_cells()
        if frontier:
            return frontier
        return self.hidden_cells()

    def deduce(self) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """Forced mines and safes from each number's remaining-neighbor count."""
        flags = {
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == FLAG
        }
        hidden = set(self.hidden_cells())
        safes: set[tuple[int, int]] = set()
        progress = True
        while progress:
            progress = False
            for row in range(self.rows):
                for col in range(self.cols):
                    cell = self.grid[row][col]
                    if cell not in "12345678":
                        continue
                    needed = int(cell)
                    neighbors = self.neighbors(row, col)
                    flag_count = sum(1 for pos in neighbors if pos in flags)
                    unknown = [pos for pos in neighbors if pos in hidden and pos not in flags and pos not in safes]
                    remaining = needed - flag_count
                    if remaining < 0 or remaining > len(unknown):
                        continue
                    if remaining == 0 and unknown:
                        safes.update(unknown)
                        progress = True
                    elif remaining == len(unknown) and unknown:
                        flags.update(unknown)
                        hidden.difference_update(unknown)
                        progress = True
        already_flagged = {
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == FLAG
        }
        return flags - already_flagged, safes

    def to_text(self) -> str:
        return "\n".join("".join(row) for row in self.grid)

    def status(self) -> str:
        if self.has_mine():
            return "lost"
        if not self.hidden_cells():
            return "won"
        return "playing"
