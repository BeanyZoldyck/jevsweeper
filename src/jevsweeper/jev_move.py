from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Noul, TypeSafeClient

from jevsweeper.board import Board
from jevsweeper.client import make_client

GAME_RULES = (
    "Minesweeper. A digit is the count of mines in the 8 adjacent cells. "
    "'.' is hidden, 'F' is flagged, ' ' is revealed empty. "
    "Never left-click a cell that must be a mine; those should be flagged."
)
CLICK_THRESHOLD = 0.75
FLAG_THRESHOLD = 0.75


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    noul: float
    reason: str
    action: str = "click"
    safe_noul: float | None = None
    mine_noul: float | None = None


def opening_move(board: Board) -> Move:
    return Move(row=board.rows // 2, col=board.cols // 2, noul=1.0, reason="opening", action="click")


def _forced_move(board: Board) -> Move | None:
    mines, safes = board.deduce()
    if safes:
        row, col = sorted(safes)[0]
        return Move(row=row, col=col, noul=1.0, reason="forced", action="click", safe_noul=1.0, mine_noul=0.0)
    if mines:
        row, col = sorted(mines)[0]
        return Move(row=row, col=col, noul=1.0, reason="forced", action="flag", safe_noul=0.0, mine_noul=1.0)
    return None


def _pick_jev_move(candidates: list[tuple[int, int]], response) -> Move:
    scored: list[Move] = []
    for row, col in candidates:
        safe = float(response.nouls[f"safe_r{row}c{col}"].noul)
        mine = float(response.nouls[f"mine_r{row}c{col}"].noul)
        scored.append(
            Move(
                row=row,
                col=col,
                noul=max(safe, mine),
                reason="jev",
                action="click" if safe > mine else "flag",
                safe_noul=safe,
                mine_noul=mine,
            )
        )

    flags = [move for move in scored if move.mine_noul is not None and move.safe_noul is not None and move.mine_noul > move.safe_noul]
    clicks = [move for move in scored if move.safe_noul is not None and move.mine_noul is not None and move.safe_noul > move.mine_noul]
    best_flag = max(flags, key=lambda move: move.mine_noul or 0.0, default=None)
    best_click = max(clicks, key=lambda move: move.safe_noul or 0.0, default=None)

    if best_flag is not None and (best_flag.mine_noul or 0) >= FLAG_THRESHOLD:
        return best_flag
    if best_click is not None and (best_click.safe_noul or 0) >= CLICK_THRESHOLD:
        return best_click
    if best_flag is not None and best_click is not None:
        flag_margin = (best_flag.mine_noul or 0) - (best_flag.safe_noul or 0)
        click_margin = (best_click.safe_noul or 0) - (best_click.mine_noul or 0)
        return best_flag if flag_margin >= click_margin else best_click
    if best_flag is not None:
        return best_flag
    if best_click is not None:
        return best_click
    # Every cell is a coin flip. Flag the most mine-like instead of left-clicking.
    fallback = max(scored, key=lambda move: move.mine_noul or 0.0)
    return Move(
        row=fallback.row,
        col=fallback.col,
        noul=fallback.mine_noul or 0.0,
        reason="jev",
        action="flag",
        safe_noul=fallback.safe_noul,
        mine_noul=fallback.mine_noul,
    )


def next_move(
    board: Board,
    mines: int | None = None,
    *,
    client: TypeSafeClient | None = None,
    backend: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> Move:
    """Return the next square to click or flag from a board state."""
    mine_count = mines if mines is not None else board.mines
    if board.status() != "playing":
        raise ValueError(f"game is already {board.status()}")
    if board.is_opening() or not board.candidate_cells():
        return opening_move(board)

    forced = _forced_move(board)
    if forced is not None:
        return forced

    candidates = board.candidate_cells()
    state = {
        "game": GAME_RULES,
        "mines": mine_count,
        "rows": board.rows,
        "cols": board.cols,
        "board": board.to_text(),
    }
    questions = {}
    for row, col in candidates:
        cell = f"row {row}, col {col} (0-based)"
        questions[f"safe_r{row}c{col}"] = Noul(
            instructions={
                "question": (
                    "Given `board` and Minesweeper adjacency rules, "
                    "is the hidden cell at `cell` safe to left-click (not a mine)?"
                ),
                "cell": cell,
            },
            criteria={
                "true": "The numbers force this cell to be empty.",
                "false": "This cell could be a mine, or the numbers force it to be a mine.",
            },
        )
        questions[f"mine_r{row}c{col}"] = Noul(
            instructions={
                "question": (
                    "Given `board` and Minesweeper adjacency rules, "
                    "is the hidden cell at `cell` a mine that should be right-click flagged?"
                ),
                "cell": cell,
            },
            criteria={
                "true": "The numbers force this cell to be a mine, or it is very likely a mine.",
                "false": "This cell is empty or too uncertain to flag.",
            },
        )

    owns_client = client is None
    if client is None:
        client = make_client(backend=backend, base_url=base_url, model=model)
    try:
        response = client.system_one(state=state, questions=questions)
    finally:
        if owns_client:
            client.close()

    return _pick_jev_move(candidates, response)


def next_click(
    board: Board,
    mines: int | None = None,
    *,
    client: TypeSafeClient | None = None,
    backend: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> Move:
    return next_move(board, mines, client=client, backend=backend, base_url=base_url, model=model)


def format_move(move: Move) -> str:
    extra = ""
    if move.safe_noul is not None and move.mine_noul is not None:
        extra = f" safe={move.safe_noul:.3f} mine={move.mine_noul:.3f}"
    return f"{move.action.upper()} r{move.row} c{move.col} noul={move.noul:.3f}{extra} ({move.reason})"
