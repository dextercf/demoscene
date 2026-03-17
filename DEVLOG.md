# DEVLOG — Demoscene: The Exploration of Art
# A Cellfish Production

Format: newest entry at the top.
Update this file at the end of every session before closing the chat.

---

## 2026-03-18  —  Session 6

### Goal
Fix all HQ menu actions (B, P, R, D, M, S), fix explore screen layout and
animation, fix SyncTerm disconnect on door exit, set up GitHub workflow.

### Files changed
- `game.py` — restored all action handlers, fixed action_explore animation
- `ansi.py` — multiple fixes, restored 14 missing screen functions
- `run.bat` — fixed GAME_DIR path from C:\games\demoscene to C:\demoscene

### GitHub setup completed this session
- Repo: https://github.com/dextercf/demoscene
- Git installed on Windows 11 VM, GitHub connector connected to Claude
- Key commands: git pull --rebase / git add / git commit -m "" / git push
- If repo broken: git clone https://github.com/dextercf/demoscene.git

### Bugs fixed

- All HQ action handlers (B, P, R, D, M, S) stripped in sessions 3-4.
  hq_loop only accepted E, T, Q. Caused silent no-op on those keys.
  Fix: restored action_trade, action_produce, action_raid, action_defend,
  action_messages, action_hof, action_party, end_day, _random_event etc.
  hq_loop now accepts ETPRDBMSQetpRdbmsq.

- screen_messages, screen_hof, screen_trade, screen_produce, screen_raid,
  screen_party, screen_game_over, dots, spinner, progress_bar, combat_bar,
  animate_combat_bars, wait_for_key all missing from ansi.py.
  Caused AttributeError crash (disconnect) when pressing M, B, S etc.
  Fix: extracted and restored all 14 functions from session 1 original.

- HQ menu drawn at rows 19-21 inside result zone (rows 14-22).
  Every result() call redraws 14-22, wiping the menu.
  Fix: screen_hq() draws menu at MENU_TOP (rows 10-12), above DIV_3.

- SyncTerm disconnects on door exit instead of returning to BBS menu.
  io.close() was never called. Python GC closed socket hard.
  Fix: _exit_cleanly() calls sock.setblocking(True) then sock.detach().

- run.bat GAME_DIR pointed to wrong path after git clone to C:\demoscene.
  Fix: updated GAME_DIR=C:\demoscene.

- draw_divider() used Unicode chr(0x2500) "─" which encodes incorrectly
  in cp437 over Mystic BBS socket — showed as "A" or wrong char.
  Fix: default sends raw b"\xc4" bytes directly.

- ERASE_LINE (\x1b[2K) unreliable over Mystic socket — terminal cursor
  row tracking can drift, causing wrong row to be erased.
  Mitigation: replaced with full 80-char padded line writes where possible.

- Writing to column 80 on the last terminal row (25) triggers scroll.
  Any byte after col 80 causes entire screen to scroll up one line.
  Fix: pad to col 79 max, park cursor at (1,1) after last-row writes.

### Explore screen — new custom layout implemented
  Row  1-15  Art zone (load_art("explorer_menu") or fallback)
  Row  16    Divider
  Row  17    [S] Scan network   [Q] Back to HQ
  Row  18    Divider
  Row  19    Network scanner: [bar]
  Row  20    Node: <n>
  Row  21    Info: <description>
  Rows 22-23 Empty
  Row  24    Divider
  Row  25    Status bar

Constants: EXP_SCAN=19, EXP_NODE=20, EXP_INFO=21, EXP_STATUS=25

New animation functions added to ansi.py:
- animate_scan_bar(): fills bar left to right over ~7-8s with random
  tempo. Bright green leading edge fades to dark green. Node name
  revealed at ~3 seconds via animate_explore_line().
- animate_explore_line(): types text char by char. First 2 letters of
  each word bright green, remaining letters dark green.
- screen_explore() called once on entry — results persist until [Q].

### Known remaining issue — NOT fixed this session
The explore screen shows a double "Network scanner:" bar when [S] pressed.
Investigated causes:
- screen_explore() draws scanner label on init
- animate_scan_bar() redraws it again before animating
- Terminal cursor row tracking drift causes second draw to land on wrong row
Multiple approaches tried without full resolution. Left for next session.

### Resume here next session
RECOMMENDED: Fix explore double-bar.
Approach: have screen_explore() draw scanner labels in idle state only.
animate_scan_bar() should be the only function that draws during animation,
moving cursor precisely to (EXP_SCAN, BAR_COL) without any prior label draw.
Test with ERASE_LINE removed entirely from animation path.

Other tasks queued:
- Map pagination (nodes > 7 still not all visible in list)
- screen_messages() and screen_hof() need player arg for status bar
- Counter-raid response in end_day() (counter_risk flag set, nothing acts)
- Courier mission system
- Crew management screen

---

## 2026-03-17  —  Session 5

### Goal
Bug fixing on ansi.py, wire combat.py into game.py, fix scrolling in
new_game(), fix map screen input overlapping node list.

### Files changed
- `ansi.py` — CMD_ROW defined, screen_base cmd_hint param, 5 screen
  callers fixed, screen_hq zone fix, draw_cmd removed
- `game.py` — action_raid/end_day wired to combat.py, new_game() rewrite,
  map input prompt repositioned

### Bugs fixed
- CMD_ROW undefined in wait_for_key() and screen_game_over().
- screen_base() missing cmd_hint param causing TypeError.
- Command hint strings passed as bbs_name in 5 screen functions.
- ansi.draw_cmd() called but never defined.
- combat.py never wired into game.py — action_raid and end_day now use it.
- new_game() used writeln() causing scroll. Rewritten with write_at().
- Map screen input prompt at DIV_3 overlapped node list.

---

## 2026-03-16  —  Session 4

### Goal
Stabilize I/O layer, resolve silent hang on connection, passive socket model.

### Files changed
- `socketio.py` — removed Telnet negotiation, passive I/O model
- `ansi.py` — _truncate_ansi added, STATUS_DIV/STATUS row guards
- `game.py` — refactored (NOTE: accidentally stripped most action handlers)
- `readme.txt` — updated technical requirements

### Architecture changes kept in later sessions
- Zone layout: STATUS_DIV=23, STATUS=24. All gameplay on rows 1-22.
- _truncate_ansi() — truncates strings on visible char width, not bytes.
- write_at() guards against writing rows >= STATUS_DIV.

---

## 2026-03-16  —  Session 3

### Goal
Screen layout stabilization, map pagination, HQ redesign, explore screen.

### Files changed
- `ansi.py` — layout, ANSI truncation (NOTE: screen builders stripped)
- `game.py` — map pagination, explore screen (NOTE: action handlers stripped)
- `socketio.py` — input echo adjustments

### Architecture changes kept
- screen_explore() added as dedicated explore screen.
- Map pagination: 5 nodes per page, [N]ext/[P]rev navigation.

---

## 2026-03-15  —  Session 2

### Goal
Bug fixing pass on ansi.py, wire combat.py, fix display scrolling.

### Bugs fixed
CMD_ROW undefined, screen_base cmd_hint missing, bbs_name confusion,
draw_cmd not defined, combat.py not wired, new_game scroll, map overlap.

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
