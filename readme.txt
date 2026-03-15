==============================================================================
  DEMOSCENE: THE EXPLORATION OF ART  v0.1
  A Cellfish Production
==============================================================================

  A BBS door game for Mystic BBS and compatible systems.
  Single-player RPG — explore the network, build your crew,
  produce demos, raid rivals, attend demoparties.

  https://cellfi.sh  (placeholder — update when published)

------------------------------------------------------------------------------
  REQUIREMENTS
------------------------------------------------------------------------------

  - Windows 10 / 11  (Linux also works for testing)
  - Python 3.8 or later  (free from https://python.org)
  - Mystic BBS, Synchronet, WWIV, or any BBS software that writes DOOR.SYS
  - An ANSI-capable terminal (SyncTerm, NetRunner, or any VT100 client)

  No additional Python packages are needed. Standard library only.

------------------------------------------------------------------------------
  INSTALLATION — QUICK START
------------------------------------------------------------------------------

  1. Create a folder for the game, e.g.:
       C:\games\demoscene\

  2. Copy all game files into that folder:
       game.py
       door.py
       player.py
       world.py
       ansi.py
       combat.py
       config.ini
       run.bat

  3. Create these subfolders (the game creates them automatically
     on first run, but you can create them now):
       C:\games\demoscene\saves\
       C:\games\demoscene\art\

  4. Edit config.ini with your BBS name and SysOp handle.
     See the CONFIG section below for details.

  5. Edit run.bat and set GAME_DIR to your installation folder.

  6. Test the game locally first:
       cd C:\games\demoscene
       python game.py
     It will run in debug mode — no BBS needed.

  7. Configure a door entry in Mystic BBS (see below).

------------------------------------------------------------------------------
  MYSTIC BBS DOOR CONFIGURATION
------------------------------------------------------------------------------

  In Mystic BBS, go to:
    Sysop Menu > Door Games > Add Door

  Fill in the following settings:

    Name        : Demoscene: The Exploration of Art
    Description : Demoscene BBS door RPG by Cellfish
    Filename    : C:\games\demoscene\run.bat
    Drop File   : DOOR.SYS
    Path        : C:\mystic\temp\%NODE%\
    Hot Keys    : Yes
    ANSI Level  : 1 (ANSI)
    Time limit  : 0 (use BBS time limit)

  Replace C:\mystic\temp\%NODE%\ with your actual Mystic temp path.
  The %NODE% variable is replaced by Mystic with the current node number.

------------------------------------------------------------------------------
  CONFIGURATION — config.ini
------------------------------------------------------------------------------

  Open config.ini in Notepad to customise the game for your BBS.

  [bbs]
    bbs_name      Your BBS name — appears on the title screen and as the
                  player's home node in the game world.
    sysop_handle  Your handle — appears in system messages.
    bbs_tagline   A short tagline shown on the title screen (max 60 chars).

  [gameplay]
    game_length_days      How many days before the game ends (default: 50)
    action_points_per_day Action points per day (default: 10)
    starting_*            Starting resources for new players
    npc_crew_count        Number of rival crews (default: 6)
    npc_aggression        How aggressive NPCs are: 1=passive, 3=aggressive
    node_count            Nodes on the network map (default: 20)
    random_event_chance   % chance of a random event per day (default: 25)

  [parties]
    party_frequency_days  Days between parties (default: 12)
    party_travel_cost     Credits to attend a party (default: 80)
    revision_5k_run       Enable/disable the Revision 5K run (yes/no)
    rave_events           Enable/disable rave events (yes/no)

  [display]
    ansi_mode    auto / yes / no  (auto recommended)
    art_path     Path to art pack folder (default: art)
    ansi_speed   Characters per second, 0 = instant (default: 0)
                 Set to 300 for a nostalgic modem trickle effect.

  DO NOT edit the [cellfish] section. The game identity is locked to
  Cellfish and will be restored automatically if modified.

------------------------------------------------------------------------------
  ART PACK INSTALLATION
------------------------------------------------------------------------------

  The game ships with plain ASCII fallback art on every screen.
  ANSI artists can supply replacement art files to make the game
  look spectacular.

  To install an art pack:

  1. Copy the .ans files into your art/ folder:
       C:\games\demoscene\art\

  2. Name each file to match the screen it replaces:

       title.ans     Title / main menu splash
       hq.ans        Crew HQ / main action screen
       map.ans       Network map screen
       trade.ans     Trade post screen
       produce.ans   Demo production screen
       raid.ans      Raid / combat screen
       messages.ans  Message board screen
       hof.ans       Hall of Fame screen
       party.ans     Demoparty screen
       gameover.ans  Game over screen

  3. Each file should be exactly 80 characters wide and no taller
     than 12 lines so it fits in the art zone above the UI strip.

  4. Use any standard ANSI/CP437 editor:
       PabloDraw    https://picoe.ca/products/pablodraw/
       Moebius      https://github.com/blocktronics/moebius
       ACiDDraw     Classic choice

  5. The game loads .ans files as raw bytes and outputs them directly
     to the terminal — no conversion needed. CP437 character set.

  If an art file is missing or unreadable the game falls back to
  the built-in ASCII art automatically — nothing will break.

  ART PACK CREDITS:
  If you supply art, add your handle and group to this file in the
  art/ folder so you get proper credit:
       art/ARTISTS.TXT

------------------------------------------------------------------------------
  SAVE FILES
------------------------------------------------------------------------------

  Player saves are stored in the saves/ folder:

    saves/HANDLE.sav      Player state (resources, progress, stats)
    saves/HANDLE.world    World map and NPC state for this player
    saves/leaderboard.txt Hall of Fame — shared by all players on the BBS

  All files are plain text — SysOps can open and edit them in Notepad.
  To reset a player's game, delete their .sav and .world files.
  To reset the leaderboard, delete leaderboard.txt.

------------------------------------------------------------------------------
  COMPATIBILITY
------------------------------------------------------------------------------

  DOOR.SYS support:
    Mystic BBS       Tested — primary target
    Synchronet       Should work — writes DOOR.SYS
    WWIV             Should work — writes DOOR.SYS
    EleBBS           Should work — writes DOOR.SYS
    PCBoard          Should work — writes DOOR.SYS
    RemoteAccess     Should work — writes DORINFO1.DEF (also supported)

  If your BBS software is not listed, check whether it writes a
  DOOR.SYS or DORINFO1.DEF file — if it does, the game should work.

  The game also runs in standalone debug mode with no BBS at all —
  useful for testing and single-machine play.

------------------------------------------------------------------------------
  TROUBLESHOOTING
------------------------------------------------------------------------------

  "python is not recognized..."
    Python is not installed or not in your PATH.
    Download from https://python.org and check "Add to PATH" during install.

  "No drop file found — running in DEBUG MODE"
    The game could not find DOOR.SYS. In debug mode this is normal.
    On a live BBS, check that run.bat is correctly copying DOOR.SYS
    and that the Mystic door path is configured correctly.

  Garbled characters / no colour
    Your terminal may not support ANSI. Use SyncTerm or NetRunner.
    Or set ansi_mode = no in config.ini for plain text output.

  Characters display as boxes or question marks
    Set your terminal to CP437 / IBM PC character set.
    In SyncTerm: Options > Font > CP437

  Game runs slowly
    Set ansi_speed = 0 in config.ini for instant display.

  Player save is corrupt
    Delete saves/HANDLE.sav and saves/HANDLE.world to reset that player.

------------------------------------------------------------------------------
  ABOUT
------------------------------------------------------------------------------

  Demoscene: The Exploration of Art is a tribute to the golden age of
  BBS culture and the demoscene — the coders, artists and musicians
  who pushed hardware to its limits for the love of the craft.

  Inspired by Planets: The Exploration of Space by Jon Radoff (1993)
  and the tradition of BBS door games like Legend of the Red Dragon,
  Trade Wars 2002, and Solar Realms Elite.

  Developed by Cellfish.
  Art packs welcome — see ART PACK INSTALLATION above.

  "The scene never dies. It just moves to a new node."

==============================================================================
  CELLFISH  —  DEMOSCENE: THE EXPLORATION OF ART  —  v0.1
==============================================================================
