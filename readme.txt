=============================================================================
         DEMOSCENE: THE EXPLORATION OF ART — A CELLFISH PRODUCTION
=============================================================================

PROJECT OVERVIEW
----------------
"The Exploration of Art" is a Python-based BBS Door game set in the
underground culture of the demoscene. Players manage a crew, explore a
network of BBS nodes, trade resources, produce digital art, run raids
on rival crews, and take on courier missions to earn phone credits.

TECHNICAL SPECIFICATIONS
------------------------
- Engine   : Custom 80x24 fixed-coordinate ANSI display engine
- Protocol : Passive TCP socket I/O (handle adoption, no dup)
- BBS      : Designed for Mystic BBS on Windows
- Encoding : CP437 throughout (IBM VGA font)
- Logic    : Standard Python 3.x library only — no pip requirements

INSTALLATION
------------
1. Ensure Python 3.x is installed and accessible via system PATH.
2. Extract all files to a dedicated directory
   (e.g. C:\mystic\doors\demoscene\).
3. The following subdirectories are required:
   - saves/  — player .ini save files, world state, shared BBS data
   - art/    — ANSI art files (.ans) for each screen
4. Edit config.ini to set your BBS name, SysOp handle, and balancing values.

BBS CONFIGURATION (MYSTIC)
--------------------------
Door type : Exec Door 32-bit (D3)
Data      : c:\path\to\run.bat %N %H

run.bat passes Node Number (%N) and Socket Handle (%H) to game.py.
The socket handle is adopted directly (no dup) to ensure a clean
disconnect when the player quits — the BBS resumes without RST.

FILE MANIFEST
-------------
game.py      — Core game loop, action routing, screen orchestration
ansi.py      — Coordinate-based ANSI display engine
socketio.py  — Passive TCP socket wrapper (handle adoption)
player.py    — Player state, resource tracking, save/load, oneliners
world.py     — Procedural world generation and node management
combat.py    — Raid/defense math and NPC trickle logic
courier.py   — Daily courier mission system (accept, carry, deliver)
door.py      — DROPFILE parser (DOOR.SYS / DORINFO1.DEF)
config.ini   — Game balancing and BBS identification settings
DEVLOG.md    — Full development history

art/         — ANSI art files (8 rows x 80 cols, CP437, SAUCE record)
  explore.ans   hq.ans       trade.ans    produce.ans
  raid.ans      courier.ans  oneliners.ans  hof.ans
  party.ans     gameover.ans title.ans    map.ans

saves/       — Runtime data (not in repo, created on first run)
  <handle>.ini        — Per-player save file
  <handle>.world      — Per-player world state
  oneliners.txt       — Shared BBS oneliner wall (all players)
  leaderboard.txt     — Shared Hall of Fame scores

GAMEPLAY SUMMARY
----------------
  Explore    — Scan for new BBS nodes to connect to
  Travel     — Move between discovered nodes (costs 1 turn each)
  Trade      — Buy and sell resources at each node's market
  Produce    — Spend resources to release demos, earning reputation
  Raid       — Attack rival NPC crews to steal resources
  Defend     — Shore up your crew's defenses
  Courier    — Accept a daily delivery mission for phone credits
  Oneliners  — Read and write on the shared BBS oneliner wall
  Hall of Fame — All-time score leaderboard across players

GAMEPLAY PROTOCOLS
------------------
- Layout   : Rows 1–8 art zone, rows 9–22 menu/result zone,
             row 23 status divider, row 24 status bar.
             Nothing scrolls — all output uses fixed cursor placement.
- Input    : Passive I/O — BBS handles local echo. Game reads raw keys.
- Turns    : Each in-game action costs turns. Day advances at 0 turns.
- Courier  : One mission per day, deterministic per player+day (reload-safe).
             Cargo is deducted from inventory on accept and delivered
             automatically when you travel to the destination node.
- Saves    : Player state and world saved on [Q] quit and on day advance.

GOLDEN RULES (never break these)
---------------------------------
1. Never use stdout/print directly — always socketio.get_io()
2. Never use writeln() in screen builders — use write_at()
3. combat.py is canonical for all combat logic
4. All files encoded CP437

=============================================================================
                     (C) 2026 CELLFISH PRODUCTIONS
=============================================================================
