"""
door.py — DOOR.SYS / DORINFO1.DEF drop file reader
Demoscene: The Exploration of Art
A Cellfish Production

Reads the drop file written by the BBS when launching a door game.
Supports DOOR.SYS (most common) and DORINFO1.DEF (older systems).
Falls back to a local debug mode if no drop file is found — useful
for testing on a plain Windows machine without a BBS running.
"""

import os
import sys

# Drop file search paths — Mystic and most BBS software write to
# the same directory as the door exe, or to a path passed as an
# argument on the command line.
DOOR_SYS_NAMES   = ["DOOR.SYS", "door.sys"]
DORINFO_NAMES    = ["DORINFO1.DEF", "dorinfo1.def", "DORINFO.DEF"]


class DropFileError(Exception):
    pass


class DoorInfo:
    """Holds all info read from the BBS drop file."""

    def __init__(self):
        self.handle       = "UNKNOWN"   # Player's BBS handle
        self.real_name    = ""          # Real name (may be empty)
        self.bbs_name     = "Unknown BBS"
        self.node         = 1
        self.time_limit   = 60          # Minutes remaining
        self.baud_rate    = 28800
        self.com_port     = 0           # 0 = local / no com port
        self.ansi         = True        # ANSI graphics supported
        self.debug_mode   = False       # True when no drop file found

    def __repr__(self):
        return (
            f"DoorInfo(handle={self.handle!r}, bbs={self.bbs_name!r}, "
            f"node={self.node}, time={self.time_limit}min, "
            f"ansi={self.ansi}, debug={self.debug_mode})"
        )


def _read_lines(path):
    """Read a file and return stripped lines, tolerating encoding issues."""
    try:
        with open(path, "r", encoding="cp437", errors="replace") as f:
            return [l.rstrip("\r\n") for l in f.readlines()]
    except OSError:
        return []


def _parse_door_sys(path):
    """
    Parse a DOOR.SYS file.
    Standard layout (one value per line):
      Line 1:  COM port (COM1 / COM0 = local)
      Line 2:  Baud rate
      Line 3:  Parity (ignored)
      Line 4:  Node number
      Line 5:  DTE baud rate (ignored)
      Line 6:  Screen display (Y/N)
      Line 7:  Printer (Y/N, ignored)
      Line 8:  Page bell (Y/N, ignored)
      Line 9:  Caller alarm (Y/N, ignored)
      Line 10: User real name
      Line 11: User location/city
      Line 12: Home phone (ignored)
      Line 13: Work/data phone (ignored)
      Line 14: Password (ignored)
      Line 15: Security level (ignored)
      Line 16: Total calls to BBS (ignored)
      Line 17: Last call date (ignored)
      Line 18: Seconds remaining THIS call
      Line 19: Minutes remaining THIS call
      Line 20: Graphics mode (COLOR/MONO/ANSI/RIP)
      Line 21: Screen height (rows)
      Line 22: User handle / alias
      Line 23: BBS name (not always present)
    """
    info  = DoorInfo()
    lines = _read_lines(path)
    if not lines:
        raise DropFileError(f"Could not read {path}")

    def get(n, default=""):
        return lines[n].strip() if n < len(lines) else default

    # COM port
    com_raw = get(0, "COM0").upper()
    if com_raw.startswith("COM"):
        try:
            info.com_port = int(com_raw[3:])
        except ValueError:
            info.com_port = 0

    # Baud rate
    try:
        info.baud_rate = int(get(1, "28800"))
    except ValueError:
        info.baud_rate = 28800

    # Node number
    try:
        info.node = int(get(3, "1"))
    except ValueError:
        info.node = 1

    # Real name (line 9, 0-indexed)
    info.real_name = get(9, "")

    # Minutes remaining (line 18 = seconds, line 19 = minutes — use minutes)
    try:
        info.time_limit = int(get(18, "60"))
    except ValueError:
        info.time_limit = 60

    # Graphics mode
    gfx = get(17, "GR").upper()
    info.ansi = gfx in ("GR", "COLOR", "ANSI", "RIP")

    # Handle — line 35 in Mystic's DOOR.SYS (0-indexed)
    handle = get(35, "").strip()
    if not handle:
        handle = get(34, "").strip()  # alias fallback
    if not handle:
        handle = info.real_name.split()[0] if info.real_name else "UNKNOWN"
    info.handle = handle

    # BBS name (line 22, optional)
    bbs = get(22, "").strip()
    if bbs:
        info.bbs_name = bbs

    return info


def _parse_dorinfo(path):
    """
    Parse a DORINFO1.DEF file.
    Layout:
      Line 0: BBS name
      Line 1: SysOp first name
      Line 2: SysOp last name
      Line 3: COM port (COMX or NONE)
      Line 4: Baud rate
      Line 5: 0 (reserved)
      Line 6: User first name
      Line 7: User last name
      Line 8: Location
      Line 9: ANSI flag (1 = yes, 0 = no)
      Line 10: Security level
      Line 11: Minutes remaining
      Line 12: Fossil flag (ignored)
    """
    info  = DoorInfo()
    lines = _read_lines(path)
    if not lines:
        raise DropFileError(f"Could not read {path}")

    def get(n, default=""):
        return lines[n].strip() if n < len(lines) else default

    info.bbs_name = get(0, "Unknown BBS")

    com_raw = get(3, "NONE").upper()
    info.com_port = 0 if com_raw == "NONE" else int(com_raw[3:] or 0)

    try:
        info.baud_rate = int(get(4, "28800"))
    except ValueError:
        info.baud_rate = 28800

    first = get(6, "UNKNOWN")
    last  = get(7, "")
    info.handle    = f"{first} {last}".strip()
    info.real_name = info.handle

    try:
        info.ansi = int(get(9, "1")) == 1
    except ValueError:
        info.ansi = True

    try:
        info.time_limit = int(get(11, "60"))
    except ValueError:
        info.time_limit = 60

    return info


def _debug_mode():
    """
    Return a DoorInfo populated with sensible defaults for local testing.
    Prompts for a handle so each test session feels personalised.
    """
    info = DoorInfo()
    info.debug_mode = True
    info.bbs_name   = "DEBUG STATION"
    info.ansi       = True
    info.time_limit = 99999  # unlimited in debug

    # Ask for a handle so save files work correctly during testing
    try:
        sys.stdout.write(
            "\r\n  No drop file found - running in DEBUG MODE.\r\n"
            "  Enter your handle (or press Enter for DEBUGGER): "
        )
        sys.stdout.flush()
        handle = sys.stdin.readline().strip()
        info.handle = handle if handle else "DEBUGGER"
    except (EOFError, KeyboardInterrupt):
        info.handle = "DEBUGGER"

    sys.stdout.write(f"\r\n  Debug mode active. Handle: {info.handle}\r\n\r\n")
    sys.stdout.flush()
    return info


def _search_paths():
    """
    Build a list of directories to search for drop files.
    Checks: current directory, directory of this script,
    and any path passed as a command-line argument.
    """
    paths = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
    ]
    # Mystic and some BBS software pass the node directory as argv[1]
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        paths.insert(0, sys.argv[1])
    return paths


def load():
    """
    Main entry point. Call this at game startup.
    Returns a populated DoorInfo object.

    Search order:
      1. DOOR.SYS  (preferred — most BBS software including Mystic)
      2. DORINFO1.DEF  (older / alternative systems)
      3. Debug mode  (no drop file found — local testing)
    """
    for directory in _search_paths():
        # Try DOOR.SYS first
        for name in DOOR_SYS_NAMES:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                try:
                    info = _parse_door_sys(candidate)
                    return info
                except DropFileError:
                    pass  # try next

        # Try DORINFO1.DEF
        for name in DORINFO_NAMES:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                try:
                    info = _parse_dorinfo(candidate)
                    return info
                except DropFileError:
                    pass

    # Nothing found — fall back to debug mode
    return _debug_mode()


# ---------------------------------------------------------------------------
# Quick self-test — run this file directly to check it works:
#   python door.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    info = load()
    print(info)
    print(f"\n  Handle    : {info.handle}")
    print(f"  BBS       : {info.bbs_name}")
    print(f"  Node      : {info.node}")
    print(f"  Time left : {info.time_limit} min")
    print(f"  Baud      : {info.baud_rate}")
    print(f"  ANSI      : {info.ansi}")
    print(f"  Debug mode: {info.debug_mode}")