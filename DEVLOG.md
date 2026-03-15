# DEVLOG — Demoscene: The Exploration of Art
# A Cellfish Production

Format: newest entry at the top.
Update this file at the end of every session before closing the chat.

---

## 2026-03-15  —  Session 2

### Goal
Bug fixing pass on ansi.py, wire combat.py into game.py, fix display scrolling issues.

### Files changed
- `ansi.py` — multiple bug fixes (see below)
- `game.py` — new_game() rewrite, action_raid() rewrite, end_day() fix, combat.py wired in

### Bugs fixed
- `CMD_ROW` was used in `wait_for_key()` and `screen_game_over()` but never defined.
  Fix: added `CMD_ROW = 24` constant to ansi.py zone block.

- `screen_base()` was missing `cmd_hint` parameter.
  `screen_messages()` and `screen_hof()` both called `screen_base(cmd_info=...)` —
  a kwarg that didn't exist. Would crash with TypeError at runtime.
  Fix: added `cmd_hint=""` param to `screen_base()`. Rendered embedded in DIV_3 divider.

- Command hint strings were passed as positional `bbs_name` arg in 5 screen functions:
  `screen_map`, `screen_trade`, `screen_produce`, `screen_raid`, `screen_party`.
  Status bar was showing the hint string instead of the BBS name.
  Fix: all 5 callers now pass `player.bbs_name` correctly and use `cmd_hint=`.

- `ansi.draw_cmd()` was called in `action_raid()` but never defined in ansi.py.
  Fix: replaced with `ansi.write_at()` to the result zone.

- `combat.py` was never imported or called by `game.py`.
  Duplicate inline combat math lived in `action_raid()` and `end_day()`.
  Fix: `action_raid()` now calls `combat.resolve_raid()` + `combat.apply_raid_result()`.
  `end_day()` now calls `combat.resolve_defence()`.

- `new_game()` used `ansi.writeln()` throughout, causing the screen to scroll during
  world generation instead of drawing in place.
  Fix: rewrote `new_game()` entirely using `write_at()`, `draw_art()`, `draw_divider()`,
  `dots()` at fixed rows. No writeln() calls remain in new_game().

- Map screen input prompt overlapped the node list.
  `action_travel()` wrote "SELECT NODE" prompt to DIV_3 (row 19), inside the node list.
  `get_input()` then printed inline text over nodes.
  Fix: `screen_map()` now reserves rows RES_BOT-1 and RES_BOT for overflow hint and input
  prompt. `action_travel()` positions cursor at end of the pre-drawn prompt on RES_BOT.

### What was NOT done (defer to next session)
- Map pagination (only ~7 nodes visible at once with 20 in world)
- screen_messages() and screen_hof() have blank status bars (no player passed)
- combat.py render_result() is defined but never called
- Counter-raid risk flag set in combat.py but end_day() doesn't act on it
- Courier mission system
- Crew management screen

### Resume here next session
Pick any item from "What was NOT done" above.
Recommended first: map pagination — it's the most visible gameplay gap.

---

## 2026-03-15  —  Session 1

### Goal
Initial build. Create all core game modules from scratch.

### Files created
- `game.py`      Main game loop, all action handlers, NPC message generator
- `ansi.py`      Display engine, all screen builders, animations, art loader
- `combat.py`    Raid/combat resolver, tactic system, defence resolver
- `player.py`    Player state, save/load, leaderboard
- `world.py`     Procedural world gen: nodes, NPC crews, demoparty schedule
- `door.py`      DOOR.SYS / DORINFO1.DEF drop file reader, debug mode
- `socketio.py`  TCP socket I/O layer for Mystic BBS, DebugIO fallback
- `config.ini`   SysOp configuration file
- `run.bat`      Windows batch launcher for Mystic BBS
- `readme.txt`   Installation and configuration documentation

### Architecture decisions made
- 80x24 fixed cursor-placement display. Nothing scrolls. Ever.
- All output routes through socketio.get_io() — never write to stdout directly.
- Save files are plain INI-style text in saves/ folder (one per player handle).
- World state saved separately to saves/HANDLE.world.
- Art packs: optional .ans files in art/ folder; ASCII fallback always available.
- Standard library only — no pip packages required.
- cp437 encoding throughout for BBS terminal compatibility.

### Known issues at end of session (not yet fixed)
- combat.py not wired into game.py (inline duplicate logic used instead)
- Several ansi.py bugs: CMD_ROW undefined, screen_base() missing cmd_hint param,
  command hints passed as bbs_name, draw_cmd() called but not defined
- new_game() uses writeln() causing scroll
- Map screen input overlaps node list

---
