# DEVLOG — Demoscene: The Exploration of Art
# A Cellfish Production

Format: newest entry at the top.
Update this file at the end of every session before closing the chat.

---

## 2026-03-17  —  Session 5

### Goal
Restore all action handlers stripped in sessions 3-4. Fix HQ menu being
wiped by result zone redraws. Set up GitHub workflow.

### Files changed
- `game.py` — restored all missing action handlers
- `ansi.py` — restored all missing screen builders and animation primitives,
  fixed screen_hq zone conflict

### GitHub setup completed this session
- Created repo at https://github.com/dextercf/demoscene
- Installed Git on Windows 11 VM
- GitHub connector connected to Claude
- Workflow: download outputs -> copy to C:\demoscene\ -> git add/commit/push
- Key recovery command if repo broken: git clone https://github.com/dextercf/demoscene.git
- Key sync command: git pull --rebase

### Bugs fixed
- All action handlers (B, P, R, D, M, S) stripped in sessions 3-4.
  hq_loop only accepted E, T, Q.
  Fix: restored action_trade, action_produce, action_raid, action_defend,
  action_messages, action_hof, action_party, end_day, _random_event,
  _generate_messages, _new_game, _exit_cleanly, _ordinal.
  hq_loop now accepts ETPRDBMSQetpRdbmsq.

- All screen builders stripped from ansi.py in sessions 3-4.
  screen_trade, screen_produce, screen_raid, screen_messages, screen_hof,
  screen_party, screen_game_over, dots, progress_bar, spinner, typewriter,
  combat_bar, animate_combat_bars all missing.
  Fix: appended all back to ansi.py.

- HQ menu drawn at rows 19-21 — inside result zone (rows 14-22).
  Every call to result() redraws rows 14-22, wiping the menu.
  B, P, R, D, M, S appeared not to work because their labels were erased
  immediately after being drawn.
  Fix: screen_hq now draws menu at rows 10-12 (MENU_TOP..MENU_BOT),
  above DIV_3 (row 13), completely safe from result() redraws.

- SyncTerm disconnect on door exit.
  io.close() was never called in main(). Python GC closed socket hard.
  Fix: main() calls io.close() which calls sock.setblocking(True) then
  sock.detach() — releases fd without closing the OS socket.

### What was NOT done (defer to next session)
- Map pagination needs testing now that all actions work
- screen_messages() and screen_hof() need player passed for status bar
- Counter-raid response in end_day() (flag set, nothing acts on it)
- Courier mission system
- Crew management screen
- combat.py render_result() still unused

### Resume here next session
All 9 HQ menu keys should now work. Test the full game flow first,
then pick from the deferred list above.
Recommended next: test thoroughly, then courier missions or crew management.

---

## 2026-03-17  —  Session 4

### Goal
Stabilize I/O layer for Mystic BBS compatibility, resolve silent hang
on connection, prepare for crew management.

### Files changed
- `socketio.py` — removed aggressive Telnet negotiation, passive I/O model
- `ansi.py` — hardened _truncate_ansi, added row 23/24 layout guards
- `game.py` — refactored title_loop and main(), merged trade logic
  NOTE: this session accidentally stripped most action handlers and screen
  builders — fixed in session 5.
- `readme.txt` — updated technical requirements and installation steps

### Bugs fixed
- Aggressive Telnet handshakes caused socket drops on some Mystic configs.
  Fix: passive I/O model, no IAC negotiation on connect.
- ANSI truncation bug causing raw escape code bytes visible as "<90".
  Fix: truncate on visible character width not raw byte length.
- Two conflicting action_trade functions merged into one.

---

## 2026-03-16  —  Session 3

### Goal
Stabilize screen layout, implement map pagination, fix chrome/status bar,
refactor HQ and Explore UI flow.

### Files changed
- `ansi.py` — layout adjustments, ANSI truncation, chrome row protection
  NOTE: screen builders stripped — fixed session 5.
- `game.py` — map pagination, HQ redesign, explore screen separation
  NOTE: action handlers stripped — fixed session 5.
- `socketio.py` — input echo handling adjustments

### Architecture changes (kept in later sessions)
- Zone layout: STATUS_DIV=23, STATUS=24. All gameplay on rows 1-22.
- _truncate_ansi() added — truncates on visible width.
- write_at() guards against writing to rows >= STATUS_DIV.
- screen_explore() added as dedicated explore screen.
- Map pagination: 5 nodes per page, [N]ext/[P]rev navigation.

---

## 2026-03-15  —  Session 2

### Goal
Bug fixing pass on ansi.py, wire combat.py into game.py, fix scrolling.

### Files changed
- `ansi.py` — multiple bug fixes
- `game.py` — new_game() rewrite, action_raid() rewrite, end_day() fix,
  combat.py wired in

### Bugs fixed
- CMD_ROW undefined. Fix: added CMD_ROW = 24 constant.
- screen_base() missing cmd_hint param. Fix: added cmd_hint='' param.
- Command hints passed as bbs_name in 5 screen functions. Fix: all corrected.
- ansi.draw_cmd() called but never defined. Fix: replaced with write_at().
- combat.py never used. Fix: action_raid() and end_day() now use it.
- new_game() used writeln() causing scroll. Fix: full rewrite with write_at().
- Map screen input overlapped node list. Fix: reserved bottom 2 rows.

---

## 2026-03-15  —  Session 1

### Goal
Initial build. Create all core game modules from scratch.

### Files created
- `game.py`      Main game loop, all action handlers, NPC message generator
- `ansi.py`      Display engine, screen builders, animations, art loader
- `combat.py`    Raid/combat resolver, tactic system, defence resolver
- `player.py`    Player state, save/load, leaderboard
- `world.py`     Procedural world gen: nodes, NPC crews, party schedule
- `door.py`      DOOR.SYS / DORINFO1.DEF reader, debug fallback
- `socketio.py`  TCP socket I/O for Mystic BBS, DebugIO fallback
- `config.ini`   SysOp configuration file
- `run.bat`      Windows batch launcher for Mystic BBS
- `readme.txt`   Installation and configuration documentation

### Architecture decisions
- 80x24 fixed cursor-placement. Nothing scrolls. Ever.
- All output via socketio.get_io() — never stdout directly.
- Plain INI-style save files in saves/ folder.
- Standard library only — no pip packages.
- cp437 encoding throughout.

---
