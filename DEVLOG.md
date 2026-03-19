# DEVLOG — Demoscene: The Exploration of Art
# A Cellfish Production

Format: newest entry at the top.
Update this file at the end of every session before closing the chat.

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
  explaining every function, parameter, and design decision

### Bugs fixed

- [M] Messages and [B] Trade caused disconnect (AttributeError crash).
  screen_messages, screen_hof, screen_trade, screen_produce, screen_raid,
  screen_party, screen_game_over, dots, spinner, progress_bar, combat_bar,
  animate_combat_bars, wait_for_key were all missing from ansi.py.
  Root cause: when ansi.py was reverted to the uploaded version earlier,
  only the explore functions were re-appended — all other screen builders
  were forgotten.
  Fix: extracted all 14 missing functions from the session 1 original and
  appended them back to ansi.py.

- Terminal scroll: screen bumped upward during explore animation.
  Root cause: writing to column 80 on the last terminal row (row 25)
  with any trailing byte (even a colour reset) triggers scroll.
  Fix: pad all last-row writes to col 79 max, park cursor at (1,1)
  after every write to the bottom of the screen.

- draw_divider() used Unicode "─" (U+2500) which encodes incorrectly
  over Mystic BBS cp437 socket — showed as "A" or similar garbage.
  Fix: changed to send raw b"\xc4" bytes by default.

### Explore double-bar — status (NOT fully fixed)
Still investigating. The two visible "Network scanner:" lines are caused
by screen_explore() drawing the scanner label on screen init, and then
animate_scan_bar() drawing it again when [S] is pressed. Both should
land on the same row (EXP_SCAN=19) but terminal cursor tracking drift
over the socket causes the second draw to land one row lower.

Approaches tried this session:
- Removed ERASE_LINE from animation path entirely
- Used full 80-char padded line writes instead
- Moved zone-reset logic fully inside animate_scan_bar()
- Removed _draw_exp_labels() call from game.py

None fully resolved. Root cause is cursor position drift during the
blocking get_key() wait between screen draw and scan trigger.

### Resume here next session
Priority 1: Explore double-bar.
Fresh approach to try: Have screen_explore() draw nothing in the scanner
zone at all. Only draw the [S]/[Q] menu. Let animate_scan_bar() be the
SOLE function responsible for drawing rows 19-21. This way there is
zero possibility of a prior draw conflicting.

Priority 2: Test all other HQ actions (T, P, R, D, M, S) now that
screen functions are restored.

Other tasks queued:
- Map pagination (>7 nodes not all visible)
- screen_messages/screen_hof need player arg for status bar
- Counter-raid response in end_day() (flag set, nothing acts on it)
- Courier mission system
- Crew management screen

---

## 2026-03-18  —  Session 6

### Goal
Fix all HQ menu actions (B, P, R, D, M, S), fix explore screen layout
and animation, fix SyncTerm disconnect on door exit, set up GitHub.

### Files changed
- `game.py` — restored all action handlers, fixed action_explore flow
- `ansi.py` — multiple fixes, layout adjustments
- `run.bat` — fixed GAME_DIR path

### GitHub setup completed
- Repo: https://github.com/dextercf/demoscene
- Git on VM, GitHub connector connected to Claude
- Key commands: git pull --rebase / git add / git commit / git push
- Recovery: git clone https://github.com/dextercf/demoscene.git

### Bugs fixed
- All HQ action handlers stripped in sessions 3-4. Restored.
- HQ menu drawn inside result zone — wiped on every action. Fixed.
- SyncTerm disconnect on door exit. Fixed with sock.detach().
- run.bat wrong path. Fixed.
- draw_divider() wrong chars over cp437. Fixed.
- ERASE_LINE unreliable over Mystic socket. Mitigated.
- Col 80 last-row scroll trigger. Mitigated.

### Explore screen layout (current spec)
  Row  1-15  Art zone
  Row  16    Divider
  Row  17    [S] Scan network   [Q] Back to HQ
  Row  18    Divider
  Row  19    Network scanner: [bar]  (EXP_SCAN)
  Row  20    Node: <n>               (EXP_NODE)
  Row  21    Info: <description>     (EXP_INFO)
  Rows 22-23 Empty
  Row  24    Divider
  Row  25    Status bar

---

## 2026-03-17  —  Session 5

### Goal
Bug fixes on ansi.py, wire combat.py, fix scrolling, fix map input.

### Bugs fixed
CMD_ROW undefined, screen_base cmd_hint missing, bbs_name confusion,
draw_cmd not defined, combat.py not wired, new_game scroll, map overlap.

---

## 2026-03-16  —  Session 4

### Goal
Stabilize I/O, passive socket model, ANSI truncation.

### Architecture changes kept
STATUS_DIV=23, STATUS=24. _truncate_ansi(). write_at() row guards.
NOTE: session accidentally stripped most action handlers — fixed s6.

---

## 2026-03-16  —  Session 3

### Goal
Layout stabilization, map pagination, explore screen separation.

### Architecture changes kept
screen_explore() as dedicated screen. Map pagination 5 nodes/page.
NOTE: session stripped screen builders from ansi.py — fixed s6/s7.

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
