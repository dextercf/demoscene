"""
ansi.py - Display engine, cursor placement, animations
Demoscene: The Exploration of Art
A Cellfish Production

Full cursor-placement based display engine.
Nothing scrolls. Everything draws in place.
All output routes through socketio.
"""

import sys
import os
import time
import socketio as _sio

# ---------------------------------------------------------------------------
# Screen dimensions and zone constants
# ---------------------------------------------------------------------------

SCREEN_W = 80
SCREEN_H = 24

ART_TOP  = 1    # Art zone
ART_BOT  = 12
DIV_1    = 13   # Divider after art
STATUS   = 14   # Status bar
DIV_2    = 15   # Divider after status
MENU_TOP = 16   # Menu / content zone
MENU_BOT = 18
DIV_3    = 19   # Divider above result zone
RES_TOP  = 20   # Result zone (5 lines)
RES_BOT  = 24   # Last line of screen
CMD_ROW  = 24   # Command / prompt row (alias for RES_BOT)

# ---------------------------------------------------------------------------
# ANSI escape codes
# ---------------------------------------------------------------------------

ESC = "\x1b"

# Foreground colours
FG = {
    "black"         : f"{ESC}[30m",
    "red"           : f"{ESC}[31m",
    "green"         : f"{ESC}[32m",
    "yellow"        : f"{ESC}[33m",
    "blue"          : f"{ESC}[34m",
    "magenta"       : f"{ESC}[35m",
    "cyan"          : f"{ESC}[36m",
    "white"         : f"{ESC}[37m",
    "bright_black"  : f"{ESC}[90m",
    "bright_red"    : f"{ESC}[91m",
    "bright_green"  : f"{ESC}[92m",
    "bright_yellow" : f"{ESC}[93m",
    "bright_blue"   : f"{ESC}[94m",
    "bright_magenta": f"{ESC}[95m",
    "bright_cyan"   : f"{ESC}[96m",
    "bright_white"  : f"{ESC}[97m",
}

RESET = f"{ESC}[0m"
BOLD  = f"{ESC}[1m"
BLINK = f"{ESC}[5m"

CLEAR      = f"{ESC}[2J"
HOME       = f"{ESC}[H"
HIDE_CURSOR= f"{ESC}[?25l"
SHOW_CURSOR= f"{ESC}[?25h"
ERASE_LINE = f"{ESC}[2K"
SAVE_CUR   = f"{ESC}[s"
REST_CUR   = f"{ESC}[u"

# Shorthand colour aliases
C   = FG["cyan"]
Y   = FG["yellow"]
W   = FG["bright_white"]
G   = FG["bright_green"]
R   = FG["bright_red"]
B   = FG["bright_blue"]
M   = FG["magenta"]
DG  = FG["bright_black"]
RST = RESET

# ---------------------------------------------------------------------------
# Core I/O — all output routes through socketio
# ---------------------------------------------------------------------------

def _out(text):
    """Write to the current I/O layer."""
    io = _sio.get_io()
    if io:
        io.write(text)
    else:
        if isinstance(text, bytes):
            sys.stdout.buffer.write(text)
        else:
            sys.stdout.buffer.write(
                text.encode("cp437", errors="replace")
            )
        sys.stdout.buffer.flush()


def write(text, colour="", reset=True):
    """Write coloured text."""
    out = colour + text + (RST if reset and colour else "")
    _out(out)


def writeln(text="", colour="", reset=True):
    """Write coloured text followed by CRLF."""
    write(text + "\r\n", colour, reset)


def hide_cursor():
    _out(HIDE_CURSOR)


def show_cursor():
    _out(SHOW_CURSOR)


def pause(seconds):
    time.sleep(seconds)


# ---------------------------------------------------------------------------
# Cursor control
# ---------------------------------------------------------------------------

def move(row, col):
    """Move cursor to absolute position (1-based)."""
    _out(f"{ESC}[{row};{col}H")


def clear_screen():
    """Clear entire screen."""
    io = _sio.get_io()
    if io and not getattr(io, "is_socket", True) and sys.platform == "win32":
        os.system("cls")
    else:
        _out(CLEAR + HOME)
    hide_cursor()


def clear_line(row):
    """Clear a specific line without touching others."""
    move(row, 1)
    _out(ERASE_LINE)


def clear_zone(top, bot):
    """Clear a range of lines."""
    for row in range(top, bot + 1):
        clear_line(row)


def write_at(row, col, text, colour="", reset=True):
    """Write text at a specific screen position."""
    move(row, col)
    _out(ERASE_LINE)
    if colour:
        _out(colour + text[:SCREEN_W] + (RST if reset else ""))
    else:
        _out(text[:SCREEN_W])


def write_at_no_clear(row, col, text, colour="", reset=True):
    """Write text at position without clearing the line first."""
    move(row, col)
    if colour:
        _out(colour + text + (RST if reset else ""))
    else:
        _out(text)


# ---------------------------------------------------------------------------
# Result zone — fixed 4-line scrolling buffer
# ---------------------------------------------------------------------------

_result_buf = ["", "", "", "", ""]


def _redraw_result_zone():
    """Redraw all result lines in place."""
    for i, line in enumerate(_result_buf):
        move(RES_TOP + i, 1)
        _out(ERASE_LINE)
        if line:
            _out(line[:SCREEN_W])


def result(text, colour=""):
    """
    Add a line to the result zone. Old lines scroll up within the zone.
    Nothing ever escapes rows RES_TOP to RES_BOT.
    """
    global _result_buf
    formatted = colour + text + (RST if colour else "")
    size = RES_BOT - RES_TOP + 1
    _result_buf = (_result_buf + [formatted])[-size:]
    _redraw_result_zone()
    hide_cursor()


def clear_results():
    """Clear the result zone."""
    global _result_buf
    size = RES_BOT - RES_TOP + 1
    _result_buf = [""] * size
    _redraw_result_zone()
    hide_cursor()


# ---------------------------------------------------------------------------
# Art zone
# ---------------------------------------------------------------------------

ART_PATH = "art"


def set_art_path(path):
    global ART_PATH
    ART_PATH = path


def load_art(name, speed=0):
    """
    Load a .ans file from the art folder.
    Returns True if displayed, False if not found.
    """
    path = os.path.join(ART_PATH, f"{name}.ans")
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            data = f.read()
        move(ART_TOP, 1)
        if speed <= 0:
            _out(data)
        else:
            delay = 1.0 / speed
            for byte in data:
                _out(bytes([byte]))
                time.sleep(delay)
        return True
    except OSError:
        return False


# Fallback art — one per screen, max 12 lines x 80 chars
FALLBACK_ART = {
    "title": [
        "                                                                                ",
        f"{DG}  ██████╗ ███████╗███╗   ███╗ ██████╗ ███████╗ ██████╗███████╗███╗   ██╗{RST}",
        f"{DG}  ██╔══██╗██╔════╝████╗ ████║██╔═══██╗██╔════╝██╔════╝██╔════╝████╗  ██║{RST}",
        f"{C}  ██║  ██║█████╗  ██╔████╔██║██║   ██║███████╗██║     █████╗  ██╔██╗ ██║{RST}",
        f"{C}  ██║  ██║██╔══╝  ██║╚██╔╝██║██║   ██║╚════██║██║     ██╔══╝  ██║╚██╗██║{RST}",
        f"{W}  ██████╔╝███████╗██║ ╚═╝ ██║╚██████╔╝███████║╚██████╗███████╗██║ ╚████║{RST}",
        f"{DG}  ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═══╝{RST}",
        "                                                                                ",
        f"              {Y}T H E   E X P L O R A T I O N   O F   A R T{RST}             ",
        "                                                                                ",
        f"                    {DG}>>> A CELLFISH PRODUCTION <<<{RST}                    ",
        "                                                                                ",
    ],
    "hq": [
        "                                                                                ",
        f"  {DG}+{'─'*74}+{RST}",
        f"  {DG}│{RST}{C}  YOUR CREW HEADQUARTERS  ·  THE NERVE CENTRE OF YOUR OPERATION    {RST}{DG}│{RST}",
        f"  {DG}│{RST}  {DG}monitors flickering · floppy disks scattered · modem winking       {RST}{DG}│{RST}",
        f"  {DG}+{'─'*74}+{RST}",
        "                                                                                ",
        f"  {DG}[ PLACE YOUR HQ ANSI ART HERE — art/hq.ans — 80 cols x 10 rows ]{RST}   ",
        "                                                                                ",
        f"  {DG}Drop a .ans file into the /art folder to replace this placeholder.{RST}  ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "map": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {C}N E T W O R K   M A P{RST}  {DG}//  T H E   S C E N E   I S   A L I V E{RST}  {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {DG}o────o────o      o        nodes pulse across the phone lines            {RST}",
        f"  {DG}│         ╲    ╱ │        each one a world · each one a risk            {RST}",
        f"  {DG}o    ?     o──o  o                                                      {RST}",
        f"  {DG} ╲         │      ╲       [ art/map.ans to replace this screen ]        {RST}",
        f"  {DG}  o────────o   ?  o                                                     {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "trade": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {Y}T R A D E   P O S T{RST}  {DG}//  B U Y  *  S E L L  *  S W A P         {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {DG}floppy disks · source code · mod music · artwork · hardware · beer      {RST}",
        f"  {DG}the economy of the underground · know when to buy · know when to sell   {RST}",
        "                                                                                ",
        f"  {DG}[ art/trade.ans to replace this screen ]                                {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "produce": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {G}D E M O   P R O D U C T I O N{RST}  {DG}//  CREATE YOUR MASTERPIECE     {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {G}> COMPILING ...{RST}                                                        ",
        f"  {G}> LINKING   ...{RST}                                                        ",
        f"  {G}> PACKING   ...{RST}                                                        ",
        f"  {DG}64512 bytes · copper bars loading · tracker syncing{RST}                   ",
        "                                                                                ",
        f"  {DG}[ art/produce.ans to replace this screen ]                              {RST}",
        "                                                                                ",
        "                                                                                ",
    ],
    "raid": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {R}R A I D{RST}  {DG}//  ATTACK — STEAL — DOMINATE                        {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {R}YOUR CREW VERSUS THEIRS.{RST}                                               ",
        f"  {DG}a war fought through copper wire and cunning · no fists · only packets  {RST}",
        "                                                                                ",
        f"  {DG}[ art/raid.ans to replace this screen ]                                 {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "messages": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {B}M E S S A G E   B O A R D{RST}  {DG}//  THE UNDERGROUND               {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {DG}threats · rumours · alliances · trash talk · the board never sleeps     {RST}",
        "                                                                                ",
        f"  {DG}[ art/messages.ans to replace this screen ]                             {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "hof": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {Y}H A L L   O F   F A M E{RST}  {DG}//  LEGENDS OF THE BOARD            {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {DG}their names echo across every node · their modems are silent now        {RST}",
        f"  {DG}but their names remain · can you join them?                             {RST}",
        "                                                                                ",
        f"  {DG}[ art/hof.ans to replace this screen ]                                  {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "party": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {M}D E M O P A R T Y{RST}  {DG}//  THE SCENE GATHERS                      {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {DG}hundreds of screens flickering · the smell of energy drinks             {RST}",
        f"  {DG}somewhere h0ffman is setting up the decks · compo starts soon           {RST}",
        "                                                                                ",
        f"  {DG}[ art/party.ans to replace this screen ]                                {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
    "gameover": [
        f"  {DG}+=======================================================================+{RST}",
        f"  {DG}|{RST}  {R}G A M E   O V E R{RST}  {DG}//  YOUR LEGACY IS WRITTEN               {DG}|{RST}",
        f"  {DG}+=======================================================================+{RST}",
        "                                                                                ",
        f"  {DG}the modem goes silent · the screen fades                                {RST}",
        f"  {DG}but your name remains on the board · for now                            {RST}",
        "                                                                                ",
        f"  {DG}[ art/gameover.ans to replace this screen ]                             {RST}",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
        "                                                                                ",
    ],
}


def draw_art(name, speed=0):
    """Draw art zone — tries .ans file first, falls back to ASCII."""
    move(ART_TOP, 1)
    if load_art(name, speed):
        return
    lines = FALLBACK_ART.get(name, [])
    for i, line in enumerate(lines):
        if i >= (ART_BOT - ART_TOP + 1):
            break
        move(ART_TOP + i, 1)
        _out(ERASE_LINE)
        _out(line)


# ---------------------------------------------------------------------------
# Dividers and structural chrome
# ---------------------------------------------------------------------------

def draw_divider(row, char="─", colour=DG):
    move(row, 1)
    _out(ERASE_LINE)
    _out(colour + char * SCREEN_W + RST)


def draw_status(player, bbs_name="", node=1):
    """Draw the status bar at row STATUS. Called on resource changes."""
    move(STATUS, 1)
    _out(ERASE_LINE)
    left = (f" {DG}CREW {RST}{W}{player.crew_name}{RST}"
            f"  {DG}·{RST}  "
            f"{DG}HANDLE {RST}{G}{player.handle}{RST}"
            f"  {DG}·{RST}  "
            f"{DG}TURNS {RST}{Y}{player.turns_remaining}{DG}/10{RST}"
            f"  {DG}·{RST}  "
            f"{DG}DAY {RST}{W}{player.day}{RST}")
    # BBS info on right
    bbs  = bbs_name or getattr(player, "bbs_name", "")
    right = f"{DG}{bbs}  ·  NODE {node}{RST} "
    left_plain  = (f" CREW {player.crew_name}  ·  HANDLE {player.handle}"
                   f"  ·  TURNS {player.turns_remaining}/10  ·  DAY {player.day}")
    right_plain = f"{bbs}  ·  NODE {node} "
    pad = SCREEN_W - len(left_plain) - len(right_plain)
    _out(left + " " * max(0, pad) + right)


# ---------------------------------------------------------------------------
# Animation primitives
# ---------------------------------------------------------------------------

SPINNER_FRAMES = ["/", "-", "\\", "|"]


def spinner(row, col, message, duration=1.5, colour=C):
    """Animated spinner at fixed position."""
    hide_cursor()
    end = time.time() + duration
    i   = 0
    while time.time() < end:
        frame = SPINNER_FRAMES[i % 4]
        write_at_no_clear(row, col,
                          f"{colour}[{frame}]{RST} {DG}{message}{RST}")
        time.sleep(0.1)
        i += 1
    # Clear spinner line when done
    move(row, col)
    _out(" " * (len(message) + 5))


def dots(row, col, message, count=8, delay=0.15, colour=DG):
    """Dots appearing one by one — scanning/connecting feel."""
    hide_cursor()
    for i in range(count + 1):
        write_at_no_clear(row, col,
                          f"{colour}{message}{'.' * i}{RST}"
                          + " " * (count - i))
        time.sleep(delay)


def progress_bar(row, col, label, width=24, duration=1.2, colour=G):
    """Animated progress bar filling from 0 to 100%."""
    hide_cursor()
    steps = width
    for i in range(steps + 1):
        filled = "█" * i
        empty  = "░" * (steps - i)
        pct    = int((i / steps) * 100)
        bar    = f"{colour}[{filled}{empty}]{RST} {W}{pct:>3}%{RST}"
        write_at_no_clear(row, col, f"{DG}{label} {RST}{bar}")
        time.sleep(duration / steps)


def typewriter(row, col, text, colour=W, delay=0.04):
    """Text appears character by character."""
    hide_cursor()
    for i in range(len(text) + 1):
        move(row, col)
        _out(colour + text[:i] + RST + " ")
        time.sleep(delay)


def dial(row, col, node_name, colour=C):
    """Modem dialling effect."""
    hide_cursor()
    msg = f"Dialling {node_name}"
    dot_count = 10
    for i in range(dot_count + 1):
        write_at_no_clear(row, col,
                          f"{DG}{msg}{'.' * i}{RST}"
                          + " " * (dot_count - i))
        time.sleep(0.1)
    time.sleep(0.15)
    write_at_no_clear(row, col,
                      f"{DG}{msg}{'.' * dot_count} {RST}"
                      f"{colour}CONNECT 28800{RST}")
    time.sleep(0.5)


def combat_bar(row, col, label, value, max_val, width=20, colour=G):
    """Draw a single combat stat bar — used in raid screen."""
    pct    = max(0, min(1.0, value / max_val)) if max_val > 0 else 0
    filled = int(pct * width)
    bar    = "█" * filled + "░" * (width - filled)
    write_at_no_clear(row, col,
                      f"{DG}{label:<12}{RST}{colour}[{bar}]{RST}"
                      f" {W}{value:>3}{RST}")


def animate_combat_bars(row, player_power, enemy_power):
    """
    Animate both combat bars simultaneously — bars fill up
    then one drains based on outcome.
    """
    hide_cursor()
    max_p = 100
    steps = 20
    for i in range(steps + 1):
        pp = int((i / steps) * player_power)
        ep = int((i / steps) * enemy_power)
        combat_bar(row,     2, "Your crew",   pp, max_p, colour=G)
        combat_bar(row + 1, 2, "Enemy crew",  ep, max_p, colour=R)
        time.sleep(0.05)
    time.sleep(0.3)


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def get_key(prompt="", valid_keys=None):
    """Read a single keypress from the player."""
    if prompt:
        write(prompt)
    show_cursor()
    io = _sio.get_io()
    if io:
        key = io.getkey(valid_keys)
        hide_cursor()
        return key
    hide_cursor()
    return "Q"


def get_input(prompt, max_len=30):
    """Read a line of text input from the player."""
    show_cursor()
    write(prompt, C)
    io = _sio.get_io()
    if io:
        result_str = io.getline(max_len)
        hide_cursor()
        return result_str
    hide_cursor()
    return ""


def wait_for_key(message=None):
    """Display optional message and wait for any keypress."""
    if message:
        result(f"{DG}{message}{RST}")
    move(RES_TOP, 6)
    show_cursor()
    io = _sio.get_io()
    if io:
        io.getkey()
    hide_cursor()


# ---------------------------------------------------------------------------
# Full screen builders
# Each draws the static chrome once, then returns.
# Dynamic updates use write_at / result / draw_status.
# ---------------------------------------------------------------------------

def screen_base(art_name, status_player=None, bbs_name="", node=1,
                cmd_hint=""):
    """
    Draw the base chrome for any screen.
    status_player -- Player instance for the status bar, or None
    bbs_name      -- BBS name shown on the right of the status bar
    cmd_hint      -- short command reference shown on the DIV_3 divider line
    """
    clear_screen()
    draw_art(art_name)
    draw_divider(DIV_1)
    if status_player:
        draw_status(status_player, bbs_name, node)
    else:
        clear_line(STATUS)
    draw_divider(DIV_2)
    clear_zone(MENU_TOP, MENU_BOT)
    # Draw divider with optional command hint embedded
    if cmd_hint:
        move(DIV_3, 1)
        _out(ERASE_LINE)
        hint_str = f" {DG}{cmd_hint}{RST} "
        plain_len = len(cmd_hint) + 2
        pad = max(0, SCREEN_W - plain_len)
        _out(DG + "─" * (pad // 2) + RST + hint_str +
             DG + "─" * (pad - pad // 2) + RST)
    else:
        draw_divider(DIV_3)
    clear_zone(RES_TOP, RES_BOT)
    global _result_buf
    _result_buf = ["", "", "", "", ""]
    hide_cursor()


def screen_title():
    """Title / main menu screen."""
    clear_screen()
    draw_art("title")
    draw_divider(DIV_1)
    clear_line(STATUS)
    draw_divider(DIV_2)

    move(MENU_TOP, 1)
    _out(ERASE_LINE + f"  {C}[N]{RST} {W}New game{RST}")
    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE + f"  {C}[C]{RST} {W}Continue saved game{RST}")
    move(MENU_TOP + 2, 1)
    _out(ERASE_LINE + f"  {C}[S]{RST} {W}Hall of fame{RST}")

    draw_divider(DIV_3)
    clear_zone(RES_TOP, RES_BOT - 1)

    # [Q] Quit on last line
    move(RES_BOT, 1)
    _out(ERASE_LINE)
    _out(f"  {C}[Q]{RST} {W}Quit to BBS{RST}"
         + " " * 28
         + f"{DG}A CELLFISH PRODUCTION  v0.1{RST}")
    hide_cursor()


def screen_hq(player):
    """
    Crew HQ — main action screen.
    Drawn once. Updates via draw_status() and result().
    """
    screen_base("hq", player, player.bbs_name)

    actions = [
        ("[E]", "Explore network",  "[D]", "Defend home board"),
        ("[T]", "Travel to node",   "[B]", "Trade post"),
        ("[P]", "Produce demo",     "[M]", "Message board"),
        ("[R]", "Raid rival crew",  "[S]", "Scores / Hall of Fame"),
        ("[Q]", "Quit / save",      "",    ""),
    ]
    for i, (k1, l1, k2, l2) in enumerate(actions):
        row = MENU_TOP + i
        if row > MENU_BOT:
            break
        move(row, 1)
        _out(ERASE_LINE)
        col1 = f"  {C}{k1}{RST} {W}{l1}{RST}"
        col2 = f"  {C}{k2}{RST} {W}{l2}{RST}" if k2 else ""
        _out(col1.ljust(40) + col2)


def screen_map(player, world):
    """Network map screen — node list in menu+upper result zone, prompt at bottom."""
    screen_base("map", player, player.bbs_name,
                cmd_hint="[T] Travel  [E] Explore  [Q] Back")

    discovered = world.discovered_nodes()

    # Header rows in menu zone
    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'#':<5}{'NODE':<26}{'TYPE':<16}{'DIST':<10}CREW{RST}")
    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(DG + "·" * SCREEN_W + RST)

    # Node list: rows MENU_TOP+2 .. RES_BOT-2  (leave 2 rows for input prompt)
    LIST_TOP = MENU_TOP + 2
    LIST_BOT = RES_BOT - 2
    max_rows = LIST_BOT - LIST_TOP + 1

    for i, node in enumerate(discovered[:max_rows]):
        row = LIST_TOP + i
        move(row, 1)
        _out(ERASE_LINE)
        cur = f"{Y}►{RST}" if node.name == player.current_node else " "
        col = Y if node.name == player.current_node else W
        crew = f"{R}{node.crew}{RST}" if node.crew else ""
        _out(f"  [{i+1:02d}]{cur} {col}{node.name:<26}{RST}"
             f"{DG}{node.label:<16}{RST}"
             f"{DG}{node.hops} hops  {RST}{crew}")

    # Clear any leftover rows between list end and hint row
    for row in range(LIST_TOP + min(len(discovered), max_rows), RES_BOT - 1):
        move(row, 1)
        _out(ERASE_LINE)

    # Overflow / undiscovered hint on the line just above input prompt
    hint_row = RES_BOT - 1
    move(hint_row, 1)
    _out(ERASE_LINE)
    parts = []
    if len(discovered) > max_rows:
        parts.append(f"+ {len(discovered) - max_rows} more (#{max_rows+1:02d}+)")
    if world.undiscovered_count() > 0:
        parts.append(f"{world.undiscovered_count()} undiscovered")
    if parts:
        _out(DG + "  " + "  ·  ".join(parts) + RST)

    # Input prompt pinned to last row
    move(RES_BOT, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}Enter node number to travel, or {C}00{DG} to cancel:{RST}")


def screen_trade(player, node):
    """Trade post screen."""
    from player import RESOURCE_NAMES
    screen_base("trade", player, player.bbs_name,
                cmd_hint="[1-7] Select  [B] Buy  [S] Sell  [Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}LOCATION {RST}{B}{node.name}{RST}"
         f"  {DG}·{RST}  {DG}YOUR CREDITS {RST}{Y}{player.phone_credits}{RST}")

    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'ITEM':<16}  {'BUY':>7}  {'SELL':>7}  "
         f"{'STOCK':>6}  {'YOURS':>6}{RST}")

    trade_keys = ["floppy_disks", "source_code", "artwork",
                  "mod_music", "hardware", "tools", "beer"]
    for i, key in enumerate(trade_keys):
        row = MENU_TOP + 2 + i
        if row > MENU_BOT + 2:
            break
        name  = RESOURCE_NAMES.get(key, key)
        buy   = node.prices.get(key, 0)
        sell  = node.sell_price(key)
        yours = player.get_resource(key)
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {C}[{i+1}]{RST} {W}{name:<14}{RST}"
             f"  {G}{buy:>6}c{RST}"
             f"  {R}{sell:>6}c{RST}"
             f"  {DG}{99:>6}{RST}"
             f"  {Y}{yours:>6}{RST}")


def screen_produce(player):
    """Demo production screen."""
    screen_base("produce", player, player.bbs_name,
                cmd_hint="[1-5] Select  [Q] Back")

    demos = [
        ("1", "Cracktro",   {"source_code": 50,  "artwork": 20},        40),
        ("2", "4K Intro",   {"source_code": 120, "artwork": 40},        120),
        ("3", "64K Intro",  {"source_code": 200, "artwork": 80},        280),
        ("4", "Musicdisk",  {"source_code": 80,  "mod_music": 300},     200),
        ("5", "Full Demo",  {"source_code": 400, "artwork": 200,
                             "mod_music": 150},                          600),
    ]

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'':4}{'TYPE':<16}{'COST':<32}{'REP GAIN':>10}{RST}")

    for i, (key, label, costs, rep) in enumerate(demos):
        row = MENU_TOP + 1 + i
        if row > MENU_BOT + 2:
            break
        can      = player.can_afford(costs)
        col      = W if can else DG
        cost_str = "  ".join(f"{v} {k[:3]}" for k, v in costs.items())
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {C if can else DG}[{key}]{RST}"
             f" {col}{label:<16}{RST}"
             f"  {DG}{cost_str:<30}{RST}"
             f"  {Y if can else DG}+{rep} rep{RST}")

    # Current resources hint
    move(MENU_BOT + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}src:{RST}{W}{player.source_code:>5}{RST}  "
         f"{DG}art:{RST}{W}{player.artwork:>5}{RST}  "
         f"{DG}mod:{RST}{W}{player.mod_music:>5}{RST}  "
         f"{DG}rep:{RST}{C}{player.reputation:>5}{RST}")


def screen_raid(player, npc_crew):
    """Raid / combat screen."""
    screen_base("raid", player, player.bbs_name,
                cmd_hint="[A] Assault  [S] Sneak  [H] Hit&run  [Q] Retreat")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}RAIDING {RST}{R}{npc_crew.name}{RST}")

    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'YOUR CREW':<38}{'ENEMY CREW'}{RST}")

    # Draw initial combat bars (will animate when combat starts)
    combat_bar(MENU_TOP + 2, 2,  "Strength",
               player.tools * 2 + 20, 100, colour=G)
    combat_bar(MENU_TOP + 2, 42, "Strength",
               npc_crew.strength,     100, colour=R)
    combat_bar(MENU_TOP + 3, 2,  "Defense",
               player.defense,        100, colour=B)
    combat_bar(MENU_TOP + 3, 42, "Defense",
               npc_crew.defense,      100, colour=R)

    loot_c = npc_crew.resources.get("phone_credits", 0) // 3
    loot_d = npc_crew.resources.get("floppy_disks",  0) // 3
    move(MENU_BOT, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}Potential loot: {RST}"
         f"{Y}~{loot_c} credits{RST}  "
         f"{W}~{loot_d} disks{RST}")


def screen_messages(messages):
    """Message board screen."""
    screen_base("messages", cmd_hint="[Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'':3}{'FROM':<18}{'SUBJECT':<34}{'DAY'}{RST}")
    move(MENU_TOP + 1, 1)
    _out(DG + "·" * SCREEN_W + RST)

    row = MENU_TOP + 2
    shown = messages[-3:] if messages else []
    for msg in shown:
        if row > MENU_BOT:
            break
        new_tag = f"{C}NEW{RST}" if msg.get("new") else "   "
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {new_tag} "
             f"{B}{msg.get('from','???'):<18}{RST}"
             f"{W}{msg.get('subject',''):<34}{RST}"
             f"{DG}Day {msg.get('day','?')}{RST}")
        row += 1


def screen_hof(entries, player_handle):
    """Hall of Fame screen."""
    screen_base("hof", cmd_hint="[Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'HANDLE':<16}{'CREW':<22}"
         f"{'BBS':<18}{'SCORE':>8}{RST}")
    move(MENU_TOP + 1, 1)
    _out(DG + "·" * SCREEN_W + RST)

    row = MENU_TOP + 2
    for i, e in enumerate(entries[:3]):
        if row > MENU_BOT:
            break
        is_p = e["handle"].upper() == player_handle.upper()
        col  = G if is_p else W
        rnk  = Y if i == 0 else (W if i < 3 else DG)
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {rnk}{str(i+1)+'.':<4}{RST}"
             f"{col}{e['handle']:<16}{RST}"
             f"{DG}{e['crew']:<22}{RST}"
             f"{DG}{e['bbs']:<18}{RST}"
             f"{Y}{e['score']:>8}{RST}")
        row += 1


def screen_party(party, player):
    """Demoparty screen."""
    from world import COMPO_DEFS
    screen_base("party", player, player.bbs_name,
                cmd_hint=f"[1-{len(party.compos)}] Compo  [D] Bar  [R] Rave  [Q] Leave")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {Y}{party.name}{RST}  {DG}·{RST}  {DG}{party.location}{RST}")
    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{party.flavour}{RST}")

    row = MENU_TOP + 2
    for i, key in enumerate(party.compos):
        if row > MENU_BOT:
            break
        cdef = COMPO_DEFS.get(key, {})
        if not cdef:
            continue
        can  = player.can_afford(cdef.get("costs", {}))
        col  = W if can else DG
        cost = "  ".join(f"{v}{k[:3]}"
                         for k, v in cdef.get("costs", {}).items())
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {C if can else DG}[{i+1}]{RST}"
             f" {col}{cdef.get('label',''):<20}{RST}"
             f"  {DG}{cost:<28}{RST}"
             f"  {Y if can else DG}+{cdef.get('rep_1st',0)} rep{RST}")
        row += 1


def screen_game_over(player, rank):
    """Game over screen."""
    screen_base("gameover")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {Y}GAME OVER — YOUR LEGACY IS WRITTEN{RST}")

    stats = [
        ("Handle",           player.handle,           W),
        ("Crew",             player.crew_name,         W),
        ("Days played",      str(player.day),          W),
        ("Final score",      str(player.total_score),  Y),
        ("Hall of Fame",     f"#{rank}" if rank else "unranked", G),
        ("Demos produced",   str(player.demos_produced), W),
        ("Raids won",        str(player.raids_won),    W),
        ("Parties attended", str(player.parties_attended), W),
        ("Beers drunk",      str(player.beers_drunk),  Y),
    ]
    row = MENU_TOP + 1
    for label, value, col in stats:
        if row > MENU_BOT + 4:
            break
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {DG}{label:<20}{RST}{col}{value}{RST}")
        row += 1

    move(RES_BOT, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}Press any key to return to BBS...{RST}"
         + " " * 20
         + f"{DG}A CELLFISH PRODUCTION{RST}")