# jevsweeper

Play Windows XP Minesweeper by sending the live board to a [local-jev](https://github.com/amithgc/local-jev) server and clicking the safest square.

local-jev is an offline System One server with the same `/v1/systemone` wire format as TypeSafe Jev. This bot keeps using `typesafe-sdk` and points it at `http://127.0.0.1:8765` by default. Code first flags or clicks cells that Minesweeper numbers already force (100% mine or 100% safe). Remaining frontier cells get two Nouls each — “safe to left-click?” and “is this a mine?” — then the bot left-clicks safes and right-clicks flags. Uncertain cells are flagged rather than clicked if the mine score is higher.

## Setup

Python 3.10+ on Windows. Run [local-jev](https://github.com/amithgc/local-jev) in a separate terminal (WSL2 is what that project documents for Windows):

```sh
git clone https://github.com/amithgc/local-jev && cd local-jev
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
.venv/bin/local-jev serve
```

That prints `api http://127.0.0.1:8765/v1/systemone`. The first start downloads `nli-deberta-large` (~0.87 GB). For the more accurate default:

```sh
.venv/bin/local-jev serve --model llm-qwen3.5-4b
```

Then install this bot:

```powershell
cd C:\Users\chuka\Documents\GitHub\jevsweeper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
```

`.env` already targets local-jev:

```
TYPESAFE_BASE_URL=http://127.0.0.1:8765
TYPESAFE_API_KEY=local
```

`TYPESAFE_API_KEY=local` is required by the SDK; local-jev ignores it unless you set `LOCAL_JEV_API_KEY` on the server.

Default Minesweeper path is `C:\Users\chuka\Documents\Minesweeper-Windows-XP\WINMINE.EXE` (override with `--exe`). Keep the Minesweeper window visible (not minimized).

## Run

Play until win, loss, or a stuck board:

```powershell
python -m jevsweeper
python -m jevsweeper --url http://127.0.0.1:8765 --model llm-qwen3.5-4b
```

Print the next square from the current window and move the mouse there without clicking:

```powershell
python -m jevsweeper --once
```

## Library

```python
from jevsweeper.board import Board
from jevsweeper.client import make_client
from jevsweeper.jev_move import next_move

board = Board.from_text(
    ".....\n.111.\n.1 1.\n.111.\n.....",
    mines=10,
)
with make_client() as client:
    move = next_move(board, client=client)
print(move.action, move.row, move.col, move.noul)
```

Opening boards (nothing revealed yet) click the center tile in code and skip local-jev.

## Layout

| Module | Role |
| --- | --- |
| `board.py` | Grid, frontier cells, win/loss |
| `client.py` | `typesafe-sdk` client aimed at local-jev |
| `jev_move.py` | `next_move()` — one `/v1/systemone` call, then click or flag |
| `vision.py` | Capture the XP window and classify 16×16 tiles |
| `clicker.py` | Client-area left click or right-click flag |
| `loop.py` | Launch or attach `WINMINE.EXE` and play |
