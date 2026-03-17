=============================================================================
         DEMOSCENE: THE EXPLORATION OF ART — A CELLFISH PRODUCTION
=============================================================================

PROJECT OVERVIEW
----------------
"The Exploration of Art" is a Python-based BBS Door game focused on the 
underground culture of the demoscene. Players manage a crew, explore a 
procedural network of BBS nodes, trade resources, and produce digital art 
to gain reputation.

TECHNICAL SPECIFICATIONS
------------------------
- Engine: Custom 80x24 fixed-coordinate ANSI display engine.
- Protocol: Passive TCP Socket I/O.
- Compatibility: Designed primarily for Mystic BBS on Windows/Linux.
- Logic: Standard Python 3.x library only (no external pip requirements).

INSTALLATION
------------
1. Ensure Python 3.x is installed and accessible via your system PATH.
2. Extract all files to a dedicated directory (e.g., C:\mystic\doors\demoscene\).
3. Create the following subdirectories:
   - /saves : Stores player .sav and .world files.
   - /art   : Stores custom .ans files for the display engine.
4. Edit 'config.ini' to set your BBS name and SysOp handle.

BBS CONFIGURATION (MYSTIC)
--------------------------
To run this game as a door in Mystic BBS, use the following settings:

  Command: (D3) Exec Door 32-bit
  Data: c:\path\to\run.bat %N %H

The run.bat script must pass the Node Number (%N) and Socket Handle (%H) 
to game.py for the I/O layer to initialize correctly.

FILE MANIFEST
-------------
game.py      - Core game loop, action routing, and screen orchestration.
ansi.py      - Coordinate-based display engine and ANSI truncation logic.
socketio.py  - Passive TCP socket wrapper for Telnet-based BBS I/O.
player.py    - Player state management, resource tracking, and save/load.
world.py     - Procedural world generation and node management.
combat.py    - Math for raids, defenses, and tactic resolution.
door.py      - DROPFILE (DOOR.SYS / DORINFO1.DEF) parser.
config.ini   - Game balancing and BBS identification settings.
DEVLOG.md    - History of project development and version changes.

GAMEPLAY PROTOCOLS
------------------
- Layout: Reserved rows 23 (divider) and 24 (status bar). All gameplay 
  rendering occurs on rows 1 through 22.
- Input: The game uses a "Passive I/O" model. The BBS is expected to 
  handle local echoing of keystrokes.
- Persistence: Player data and world state are saved independently 
  using the player's handle as the filename.

=============================================================================
                     (C) 2026 CELLFISH PRODUCTIONS
=============================================================================