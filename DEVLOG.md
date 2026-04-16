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
  https://raw.githubusercontent.com/dextercf/demoscene/main/courier.py
  https://raw.githubusercontent.com/dextercf/demoscene/main/config.ini
  https://raw.githubusercontent.com/dextercf/demoscene/main/DEVLOG.md

---

## 2026-04-16  —  UI polish session 2

### Changes
- Hall of Fame: removed header line, single divider, score table moved up,
  handle in bright green, crew/bbs in dark green, styled [Q] Quit prompt
- Hall of Fame: fixed leaderboard save crash (em dash not CP437 encodable)
- Hall of Fame: score now submitted on [Q] quit as well as game end
- Travel screen: current node shown as dimmed with (current) tag, pressing
  its number does nothing
- Travel prompt: "BBS to connect to:" wording, "-" separators between options
- Quit prompt: clear_results() on [N], styled [Y]/[N] brackets
- Raid screen: fixed write_at for target list to prevent disconnect
- Raid screen: removed undefined colour names causing silent crash on [R]

### Resume here next session
Priority 1: Commit all changes to GitHub
Priority 2: Starting tools = 0 makes early combat unwinnable — add starting bonus
Priority 3: Node-specific events (warez vs music vs art boards)
Priority 4: NPC personalities visible in more places (messages, events)

---

## 2026-04-16  —  Art, UI polish, NPC personalities

### Changes
- Score submitted on [Q] quit as well as game end — HoF now populates during testing
- Travel screen: 5 nodes/page, 4-char left padding, full dial-up sequence
  with green modem animation, bright white node name, keypress to continue
- Travel prompt: styled brackets, "Press node number to travel to:" wording
- ansi.py screen_map: fixed indentation error introduced during manual edit
- Fixed silent crash on [R] Raid and [Q] Quit caused by undefined colour
  names (BK, BW, BBLK, BWHT) — replaced with correct names (DG, C, W)
- Quit prompt: clear_results() on [N] so result zone doesn't stay dirty
- Raid target list: switched writeln() to write_at() to prevent disconnect
- All placeholder .ans files replaced with hand-made ANSI art
- header.ans renamed to explore.ans — all art files now named after their screen
- screen_explore(): removed post-load row clear loop (rows 9-14) that was
  erasing the bottom half of explore.ans art
- screen_title(): removed hard-coded menu lines — menu is now drawn in title.ans
  giving the art the full canvas (rows 1-22)
- hq_loop() [Q] Quit: added Y/N confirmation before saving and exiting
- NPC personalities: behaviour, backstory, taunt, home_bbs added to all 12 crews
  Combat modifiers applied per behaviour (raider/trader/artist/party/producer)
  Taunt shown on raid screen. Backstory surfaces in message board templates.

### Resume here next session
Priority 1: BBS test — title screen, explore screen, raid screen, quit confirm
Priority 2: Starting tools = 0 makes early combat unwinnable — add starting bonus
Priority 3: Node-specific events (warez vs music vs art boards feel different)

---

## 2026-04-16  —  Art placeholder session

### Goal
Generate placeholder .ans files for all art slots so every screen has
something visual while waiting for a real ANSI artist.

### Files changed
- `make_placeholders.py` — NEW FILE: generator script, produces all 12 art files
- `art/title.ans`     — NEW: colour-gradient block band, spaced letter logo
- `art/hq.ans`        — NEW: ASCII computer room, desk + monitor + scattered floppies
- `art/map.ans`        — NEW: node diagram with named nodes and link lines
- `art/raid.ans`       — NEW: two crews facing off, strength bars, VS divider
- `art/trade.ans`      — NEW: market shelves with item icons in box frames
- `art/produce.ans`    — NEW: fake TASM compiler output mid-compile
- `art/courier.ans`    — NEW: route line from origin to destination node
- `art/party.ans`      — NEW: big screen on wall, crowd of block-character heads
- `art/messages.ans`   — NEW: column headers + sample message rows, terminal style
- `art/hof.ans`        — NEW: three-column podium (1st/2nd/3rd) with stars
- `art/gameover.ans`   — NEW: fading signal bar, NO CARRIER centred, black borders
- `art/explore.ans`    — NEW: ASCII radar circle left, scanner status lines right

### Notes
- `art/header.ans` left untouched (existing hand-made art, already working)
- All placeholders: 80 cols x 8 rows, CP437, ANSI colour codes, SAUCE record
- Each file contains a red `[ PLACEHOLDER — art/xxx.ans ]` label so an artist
  knows exactly which file to replace
- To regenerate all placeholders: `python make_placeholders.py`
- To replace with final art: drop a new .ans into art/ — no code changes needed

### Artist brief (for when a real artist is found)
  80 cols wide, 8 rows tall
  CP437 charset (IBM VGA font)
  ANSI colour codes
  End file with SAUCE00 record
  Priority order: hq > title > party > raid > gameover > rest

### Known issues / TODO (unchanged from previous session)
- Local debug mode (python game.py without BBS) does not work reliably on
  this setup — use SyncTerm via Mystic BBS for all testing
- Placeholder art is functional but visually basic — awaiting real artist

### Resume here next session
Priority 1: Commit placeholder art + make_placeholders.py to GitHub
Priority 2: Pick a gameplay feature to implement:
  - NPC personalities (names, backstories, signature behaviours)
  - Node-specific events (warez vs music vs art boards feel different)
  - Courier mission variety (more mission templates)
  - Crew management (hire/fire with skills)
Priority 3: Investigate starting tools = 0 making early combat unwinnable

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

---

## 2026-04-12  —  BBS Skill Upgrade Pass (session 2)

### Goal
Finish the two remaining backlog items from the upgrade pass:
map pagination fix and courier mission system.

### Files changed
- `ansi.py`   — screen_map expanded, screen_courier_board/active added, HQ menu updated
- `game.py`   — action_courier added, hq_loop wired with courier + auto-delivery
- `combat.py` — apply_defense_decay restored
- `courier.py` — NEW FILE: full courier mission system

### Changes made

**ansi.py — screen_map pagination fixed**
  page_size=7, uses full RES_TOP..RES_BOT zone, shows total discovered
  count, contextual [N]ext/[P]rev hints, crew presence shown inline.

**courier.py — new module**
  5 mission templates scaling by difficulty (days 1-10, 1-25, all game).
  Full lifecycle: get_daily_mission → accept_mission → deliver_mission / fail_mission.
  Missions expire end of day+1.

**combat.py — apply_defense_decay restored**
  Was accidentally merged into apply_npc_daily_trickle. Restored.

---

## 2026-04-12  —  BBS Skill Upgrade Pass (session 1)

### Goal
Full codebase review. Fix dead code, expand content, balance improvements.

### Files changed
- `game.py`  — random events, message templates, produce failure, defense decay wired
- `combat.py` — NPC trickle, NPC strength cap fix
- `player.py` — resource cap enforcement, _caps dict

### Changes made

**Random events expanded (6 → 18)**
  18 events (7 positive, 7 negative, 4 neutral), weighted by rarity,
  negative events get 1.3× weight after day 35.

**Message templates (9 → 17, with act awareness)**
  Act-gated messages (early/mid/late game), deterministic seeding restored.

**Produce failure state added**
  Per-demo-type failure chance (cracktro 5% → full demo 20%).
  Resources spent before failure check.

**NPC daily resource trickle added**
  Aggressive crews recover ~14 resources/day vs ~8 for passive crews.

**Resource caps enforced in player.py**
  set_resource() now clamps to max(0, min(value, cap)).

---

## 2026-03-19  —  Session 8

### Goal
Fix explore double-bar, blank status bar on messages/hof, wire
counter-raid, fix defend scroll, unify status bar across all screens.

### Files changed
- `ansi.py` — cursor reset fix, draw_status unified, scroll fixes
- `game.py` — counter-raid wired, screen_messages/hof player arg

### Bugs fixed
- Explore double-bar: move(1,1) cursor reset before animation rows.
- Blank status bar on [M]/[S]: screen_messages/hof now pass player.
- Counter-raid flag now acted on in end_day().
- Defend scroll: draw_status() pads to 79 cols, parks cursor at (1,1).
- Status bar format unified across all screens via draw_status().

---

## 2026-03-19  —  Session 7

### Goal
Fix M and B disconnect, restore missing screen functions.

### Files changed
- `ansi.py` — restored 14 missing screen functions, scroll fix, CP437 fix
- `game.py` — explore animation flow fixes
- `game_commented.py` — NEW: fully commented copy of game.py

---

## 2026-03-18  —  Session 6

### Goal
Fix all HQ menu actions, explore screen layout, SyncTerm disconnect, GitHub.

### GitHub setup
  Repo: https://github.com/dextercf/demoscene
  Key commands: git pull --rebase / git add . / git commit -m "..." / git push
  Recovery: git clone https://github.com/dextercf/demoscene.git

### Explore screen layout (current spec)
  Rows  1-14  Art zone (header.ans or fallback)
  Row   15    Divider
  Row   16    [S] Scan   [Q] Back to HQ
  Row   17    Divider
  Row   18    Network scanner: [bar]     (EXP_SCAN)
  Row   19    Node: <name>               (EXP_NODE)
  Row   20    Info: <description>        (EXP_INFO)
  Rows 21-22  Empty
  Row   23    Divider
  Row   24    Status bar

---

## 2026-03-17  —  Session 5
Bug fixes on ansi.py, wire combat.py, fix scrolling, fix map input.

## 2026-03-16  —  Session 4
Stabilize I/O, passive socket model, ANSI truncation.
NOTE: accidentally stripped most action handlers — fixed in session 6.

## 2026-03-16  —  Session 3
Layout stabilization, map pagination, explore screen separation.
NOTE: stripped screen builders from ansi.py — fixed in sessions 6/7.

## 2026-03-15  —  Session 2
Bug fixes, combat.py wiring, new_game scroll fix, map input fix.

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

### 4 golden rules (never break these)
  1. Never use stdout/print directly — always socketio.get_io()
  2. Never use writeln() in screen builders — use write_at()
  3. combat.py is canonical for all combat logic
  4. All files encoded cp437

---
