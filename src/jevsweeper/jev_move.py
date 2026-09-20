from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Noul, TypeSafeClient

from jevsweeper.board import Board

GAME_RULES = (
    "Minesweeper. A digit is the count of mines in the 8 adjacent cells. "
    "'.' is hidden, 'F' is flagged, ' ' is revealed empty."
)


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    noul: float
    reason: str


def opening_move(board: Board) -> Move:
    return Move(row=board.rows // 2, col=board.cols // 2, noul=1.0, reason="opening")


def next_click(board: Board, mines: int | None = None, *, client: TypeSafeClient | None = None) -> Move:
    """Return the next square to left-click from a board state."""
    mine_count = mines if mines is not None else board.mines
    if board.status() != "playing":
        raise ValueError(f"game is already {board.status()}")
    if board.is_opening() or not board.candidate_cells():
        return opening_move(board)

    candidates = board.candidate_cells()
    state = {
        "game": GAME_RULES,
        "mines": mine_count,
        "rows": board.rows,
        "cols": board.cols,
        "board": board.to_text(),
    }
    questions = {
        f"r{row}c{col}": Noul(
            instructions={
                "question": (
                    "Given `board` and Minesweeper adjacency rules, "
                    "is the hidden cell at `cell` safe to left-click (not a mine)?"
                ),
                "cell": f"row {row}, col {col} (0-based)",
            },
            criteria={
                "true": "Numbers already on the board force this cell to be empty.",
                "false": "The numbers are consistent with this cell being a mine, or it is a pure guess.",
            },
        )
        for row, col in candidates
    }

    owns_client = client is None
    if client is None:
        client = TypeSafeClient()
    try:
        response = client.system_one(state=state, questions=questions)
    finally:
        if owns_client:
            client.close()

    best: Move | None = None
    for row, col in candidates:
        noul = float(response.nouls[f"r{row}c{col}"].noul)
        if best is None or noul > best.noul:
            best = Move(row=row, col=col, noul=noul, reason="jev")
    if best is None:
        raise RuntimeError("Jev returned no cell scores")
    return best
