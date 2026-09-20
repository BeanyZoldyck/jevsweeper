# jevsweeper

Play Windows XP Minesweeper by sending the live board to [TypeSafe Jev](https://docs.typesafe.ai/introduction) and clicking the safest square.

Jev is a System One model: you pass a `state` and typed questions, and you get probabilities back. Code first flags or clicks cells that Minesweeper numbers already force (100% mine or 100% safe). Remaining frontier cells get two Nouls each — “safe to left-click?” and “is this a mine?” — then the bot left-clicks safes and right-clicks flags. Uncertain cells are flagged rather than clicked if the mine score is higher.

## Setup

Python 3.10+ on Windows. Get an API key from the [TypeSafe dashboard](https://docs.typesafe.ai/introduction/quickstart).

```powershell
cd C:\Users\chuka\Documents\GitHub\jevsweeper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
```

Put your key in `.env`:

```
TYPESAFE_API_KEY=...
```

Default Minesweeper path:

`C:\Users\chuka\Documents\GitHub\ofdl\Minesweeper-Windows-XP\WINMINE.EXE`

Keep the Minesweeper window visible (not minimized).

## Run

Play until win, loss, or a stuck board:

```powershell
python -m jevsweeper
python -m jevsweeper --exe "C:\Users\chuka\Documents\GitHub\ofdl\Minesweeper-Windows-XP\WINMINE.EXE"
```

Print the next square from the current window and move the mouse there without clicking:

```powershell
python -m jevsweeper --once
```

## Library

```python
from typesafe_sdk import TypeSafeClient
from jevsweeper.board import Board
from jevsweeper.jev_move import next_move

board = Board.from_text(
    ".....\n.111.\n.1 1.\n.111.\n.....",
    mines=10,
)
with TypeSafeClient() as client:
    move = next_move(board, client=client)
print(move.action, move.row, move.col, move.noul)
```

Opening boards (nothing revealed yet) click the center tile in code and skip Jev.

## Layout

| Module | Role |
| --- | --- |
| `board.py` | Grid, frontier cells, win/loss |
| `jev_move.py` | `next_click()` — one TypeSafe call, argmax Noul |
| `vision.py` | Capture the XP window and classify 16×16 tiles |
| `clicker.py` | Client-area left click |
| `loop.py` | Launch or attach `WINMINE.EXE` and play |
