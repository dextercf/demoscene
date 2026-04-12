"""
ansi.py - Display engine, cursor placement, animations
Demoscene: The Exploration of Art
A Cellfish Production
"""

import sys
import os
import time
import socketio as _sio
import re

SCREEN_W, SCREEN_H = 80, 25
ART_TOP, ART_BOT, DIV_1 = 1, 8, 9
MENU_TOP, MENU_BOT = 10, 12
DIV_3, RES_TOP, RES_BOT = 13, 14, 22
STATUS_DIV, STATUS, CMD_ROW = 23, 24, 22

ESC = "\x1b"
FG = {
    "black": f"{ESC}[30m", "red": f"{ESC}[31m", "green": f"{ESC}[32m",
    "yellow": f"{ESC}[33m", "blue": f"{ESC}[34m", "magenta": f"{ESC}[35m",
    "cyan": f"{ESC}[36m", "white": f"{ESC}[37m", "bright_black": f"{ESC}[90m",
    "bright_red": f"{ESC}[91m", "bright_green": f"{ESC}[92m", "bright_yellow": f"{ESC}[93m",
    "bright_blue": f"{ESC}[94m", "bright_magenta": f"{ESC}[95m", "bright_cyan": f"{ESC}[96m",
    "bright_white": f"{ESC}[97m",
}
RESET, BOLD, BLINK = f"{ESC}[0m", f"{ESC}[1m", f"{ESC}[5m"
CLEAR, HOME, HIDE_CURSOR, SHOW_CURSOR, ERASE_LINE = f"{ESC}[2J", f"{ESC}[H", f"{ESC}[?25l", f"{ESC}[?25h", f"{ESC}[2K"
C, Y, W, G, R, B, M, DG, RST = FG["cyan"], FG["yellow"], FG["bright_white"], FG["bright_green"], FG["bright_red"], FG["bright_blue"], FG["magenta"], FG["bright_black"], RESET

def _out(text):
    io = _sio.get_io()
    if io:
        io.write(text)
    else:
        if isinstance(text, bytes): sys.stdout.buffer.write(text)
        else: sys.stdout.buffer.write(text.encode("cp437", errors="replace"))
        sys.stdout.buffer.flush()

def write(text, colour="", reset=True):
    _out(colour + text + (RST if reset and colour else ""))

def writeln(text="", colour="", reset=True):
    write(text + "\r\n", colour, reset)

def hide_cursor(): _out(HIDE_CURSOR)
def show_cursor(): _out(SHOW_CURSOR)
def move(row, col): _out(f"{ESC}[{row};{col}H")

def clear_screen():
    _out(CLEAR + HOME)
    hide_cursor()

def clear_line(row):
    move(row, 1)
    _out(ERASE_LINE)

def clear_zone(top, bot):
    for row in range(top, bot + 1): clear_line(row)

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

def _truncate_ansi(text, width):
    visible, out, i = 0, [], 0
    while i < len(text) and visible < width:
        if text[i] == "\x1b":
            m = ANSI_RE.match(text, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                continue
        out.append(text[i])
        visible += 1
        i += 1
    return "".join(out)

def write_at(row, col, text, colour="", reset=True):
    if row > STATUS: return  # block writes beyond STATUS row (25+)
    move(row, col)
    _out(ERASE_LINE)
    out = colour + text + (RST if reset and colour else "")
    _out(_truncate_ansi(out, SCREEN_W - col + 1))

def write_at_no_clear(row, col, text, colour="", reset=True):
    if row > STATUS: return  # block writes beyond STATUS row (25+)
    move(row, col)
    out = colour + text + (RST if reset and colour else "")
    _out(_truncate_ansi(out, SCREEN_W - col + 1))

_result_buf = [""] * (RES_BOT - RES_TOP + 1)

def _redraw_result_zone():
    for i, line in enumerate(_result_buf):
        move(RES_TOP + i, 1)
        _out(ERASE_LINE)
        if line: _out(_truncate_ansi(line, SCREEN_W))

def result(text, colour=""):
    global _result_buf
    formatted = colour + text + (RST if colour else "")
    size = RES_BOT - RES_TOP + 1
    _result_buf = (_result_buf + [formatted])[-size:]
    _redraw_result_zone()
    hide_cursor()

def clear_results():
    global _result_buf
    _result_buf = [""] * (RES_BOT - RES_TOP + 1)
    _redraw_result_zone()
    hide_cursor()

ART_PATH = "art"
def set_art_path(path):
    global ART_PATH
    ART_PATH = path

def load_art(name, speed=0):
    path = os.path.join(ART_PATH, f"{name}.ans")
    if not os.path.isfile(path): return False
    try:
        with open(path, "rb") as f: data = f.read()
        move(ART_TOP, 1)
        if speed <= 0: _out(data)
        else:
            delay = 1.0 / speed
            for byte in data: _out(bytes([byte])); time.sleep(delay)
        return True
    except OSError: return False

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
    ]
}

def draw_art(name, speed=0):
    move(ART_TOP, 1)
    if load_art(name, speed): return
    lines = FALLBACK_ART.get(name, [])
    for i, line in enumerate(lines):
        if i >= (ART_BOT - ART_TOP + 1): break
        move(ART_TOP + i, 1)
        _out(ERASE_LINE); _out(line)

def draw_divider(row, char=None, colour=DG):
    move(row, 1)
    _out(ERASE_LINE)
    _out(colour)
    if char is None:
        _out(b"\xc4" * (SCREEN_W - 1))   # CP437 ─, stop at col 79 to prevent scroll
    else:
        _out(char * (SCREEN_W - 1))
    _out(RST)

def draw_status(player, bbs_name="", node=1):
    """
    Draw the status bar on the last row (STATUS=24).
    Format matches the explore screen bar — identical across all screens.
    Stops at col 79 to prevent terminal scroll. Parks cursor at (1,1).
    """
    move(STATUS, 1)
    _out(ERASE_LINE)
    _out(f" {DG}HANDLE:{RST} {G}{player.handle}{RST}"
         f"       {DG}CREW:{RST} {W}{player.crew_name}{RST}"
         f"          "
         f"{DG}TURNS{RST} {Y}{player.turns_remaining}{DG}/10{RST}"
         f" {DG}.{RST} {DG}DAY{RST} {W}{player.day}{RST}"
         f" {DG}.{RST} {DG}NODE{RST} {W}{node}{RST}")
    move(1, 1)  # park cursor at top-left — never leave it on the last row

def dial(row, col, node_name, colour=C):
    hide_cursor()
    msg = f"Dialling {node_name}"
    for i in range(11):
        write_at_no_clear(row, col, f"{DG}{msg}{'.' * i}{RST}" + " " * (10 - i))
        time.sleep(0.1)
    write_at_no_clear(row, col, f"{DG}{msg}.......... {RST}{colour}CONNECT 28800{RST}")
    time.sleep(0.5)

def get_key(prompt="", valid_keys=None):
    if prompt: write(prompt)
    show_cursor()
    io = _sio.get_io()
    key = io.getkey(valid_keys) if io else "Q"
    hide_cursor()
    return key

def get_input(prompt, max_len=30):
    show_cursor()
    write(prompt, C)
    io = _sio.get_io()
    res = io.getline(max_len) if io else ""
    hide_cursor()
    return res

def screen_base(art_name, status_player=None, bbs_name="", node=1, cmd_hint=""):
    clear_screen()
    draw_art(art_name)
    draw_divider(DIV_1)
    clear_zone(MENU_TOP, MENU_BOT)
    if cmd_hint:
        move(DIV_3, 1); _out(ERASE_LINE)
        hint = f" {DG}{cmd_hint}{RST} "
        pad = max(0, SCREEN_W - (len(cmd_hint) + 2))
        _out(DG); _out(b"\xc4" * (pad // 2)); _out(RST + hint); _out(DG); _out(b"\xc4" * (pad - pad // 2)); _out(RST)
    else: draw_divider(DIV_3)
    clear_zone(RES_TOP, RES_BOT)
    draw_divider(STATUS_DIV)
    if status_player: draw_status(status_player, bbs_name, node)
    else: clear_line(STATUS)
    clear_results()

def screen_title():
    clear_screen(); draw_art("title"); draw_divider(DIV_1)
    move(MENU_TOP, 1); _out(f"  {C}[N]{RST} New game  {C}[C]{RST} Continue  {C}[S]{RST} Scores  {C}[Q]{RST} Quit")
    draw_divider(DIV_3); clear_line(STATUS); hide_cursor()

def screen_hq(player):
    clear_screen(); draw_art("hq"); draw_divider(DIV_1)
    # Menu at rows MENU_TOP (10-12) — safely above the result zone (14-22)
    # so result() calls never wipe the menu
    clear_zone(MENU_TOP, MENU_BOT)
    rows = [
        [("[E]", "Explore"),  ("[T]", "Travel"),  ("[P]", "Produce")],
        [("[R]", "Raid"),     ("[D]", "Defend"),   ("[B]", "Trade")],
        [("[C]", "Courier"),  ("[M]", "Messages"), ("[W]", "Crew")],
    ]
    col_starts = [3, 30, 57]
    for r_idx, items in enumerate(rows):
        row = MENU_TOP + r_idx
        for col, (hk, lbl) in zip(col_starts, items):
            move(row, col); _out(f"{C}{hk}{RST} {W}{lbl}{RST}")
    # Show [Q] Quit on the DIV_3 line
    move(DIV_3, 1)
    _out(ERASE_LINE)
    _out(f" {DG}{'─' * 48}{RST}  {C}[S]{RST} {W}Scores{RST}  {C}[Q]{RST} {W}Quit/Save{RST}")
    clear_zone(RES_TOP, RES_BOT)
    draw_divider(STATUS_DIV); draw_status(player, player.bbs_name)

def screen_map(player, world, page=0, page_size=7):
    clear_screen(); draw_art("map"); draw_divider(DIV_1); clear_zone(MENU_TOP, RES_BOT)
    disc = world.discovered_nodes()
    total = len(disc)
    pg_cnt = max(1, (total + page_size - 1) // page_size)
    shown = disc[page*page_size : (page+1)*page_size]

    # Header row in MENU zone
    write_at(MENU_TOP, 1,
        f"  {DG}NETWORK MAP{RST}  "
        f"{C}Page {page+1}/{pg_cnt}{RST}  "
        f"{DG}({total} nodes discovered){RST}")

    # Nav hints on MENU_TOP+1
    nav = []
    if page > 0:           nav.append(f"{C}[P]{RST} Prev")
    if page < pg_cnt - 1:  nav.append(f"{C}[N]{RST} Next")
    nav.append(f"{C}[Q]{RST} Back")
    write_at(MENU_TOP + 1, 1, "  " + "   ".join(nav))

    draw_divider(DIV_3)

    # Node list in RES zone — up to 7 rows (RES_TOP..RES_TOP+6)
    for idx, node in enumerate(shown, 1):
        crew_tag = f"  {R}{node.crew[:12]}{RST}" if node.crew else ""
        write_at(RES_TOP + idx - 1, 1,
            f"  {C}[{idx}]{RST} {W}{node.name:<24}{RST} "
            f"{DG}{node.label:<18}{RST}"
            f"{crew_tag}")

    # Prompt on RES_BOT (row 22) — safe from status bar
    write_at(RES_BOT, 1,
        f"  {DG}Travel [1-{len(shown)}]"
        + (f"  [N]ext" if page < pg_cnt - 1 else "")
        + (f"  [P]rev" if page > 0 else "")
        + f"  [Q]uit: {RST}")

def screen_explore(player):
    """
    Explore screen layout — strictly 24 rows:
      Rows  1-14  Art zone (header.ans or map.ans fallback)
      Row  15     Divider
      Row  16     [S] Scan network   [Q] Back to HQ
      Row  17     Divider
      Row  18     Network scanner: [bar]
      Row  19     Node: <n>
      Row  20     Info: <description>
      Rows 21-22  (empty)
      Row  23     Divider
      Row  24     Status bar (HANDLE / CREW / TURNS / DAY / NODE)
    """
    global _result_buf
    clear_screen()

    # Art zone rows 1-14
    move(1, 1)
    if not load_art("header"):
        draw_art("map")
    # Pad/clear rows 9-14 in case art is shorter than 14 rows
    for row in range(9, 15):
        move(row, 1); _out(ERASE_LINE)

    draw_divider(15)                        # divider above menu

    move(16, 1); _out(ERASE_LINE)          # menu row
    _out(f"  {C}[S]{RST} {W}Scan network{RST}"
         f"     {C}[Q]{RST} {W}Back to HQ{RST}")

    draw_divider(17)                        # divider below menu

    # Scanner rows 18-20 — write without ERASE_LINE to avoid cursor drift
    def _wr(row, text):
        import re as _re
        plain = _re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
        move(row, 1)
        _out(text + " " * max(0, (SCREEN_W - 1) - len(plain)))

    _wr(18, f"   {DG}Network scanner: {RST}[" + " " * 30 + "]")
    _wr(19, f"   {DG}Node:{RST}")
    _wr(20, f"   {DG}Info:{RST}")
    _wr(21, "")
    _wr(22, "")

    draw_divider(23)                        # divider above status

    # Status bar — use draw_status for consistency across all screens
    draw_status(player, player.bbs_name)

    _result_buf = [""] * (RES_BOT - RES_TOP + 1)
    hide_cursor()


# Explore screen row constants
EXP_SCAN  = 18   # Network scanner bar row
EXP_NODE  = 19   # Node name row  
EXP_INFO  = 20   # Info/description row


def _draw_exp_labels():
    """
    Reset the scanner zone to idle state.
    Uses same full-width write as screen_explore — no ERASE_LINE.
    """
    import re as _re
    def _wr(row, text):
        plain = _re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
        move(row, 1)
        _out(text + " " * max(0, (SCREEN_W - 1) - len(plain)))
        move(1, 1)
    _wr(EXP_SCAN, f"   {DG}Network scanner: {RST}[" + " " * 30 + "]")
    _wr(EXP_NODE, f"   {DG}Node:{RST}")
    _wr(EXP_INFO, f"   {DG}Info:{RST}")
    _wr(21, "")
    _wr(22, "")


def _draw_explore_status(player):
    """Redraw the status bar on the explore screen — delegates to draw_status."""
    draw_status(player, player.bbs_name)


def animate_scan_bar(found=None):
    """
    Animate the Network Scanner progress bar on row EXP_SCAN.
    Bar fills left to right over ~7-8 seconds with random tempo.
    Bright green leading edge fades to dark green.
    Node name is revealed at ~3 seconds on EXP_NODE.
    """
    import random as _rnd
    BAR_WIDTH  = 30
    BAR_COL    = 22       # column of first bar char (after "   Network scanner: [")
    TOTAL_TIME = 7.5
    NODE_AT    = 3.0
    hide_cursor()

    BRIGHT_G = FG["bright_green"]
    DARK_G   = FG["green"]
    FILL     = b"\xdb".decode("cp437")   # █
    EMPTY    = b"\xb0".decode("cp437")   # ░

    # Reset cursor to a known position before any row-relative moves.
    # After get_key() the cursor position is unknown — the terminal may
    # have drifted. An explicit move(1,1) then move(EXP_SCAN, BAR_COL)
    # guarantees we land on the right row regardless of prior state.
    move(1, 1)
    move(EXP_SCAN, BAR_COL)
    _out(" " * BAR_WIDTH)  # blank the bar area before animating

    node_revealed = False
    start = time.time()
    step = 0

    while step <= BAR_WIDTH:
        elapsed = time.time() - start

        # Reveal node name at NODE_AT seconds
        if not node_revealed and elapsed >= NODE_AT:
            node_revealed = True
            if found:
                animate_explore_line(EXP_NODE, found.name)
            else:
                move(EXP_NODE, 1); _out(ERASE_LINE)
                _out(f"   {DG}Node:{RST}  {DG}--- no signal ---{RST}")

        # Build complete 30-char bar (filled green + dim dots for remainder)
        bright_portion = max(0, step - 4)
        bar = ""
        for i in range(BAR_WIDTH):
            if i < bright_portion:
                bar += DARK_G + FILL
            elif i < step:
                bar += BRIGHT_G + FILL
            else:
                bar += DG + EMPTY
        bar += RST

        # Write bar directly at BAR_COL — no ERASE_LINE, just overwrite
        move(EXP_SCAN, BAR_COL)
        _out(bar)

        step += 1

        remaining = TOTAL_TIME - elapsed
        steps_left = BAR_WIDTH - step + 1
        if steps_left > 0:
            base_delay = remaining / max(1, steps_left)
            jitter = _rnd.uniform(-0.08, 0.18)
            delay = max(0.05, base_delay + jitter)
        else:
            delay = 0.0
        time.sleep(delay)

    # Ensure node was revealed
    if not node_revealed and found:
        animate_explore_line(EXP_NODE, found.name)


def animate_explore_line(row, text):
    """
    Write text on a fixed row one character at a time.
    First two letters of each word: bright green.
    Remaining letters: dark green.
    """
    BRIGHT_G = FG["bright_green"]
    DARK_G   = FG["green"]
    hide_cursor()

    # Reset cursor tracking before writing to this row
    move(1, 1)
    move(row, 1); _out(ERASE_LINE)
    if row == EXP_NODE:
        _out(f"   {DG}Node:{RST}  ")
    elif row == EXP_INFO:
        _out(f"   {DG}Info:{RST}  ")
    else:
        _out("   ")

    word_char = 0
    for ch in text:
        if ch == " ":
            word_char = 0
            _out(DG + ch + RST)
        else:
            colour = BRIGHT_G if word_char < 2 else DARK_G
            _out(colour + ch + RST)
            word_char += 1
        time.sleep(0.04)

# ---------------------------------------------------------------------------
# Screen builders and animations (restored from original)
# ---------------------------------------------------------------------------

SPINNER_FRAMES = ["|", "/", "-", "\\"]

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
    """Dots appearing one by one - scanning/connecting feel."""
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
        filled = b"\xdb".decode("cp437") * i
        empty  = b"\xb0".decode("cp437") * (steps - i)
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


def combat_bar(row, col, label, value, max_val, width=20, colour=G):
    """Draw a single combat stat bar - used in raid screen."""
    pct    = max(0, min(1.0, value / max_val)) if max_val > 0 else 0
    filled = int(pct * width)
    bar    = b"\xdb".decode("cp437") * filled + b"\xb0".decode("cp437") * (width - filled)
    write_at_no_clear(row, col,
                      f"{DG}{label:<12}{RST}{colour}[{bar}]{RST}"
                      f" {W}{value:>3}{RST}")


def animate_combat_bars(row, player_power, enemy_power):
    """
    Animate both combat bars simultaneously - bars fill up
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


def screen_courier_board(player, mission):
    """Courier mission board screen."""
    screen_base("courier", player, player.bbs_name,
                cmd_hint="[A] Accept  [Q] Decline")
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {C}COURIER MISSION BOARD{RST}  {DG}Day {player.day}{RST}")

    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    diff_stars = "*" * mission.difficulty + " " * (3 - mission.difficulty)
    _out(f"  {Y}{mission.label}{RST}  {R}[{diff_stars}]{RST}")

    draw_divider(DIV_3)

    desc    = mission.desc[:70]
    origin  = mission.origin[:24]
    dest    = mission.dest[:24]
    cargo   = mission.cargo_key.replace("_", " ")
    reward  = mission.reward_summary()[:40]
    write_at(RES_TOP,     1, f"  {W}{desc}{RST}")
    write_at(RES_TOP + 2, 1, f"  {DG}Pick up:{RST}  {C}{origin}{RST}")
    write_at(RES_TOP + 3, 1, f"  {DG}Deliver:{RST}  {C}{dest}{RST}")
    write_at(RES_TOP + 4, 1, f"  {DG}Cargo:{RST}   {Y}{mission.cargo_amt} {cargo}{RST}")
    write_at(RES_TOP + 5, 1, f"  {DG}Reward:{RST}  {G}{reward}{RST}")
    write_at(RES_TOP + 6, 1, f"  {DG}Expires:{RST} {R}End of day {mission.expires_day}{RST}")
    write_at(RES_TOP + 8, 1, f"  {DG}Need {mission.cargo_amt} {cargo} in inventory to accept.{RST}")


def screen_courier_active(player, mission):
    """Show active mission status on HQ screen result area."""
    write_at(RES_TOP, 1,
        f"  {C}ACTIVE MISSION:{RST} {W}{mission.label}{RST}  "
        f"{DG}→ {mission.dest}{RST}")
    write_at(RES_TOP + 1, 1,
        f"  {DG}Deliver {mission.cargo_amt} "
        f"{mission.cargo_key.replace('_', ' ')} to {mission.dest}"
        f"  Reward: {mission.reward_summary()}{RST}")


def screen_trade(player, node):
    """Trade post screen — 7 items in RES zone."""
    from player import RESOURCE_NAMES
    screen_base("trade", player, player.bbs_name,
                cmd_hint="[1-7] Select  [B] Buy  [S] Sell  [Q] Back")

    # Header in MENU zone
    node_name = node.name[:24]
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {DG}NODE {RST}{B}{node_name:<24}{RST}"
         f"  {DG}Credits: {RST}{Y}{player.phone_credits}{RST}")
    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    _out(f"  {DG}{'#':<3} {'ITEM':<15} {'BUY':>7}  {'SELL':>6}  {'YOURS':>6}{RST}")
    move(MENU_TOP + 2, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # Item list in RES zone — all 7 fit in 7 rows
    trade_keys = ["floppy_disks", "source_code", "artwork",
                  "mod_music", "hardware", "tools", "beer"]
    for i, key in enumerate(trade_keys):
        row = RES_TOP + i
        if row > RES_BOT:
            break
        name  = RESOURCE_NAMES.get(key, key)
        buy   = node.prices.get(key, 0)
        sell  = node.sell_price(key)
        yours = player.get_resource(key)
        # Highlight speciality resource at this node
        is_spec = (key == node.speciality)
        col = Y if is_spec else W
        spec_tag = f"{Y}★{RST}" if is_spec else " "
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {C}[{i+1}]{RST}{spec_tag}{col}{name:<15}{RST}"
             f"  {G}{buy:>6}c{RST}"
             f"  {R}{sell:>5}c{RST}"
             f"  {Y}{yours:>6}{RST}")


def screen_produce(player):
    """Demo production screen — list in RES zone with affordability and fail chance."""
    screen_base("produce", player, player.bbs_name,
                cmd_hint="[1-5] Select  [Q] Back")

    demos = [
        ("1", "Cracktro",  {"source_code": 50,  "artwork": 20},         40,  5),
        ("2", "4K Intro",  {"source_code": 120, "artwork": 40},        120, 10),
        ("3", "64K Intro", {"source_code": 200, "artwork": 80},        280, 15),
        ("4", "Musicdisk", {"source_code": 80,  "mod_music": 300},     200, 10),
        ("5", "Full Demo", {"source_code": 400, "artwork": 200,
                            "mod_music": 150},                          600, 20),
    ]

    # Header in MENU zone
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'TYPE':<13}{'COST':<28}{'REP':>5}  {'FAIL%':>5}{RST}")
    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    _out(f"  {DG}src:{RST}{W}{player.source_code:>5}{RST}  "
         f"{DG}art:{RST}{W}{player.artwork:>5}{RST}  "
         f"{DG}mod:{RST}{W}{player.mod_music:>5}{RST}  "
         f"{DG}turns: 3  rep:{RST}{C}{player.reputation:>5}{RST}")
    move(MENU_TOP + 2, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # Demo list in RES zone
    for i, (key, label, costs, rep, fail_pct) in enumerate(demos):
        row = RES_TOP + i
        if row > RES_BOT:
            break
        can      = player.can_afford(costs)
        col      = W if can else DG
        key_col  = C if can else DG
        cost_str = "  ".join(f"{v}{k[:3]}" for k, v in costs.items())
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {key_col}[{key}]{RST}"
             f" {col}{label:<13}{RST}"
             f"  {DG}{cost_str:<26}{RST}"
             f"  {Y if can else DG}+{rep:<4}{RST}"
             f"  {R if fail_pct >= 15 else DG}{fail_pct:>4}%{RST}")


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
    loot_s = npc_crew.resources.get("source_code",   0) // 3
    # Loot preview in RES zone — safe from divider collision
    write_at(RES_TOP, 1,
        f"  {DG}Potential loot if successful:{RST}")
    write_at(RES_TOP + 1, 1,
        f"  {Y}~{loot_c} credits{RST}  "
        f"{W}~{loot_d} disks{RST}  "
        f"{C}~{loot_s} source{RST}")
    write_at(RES_TOP + 3, 1,
        f"  {DG}Enemy strength: {RST}{R}{npc_crew.strength}{RST}"
        f"  {DG}Defense: {RST}{B}{npc_crew.defense}{RST}"
        f"  {DG}Aggression: {RST}"
        + (f"{R}!!!" if npc_crew.aggression == 3
           else f"{Y}!!" if npc_crew.aggression == 2
           else f"{DG}!") + RST)


def screen_messages(messages, player=None):
    """Message board screen — uses full RES zone for up to 7 messages."""
    screen_base("messages", player, player.bbs_name if player else "", cmd_hint="[Q] Back")

    # Header in MENU zone
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {C}MESSAGE BOARD{RST}  {DG}{len(messages)} message{'s' if len(messages) != 1 else ''}{RST}")
    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    _out(f"  {DG}{'':3}{'FROM':<18}{'SUBJECT':<36}{'DAY'}{RST}")
    move(MENU_TOP + 2, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # Messages in RES zone — up to 7 rows (RES_BOT - RES_TOP + 1 = 9, leave 2 for spacing)
    shown = messages[:7]
    for i, msg in enumerate(shown):
        row = RES_TOP + i
        if row > RES_BOT:
            break
        new_tag = f"{C}NEW{RST}" if msg.get("new") else f"{DG}   {RST}"
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {new_tag} "
             f"{B}{msg.get('from', '???'):<18}{RST}"
             f"{W}{msg.get('subject', ''):<36}{RST}"
             f"{DG}D{msg.get('day', '?')}{RST}")


def screen_hof(entries, player_handle, player=None):
    """Hall of Fame screen — uses full RES zone for up to 9 entries."""
    screen_base("hof", player, player.bbs_name if player else "", cmd_hint="[Q] Back")

    # Header in MENU zone
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {Y}HALL OF FAME{RST}  {DG}{len(entries)} entr{'ies' if len(entries) != 1 else 'y'}{RST}")
    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'HANDLE':<14}{'CREW':<20}{'BBS':<16}{'SCORE':>8}{'  DAY':>6}{RST}")
    move(MENU_TOP + 2, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # Entries in RES zone — up to 9 rows
    for i, e in enumerate(entries[:9]):
        row = RES_TOP + i
        if row > RES_BOT:
            break
        is_player = e["handle"].upper() == player_handle.upper()
        name_col  = G if is_player else W
        rank_col  = Y if i == 0 else (C if i == 1 else (W if i < 5 else DG))
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {rank_col}{str(i+1)+'.':<4}{RST}"
             f"{name_col}{e['handle']:<14}{RST}"
             f"{DG}{e['crew']:<20}{RST}"
             f"{DG}{e['bbs'][:15]:<16}{RST}"
             f"{Y}{e['score']:>8}{RST}"
             f"{DG}{str(e.get('day','?')):>6}{RST}")


def screen_crew(player):
    """
    Crew management / dossier screen.
    Shows resources as visual bars, career stats, projected score,
    current node, and home board defense level.
    Full RES zone used — no data hidden by MENU_BOT cap.
    """
    screen_base("hq", player, player.bbs_name, cmd_hint="[Q] Back")

    # ── Header ────────────────────────────────────────────────────────────
    move(MENU_TOP, 1); _out(ERASE_LINE)
    crew  = player.crew_name[:18]
    hndl  = player.handle[:12]
    home  = player.bbs_name[:20]
    _out(f"  {Y}{crew:<18}{RST}  {DG}Handle: {RST}{C}{hndl:<12}{RST}  {DG}Home: {RST}{B}{home}{RST}")

    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    loc   = player.current_node[:18]
    _out(f"  {DG}Rep: {RST}{Y}{player.reputation:<6}{RST}  "
         f"{DG}Defense: {RST}{_defense_bar(player.defense)}  "
         f"{DG}Loc: {RST}{C}{loc}{RST}")

    move(MENU_TOP + 2, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # ── Resource bars in RES zone ─────────────────────────────────────────
    # Layout: two columns, 4 resources each
    resources_left = [
        ("Phone Credits", "phone_credits", 9999,  G),
        ("Floppy Disks",  "floppy_disks",  2000,  C),
        ("Source Code",   "source_code",   1000,  B),
        ("Artwork",       "artwork",        1000,  M),
    ]
    resources_right = [
        ("MOD Music",   "mod_music",  1000, Y),
        ("Beer",        "beer",         48, Y),
        ("Hardware",    "hardware",    500, DG),
        ("Tools",       "tools",       500, R),
    ]

    for i, (lbl, key, cap, col) in enumerate(resources_left):
        row = RES_TOP + i
        val = player.get_resource(key)
        bar = _resource_bar(val, cap, width=12, colour=col)
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {DG}{lbl:<14}{RST} {bar} {col}{val:>6}{RST}")

    for i, (lbl, key, cap, col) in enumerate(resources_right):
        row = RES_TOP + i
        val = player.get_resource(key)
        bar = _resource_bar(val, cap, width=12, colour=col)
        move(row, 41); _out(f"{DG}{lbl:<10}{RST} {bar} {col}{val:>5}{RST}")

    # ── Divider ───────────────────────────────────────────────────────────
    move(RES_TOP + 4, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # ── Career stats (two columns) ────────────────────────────────────────
    stats_left = [
        ("Demos released",  player.demos_produced),
        ("Raids won",       player.raids_won),
        ("Raids lost",      player.raids_lost),
        ("Parties attended",player.parties_attended),
    ]
    stats_right = [
        ("Raves attended",  player.raves_attended),
        ("Beers drunk",     player.beers_drunk),
        ("5K runs",         getattr(player, "5k_runs", 0)),
        ("Day",             f"{player.day}/50"),
    ]

    for i, (lbl, val) in enumerate(stats_left):
        row = RES_TOP + 5 + i
        if row > RES_BOT:
            break
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {DG}{lbl:<18}{RST} {W}{val}{RST}")

    for i, (lbl, val) in enumerate(stats_right):
        row = RES_TOP + 5 + i
        if row > RES_BOT:
            break
        move(row, 41)
        _out(f"{DG}{lbl:<16}{RST} {W}{val}{RST}")

    # ── Projected score ───────────────────────────────────────────────────
    proj = (player.reputation * 10
            + player.demos_produced * 50
            + player.raids_won * 30
            - player.raids_lost * 10
            + player.parties_attended * 100
            + player.raves_attended * 25
            + getattr(player, "5k_runs", 0) * 40)
    proj = max(0, proj)
    move(RES_BOT, 1); _out(ERASE_LINE)
    # Keep to 79 chars — RES_BOT is row 22, col 80 triggers scroll
    _out(f"  {DG}Projected: {RST}{Y}{proj:>8}{RST}"
         f"  {DG}Best: {RST}{C}{player.total_score:<8}{RST}")


def _resource_bar(value, cap, width=12, colour=G):
    """Render a compact resource bar: ████░░░░ style."""
    filled = min(width, int((value / max(cap, 1)) * width))
    empty  = width - filled
    return f"{colour}{'█' * filled}{DG}{'░' * empty}{RST}"


def _defense_bar(defense, width=8):
    """Render a defense bar with colour coding by level."""
    filled = min(width, int((defense / 100) * width))
    empty  = width - filled
    col = G if defense >= 60 else (Y if defense >= 30 else R)
    return f"{col}{'█' * filled}{DG}{'░' * empty}{RST} {col}{defense}{RST}"


def screen_party(party, player):
    """Demoparty screen."""

    from world import COMPO_DEFS
    screen_base("party", player, player.bbs_name,
                cmd_hint=f"[1-{len(party.compos)}] Compo  [D] Bar  [R] Rave  [Q] Leave")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {Y}{party.name}{RST}  {DG}|{RST}  {DG}{party.location}{RST}")
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
    _out(f"  {Y}GAME OVER - YOUR LEGACY IS WRITTEN{RST}")

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


