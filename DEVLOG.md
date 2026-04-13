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

## 2026-04-13  —  BBS Testing & Polish Session

### Goal
Live BBS testing via SyncTerm. Fix disconnects, improve screens, add
production animation and upload sequence.

### Files changed
- `ansi.py` — courier screen prompt fix, explore scan clear, screen_trade/produce/raid
  layout fixes, production animation, upload sequence with scrolling terminal
- `game.py` — trade ModuleNotFoundError fix, produce confirmation flow,
  explore world save fix, produce animation wiring

### Bugs fixed

**Courier screen disconnect**
  Root cause: long strings in screen_courier_board and screen_crew writing
  past col 79, triggering terminal scroll and Mystic disconnect.
  Fix: all strings truncated to safe lengths before output.

**Crew screen [Q] disconnect**
  Same root cause — col 80 overflow on projected score line.

**Trade screen [1] disconnect**
  Root cause 1: get_key(prompt=...) wrote prompt at unknown cursor position.
  Fix: prompt written at fixed RES_BOT rows.
  Root cause 2: from playermod import — playermod is an alias, not a module.
  Fix: changed to from player import RESOURCE_NAMES in all 3 locations.

**Explore duplicate nodes**
  world.save() not called after explore — disconnect lost discovered flag.
  Fix: world.save() called immediately after every successful discovery.

**screen_trade/produce/raid layout**
  All three bounded by MENU_BOT showing only 2-3 items. Fixed to use full
  RES zone. Trade shows speciality resource (star). Produce shows fail%.
  Raid shows loot preview and enemy stats.

**Produce screen — no confirmation or feedback**
  Pressing a number silently spent resources. Fixed with confirmation step
  showing cost/rep/fail% and [Y]/[Q] prompt.

**Produce screen layout reorganised**
  Resources moved to MENU_TOP (always visible), column headers below,
  demo list in RES zone, confirmation detail and prompt at bottom.
  Makes the screen readable at a glance without scrolling.

**Git hygiene — pycache and saves removed from tracking**
  __pycache__/, saves/, *.pyc, DOOR.SYS added to .gitignore.
  Removed from git history with git rm --cached.

**Double divider on produce screen**
  Fixed: screen_produce clears DIV_3 after drawing its own divider.

**Explore scan Node/Info not clearing between scans**
  Fixed: EXP_NODE and EXP_INFO reset at start of each animate_scan_bar().

**Production animation TypeError**
  write_at() called without text argument. Fixed: move()+_out() pattern.

### New features

**Production animation (screen_produce_animation)**
  Each demo type has its own step list (4-8 steps). Steps overwrite the
  same progress bar row. Scrolling log shows completed steps.
  ~25% chance of humorous interruption between steps: 15 variants including
  "Going for a 5K run...", "LOAD \"$\",8,1", "Out of beer. BRB.",
  "FORMAT C: /Q ... just kidding."

**Release board upload sequence (_produce_upload_sequence)**
  After successful production dials two boards:
  1. Cellfi.sh BBS (+47-32-75-42-50, Drammen, NO) — always first
  2. One random affiliate from 12 international boards
  Each session: modem init, digits typed out, RINGING, CONNECT, virus scan
  (5 scanners with progress bar), FILE_ID.DIZ check (shows DIZ content),
  upload progress bar (scales to file size), sysop response (18 variants
  including l33tsp34k), NO CARRIER.
  Terminal area rows 14-20 is a 7-line scrolling window. Row 21 fixed
  progress bar. Ends with release summary screen.

### Resume here next session
Priority 1: Continue BBS testing — raid, defend, parties.
Priority 2: Courier mission end-to-end test.
Priority 3: Message board sender handle improvements.

---

## 2026-04-12  —  BBS Skill Upgrade Pass (session 3)

### Goal
screen_messages/hof showing only 3 entries, crew management screen.

### Files changed
- `ansi.py`  — screen_messages, screen_hof, screen_crew, _resource_bar, _defense_bar
- `game.py`  — action_crew_screen, W key, _generate_messages count bump

### Changes made

**ansi.py — screen_messages fixed (3 → 7 messages)**
  Old: messages[-3:] bounded by MENU_BOT (3 rows max).
  New: messages[:7] in RES zone (RES_TOP..RES_BOT), header shows count,
       NEW tag coloured cyan, column widths adjusted for 80-char fit.

**ansi.py — screen_hof fixed (3 → 9 entries)**
  Old: entries[:3] bounded by MENU_BOT.
  New: entries[:9] in RES zone. Rank colours: gold=1st, cyan=2nd,
       white=3rd-5th, gray=rest. Day column added. Player row highlighted
       in green. BBS name truncated to 15 chars to fit 80 cols.

**ansi.py — screen_crew added (new)**
  Full dossier screen with:
  - Crew name, handle, home board in header
  - Reputation + defense bar (colour-coded: green≥60, yellow≥30, red<30)
  - Resource grid (8 resources, 2 columns) with visual █░░ bars and
    raw values — bars scale to per-resource cap from config
  - Career stats grid (2 columns): demos, raids, parties, raves, beer, 5K
  - Projected score formula shown live (matches final calculate_score())
  Accessible via [W] Crew on HQ menu.

**ansi.py — HQ menu updated**
  [W] Crew replaces [S] Scores in menu grid (Scores kept on divider line
  alongside [Q] Quit/Save so it remains discoverable).

**game.py — _generate_messages count bumped 5 → 7**
  Matches new screen_messages capacity.

**game.py — action_crew_screen + W key**
  Thin wrapper: calls screen_crew(player), waits for Q.

### Resume here next session
Priority 1: Push to GitHub.
Priority 2: Test on BBS — courier, crew screen, messages.
Priority 3: Map pagination confirm — test with 15+ discovered nodes.



### Goal
Finish the two remaining backlog items from the upgrade pass:
map pagination fix and courier mission system.

### Files changed
- `ansi.py`   — screen_map expanded, screen_courier_board/active added, HQ menu updated
- `game.py`   — action_courier added, hq_loop wired with courier + auto-delivery
- `combat.py` — apply_defense_decay restored (was accidentally merged into trickle fn)
- `courier.py` — NEW FILE: full courier mission system

### Changes made

**ansi.py — screen_map pagination fixed**
  Old: page_size=5, used hardcoded row numbers (12, 14–18, 22), prompt
       on row 22 collided with result buffer, no node count shown.
  New: page_size=7 (uses full RES_TOP..RES_BOT zone correctly),
       header shows total discovered nodes e.g. "(8 nodes discovered)",
       [N]ext/[P]rev hints shown contextually, crew presence shown inline.

**ansi.py — screen_hq menu updated**
  Added [C] Courier to third menu row (replaced [Q] which moved to DIV_3
  divider line — always visible, doesn't consume a menu row).

**game.py — action_courier + hq_loop**
  action_courier(): handles mission board display, accept flow, and
  in-place delivery when player is already at destination.
  hq_loop(): generates daily_mission at day start, refreshes each new
  day, auto-delivers when player travels to destination, fails mission
  with cargo return + -10 rep if day ends with active undelivered mission.

**courier.py — new module**
  5 mission templates scaling by difficulty:
    difficulty 1 (days 1-10):  disk run (120cr), source drop (160cr)
    difficulty 2 (days 1-25):  MOD transport (200cr), hardware haul (250cr)
    difficulty 3 (all game):   elite package (350cr + 40 rep)
  Full lifecycle: get_daily_mission → accept_mission → deliver_mission / fail_mission
  Missions expire end of day+1. Aggressive crews recover faster via trickle.
  Self-test included and passing.

**combat.py — apply_defense_decay restored**
  Was accidentally merged into apply_npc_daily_trickle body during
  previous session. Restored as a proper separate function.

### Resume here next session
Priority 1: Push upgraded files to GitHub.
Priority 2: Test courier missions end-to-end on BBS.
Priority 3: screen_messages shows only 3 messages — increase to 5-7.
Priority 4: Crew management screen (view your crew's stats).



### Goal
Full codebase review using the new bbs-game-creator skill. Fix dead code,
expand content, add balance improvements the skill identified as gaps.

### Files changed
- `game.py`  — random events, message templates, produce failure, defense decay wired
- `combat.py` — NPC trickle, NPC strength cap fix
- `player.py` — resource cap enforcement, _caps dict

### Changes made

**game.py — Random events expanded (6 → 18)**
  Old: 6 events, all flat-weighted, no negative events, used rng.choice()
  New: 18 events (7 positive, 7 negative, 4 neutral), weighted by rarity,
       negative events get 1.3× weight after day 35 for late-game tension.
  Skill reference: "Generate 10–20 events. Mix positive, negative, and neutral."

**game.py — Message templates (9 → 17, with act awareness)**
  Old: 9 templates, used module-level random.choice() breaking seeding,
       crew_fn lambdas took 2 args but called with 3 → silent crashes possible.
  New: 17 templates with correct 3-arg lambdas (p, w, r), act-gated messages
       (early/mid/late game), "__skip__" sentinel for out-of-window templates.
  Bug fixed: random.choice() → rng.choices() — deterministic seeding restored.

**game.py — Produce failure state added**
  Old: luck only affected reputation amount, never whether demo succeeded.
  New: per-demo-type failure chance (cracktro 5% → full demo 20%).
       Resources are spent before the failure check (risk/reward).
  Skill reference: BDD games need risk — flat-positive actions feel hollow.

**game.py — Defense decay wired**
  Old: apply_defense_decay() existed in combat.py but was never called.
  New: called in end_day() before the overnight raid check.

**combat.py — NPC daily resource trickle added**
  New function: apply_npc_daily_trickle(npc_crews, rng)
  Aggressive crews (agg=3) recover ~14 resources/day per slot vs ~8 for agg=1.
  Reason: raided crews had no recovery — after one raid they had nothing left,
          removing raiding as a viable late-game strategy.
  Called from end_day() in game.py.

**combat.py — NPC strength cap lowered**
  Old: min(100, ...) — losing crews could reach max strength of 100.
  New: min(90, ...) — leaves room for player to always have a fighting chance.

**player.py — Resource caps now enforced**
  Old: config.ini defined max_* values but set_resource() ignored them.
  New: _caps dict in __init__ with defaults matching config.ini defaults.
       apply_config() loads caps from config so sysop values are respected.
       set_resource() clamps: max(0, min(value, cap)).

### Resume here next session
Priority 1: Push to GitHub and test on BBS.
Priority 2: Map pagination — nodes beyond 7 still not all visible.
Priority 3: Courier mission system (mentioned in session 8 backlog).


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
