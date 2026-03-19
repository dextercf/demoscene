# DEVLOG — Demoscene: The Exploration of Art
# A Cellfish Production

Format: newest entry at the top.
Update this file at the end of every session before closing the chat.

Raw file links (paste directly into Claude chat to fetch):
  https://raw.githubusercontent.com/dextercf/demoscene/main/ansi.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/game.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/combat.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/door.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/player.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/socketio.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/world.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/config.ini
  https://raw.githubusercontent.com/dextercf/demoscene/main/DEVLOG.md

---

## 2026-03-19  —  Session 8

### Goal
Fix explore double-bar (again), fix blank status bar on messages/hof,
wire counter-raid in end_day, fix scroll on [D] defend, unify status bar.

### Files changed
- `ansi.py` — cursor reset fix, draw_status unified, scroll fixes
- `game.py` — counter-raid wired, screen_messages/hof player arg

### Bugs fixed

- Explore double-bar: added move(1,1) cursor reset at the start of
  animate_scan_bar() and animate_explore_line() before any row moves.
  Root cause: after get_key() returns, terminal cursor position is
  unknown. An explicit move(1,1) resets tracking before row-relative
  moves, ensuring the animation lands on the correct row.
  STATUS: deployed, awaiting test confirmation.

- Blank status bar on [M] Messages and [S] Scores screens.
  screen_messages() and screen_hof() were calling screen_base() without
  passing the player object.
  Fix: both now pass player and player.bbs_name to screen_base().

- Counter-raid flag was set by combat.py but never acted on in end_day().
  Fix: action_raid() stores result.counter_risk on player as
  player.pending_counter_raid. end_day() checks this first — if set,
  a counter-raid is guaranteed using the most aggressive crew available,
  with a warning message shown to the player. Flag always reset after.

- Pressing [D] Defend 3 times caused screen scroll.
  Root cause: draw_status() was padding to exactly SCREEN_W (80) chars,
  writing to col 80 on the last terminal row and triggering scroll.
  Fix: draw_status() now pads to SCREEN_W-1 (79) and parks cursor at
  (1,1) after writing.

- Status bar format inconsistent across screens.
  draw_status() used "CREW x · HANDLE x · TURNS n/10 · DAY n" format.
  Explore screen used "HANDLE: x  CREW: y  TURNS n/10 . DAY n . NODE n".
  Fix: draw_status() rewritten to match explore format exactly.
  _draw_explore_status() now just calls draw_status() — single source
  of truth. screen_explore() also updated to use draw_status().

### Resume here next session
Priority 1: Confirm explore double-bar fix works on BBS.
Priority 2: Map pagination — nodes beyond 7 not all visible in list.
Priority 3: Test all HQ actions end-to-end.

Other tasks queued:
- Courier mission system
- Crew management screen
- screen_messages shows only 3 messages — could show more

---

## 2026-03-19  —  Session 7

### Goal
Fix M and B disconnect on HQ, create commented version of game.py,
continue explore screen double-bar investigation.

### Files changed
- `ansi.py` — restored 14 missing screen functions, scroll fix attempts,
  explore screen row adjustments, CP437 divider fix
- `game.py` — explore screen animation flow fixes
- `game_commented.py` — new file: fully commented copy of game.py

### Bugs fixed
- [M] and [B] caused disconnect — 14 screen functions missing from ansi.py.
  Restored from session 1 original.
- Terminal scroll — col 80 last-row write triggers scroll. Mitigated.
- draw_divider() wrong chars over cp437. Fixed with raw b"\xc4" bytes.

### Explore double-bar — still unresolved at end of session 7
Cursor drift during get_key() causes second draw to land one row lower.

---

## 2026-03-18  —  Session 6

### Goal
Fix all HQ menu actions, explore screen layout, SyncTerm disconnect, GitHub.

### Files changed
- `game.py` — restored all action handlers
- `ansi.py` — layout, CP437 fixes
- `run.bat` — fixed GAME_DIR path

### GitHub setup
- Repo: https://github.com/dextercf/demoscene
- Key commands: git pull --rebase / git add / git commit / git push
- Recovery: git clone https://github.com/dextercf/demoscene.git

### Explore screen layout (current spec)
  Row  1-14  Art zone
  Row  15    Divider
  Row  16    [S] Scan network   [Q] Back to HQ
  Row  17    Divider
  Row  18    Network scanner: [bar]  (EXP_SCAN)
  Row  19    Node: <n>               (EXP_NODE)
  Row  20    Info: <description>     (EXP_INFO)
  Rows 21-22 Empty
  Row  23    Divider
  Row  24    Status bar (STATUS row)

---

## 2026-03-17  —  Session 5

### Goal
Bug fixes on ansi.py, wire combat.py, fix scrolling, fix map input.

---

## 2026-03-16  —  Session 4

### Goal
Stabilize I/O, passive socket model, ANSI truncation.
NOTE: accidentally stripped most action handlers — fixed in session 6.

---

## 2026-03-16  —  Session 3

### Goal
Layout stabilization, map pagination, explore screen separation.
NOTE: stripped screen builders from ansi.py — fixed in sessions 6/7.

---

## 2026-03-15  —  Session 2

### Goal
Bug fixes, combat.py wiring, new_game scroll fix, map input fix.

---

## 2026-03-15  —  Session 1

### Goal
Initial build. All core modules created from scratch.

### Files created
game.py, ansi.py, combat.py, player.py, world.py, door.py,
socketio.py, config.ini, run.bat, readme.txt

### Architecture decisions
- 80x25 fixed cursor-placement. Nothing scrolls. Ever.
- All output via socketio.get_io() — never stdout directly.
- Plain INI save files in saves/ folder.
- Standard library only — no pip packages.
- cp437 encoding throughout.

---
