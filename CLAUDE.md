# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Demoscene: The Exploration of Art** is a Python BBS door game for Mystic BBS on Windows. Players manage a demoscene crew across a procedurally-generated network of BBS nodes — trading, producing demos, raiding rivals, and running courier missions over 50 in-game days.

- Standard library only — no pip packages
- CP437 encoding throughout (IBM VGA font) — never use UTF-8 or smart quotes
- Fixed 80×24 ANSI display, no scrolling
- Tested via SyncTerm connected to Mystic BBS, not a local terminal

## Running the Game

**Via Mystic BBS (primary):**
```
run.bat <NODE> <HANDLE>
```
Mystic calls this with `%N` (node) and `%H` (socket handle). It copies `DOOR.SYS`, runs `python game.py <NODE> <HANDLE>`, then cleans up.

**Local debug mode (no BBS):**
```bash
python game.py
```
Falls back to debug stub if no `DOOR.SYS` found. Unreliable on Windows — prefer SyncTerm via Mystic for real tests.

**Other utilities:**
```bash
python sockettest.py            # Test socket handle adoption
python make_placeholders.py     # Regenerate placeholder art/ files
python -c "import game, courier, combat, world, player, ansi, door, socketio"  # Check imports
```

## Architecture

### Module Map

| Module | Role |
|---|---|
| `game.py` | Entry point (`main()` line 868), main game loop (`hq_loop()`), all 8 player actions, random events, day-end logic |
| `ansi.py` | Display engine — all screen builders, animations, input (`get_key()`), art loading |
| `player.py` | `Player` class, resource caps, save/load (`saves/<HANDLE>.ini`), scoring, leaderboard |
| `world.py` | Procedural world gen — `Node`, `NpcCrew`, `PartyEvent`, `World`; seeded by player handle |
| `combat.py` | **Canonical** combat logic — `resolve_raid()`, tactic multipliers, NPC daily trickle, defense decay |
| `courier.py` | Daily courier missions — deterministic per `hash(handle) ^ day`, accept/deliver/fail lifecycle |
| `door.py` | Parses `DOOR.SYS` drop file; provides `DoorInfo` with handle, BBS name, time limit |
| `socketio.py` | Adopts TCP socket handle from BBS (`socket.socket(fileno=handle)`), global I/O singleton |

### Display Engine (ansi.py)

Fixed layout, never scrolls. All output via `write_at(row, col, text, colour)`.

```
Rows  1- 8  Art zone (loaded from art/*.ans)
Row   9     DIV_1 divider
Rows 10-12  Menu zone (MENU_TOP / MENU_BOT)
Row  13     DIV_3 divider
Rows 14-22  Result zone (RES_TOP / RES_BOT) — redrawn via _result_buf[]
Row  23     STATUS_DIV
Row  24     Status bar
```

`result()` appends to `_result_buf[]`; `_redraw_result_zone()` repaints lines 14–22 atomically to avoid artifacts. `_truncate_ansi()` trims output to 80 cols while respecting colour escape sequences.

### Socket I/O

`socketio.py` adopts the BBS-provided handle with `socket.socket(AF_INET, SOCK_STREAM, 0, handle)` — never `socket.fromfd()`. `fromfd` dups the descriptor, leaving an orphaned handle that causes a TCP RST on exit instead of a clean FIN.

### World & Randomness

The world is seeded from `hash(door_info.handle)` — deterministic per player so the same handle always gets the same world layout. Courier missions are seeded `hash(player.handle) ^ player.day` so reloading the same day regenerates the same mission.

## Four Rules — Never Break

1. **Never call `print()`** — always `socketio.get_io().write()`
2. **Never use `writeln()` in screen builders** — always `write_at(row, col, text)`
3. **All combat logic lives in `combat.py`** — don't add combat math elsewhere
4. **All files are CP437** — no UTF-8; use `chr()` codepoints for any non-ASCII literals (smart-quote linter in VS Code will corrupt them otherwise)

## Config

`config.ini` controls everything tunable: `game_length_days`, `action_points_per_day`, starting/max resources, `npc_crew_count`, `npc_aggression`, `node_count`, `random_event_chance`, party frequency, display settings.

## Art Files

`art/*.ans` — 80 cols × 8 rows, CP437, with SAUCE00 record. `title.ans` uses the full canvas (rows 1–22). `art/taglines.txt` holds title screen taglines as plain ASCII (one per line) to avoid smart-quote corruption.

Run `python make_placeholders.py` to regenerate any missing placeholder art.

## Save Files

`saves/` (not in git) — created at runtime:
- `<HANDLE>.ini` — player state
- `<HANDLE>.world` — node discovery, NPC locations
- `oneliners.txt` — shared BBS oneliner wall (pipe-delimited)
- `leaderboard.txt` — all-time Hall of Fame
