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
    move(STATUS, 1)
    _out(ERASE_LINE)
    left = (f" {DG}CREW {RST}{W}{player.crew_name}{RST}"
            f"  {DG}·{RST}  " f"{DG}HANDLE {RST}{G}{player.handle}{RST}"
            f"  {DG}·{RST}  " f"{DG}TURNS {RST}{Y}{player.turns_remaining}{DG}/10{RST}"
            f"  {DG}·{RST}  " f"{DG}DAY {RST}{W}{player.day}{RST}")
    right = f"{DG}NODE {node}{RST}"
    left_plain = f" CREW {player.crew_name}  ·  HANDLE {player.handle}  ·  TURNS {player.turns_remaining}/10  ·  DAY {player.day}"
    right_plain = f"NODE {node}"
    # Stop at SCREEN_W-1 (col 79) — writing to col 80 on the last row
    # causes the terminal to scroll the entire screen up one line
    pad = (SCREEN_W - 1) - len(left_plain) - len(right_plain)
    _out(left + " " * max(0, pad) + right)
    move(1, 1)  # park cursor at top-left after writing to last row

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
        [("[E]", "Explore"), ("[T]", "Travel"),   ("[P]", "Produce")],
        [("[R]", "Raid"),    ("[D]", "Defend"),    ("[B]", "Trade")],
        [("[M]", "Messages"),("[S]", "Scores"),    ("[Q]", "Quit / save")],
    ]
    col_starts = [3, 30, 57]
    for r_idx, items in enumerate(rows):
        row = MENU_TOP + r_idx
        for col, (hk, lbl) in zip(col_starts, items):
            move(row, col); _out(f"{C}{hk}{RST} {W}{lbl}{RST}")
    draw_divider(DIV_3); clear_zone(RES_TOP, RES_BOT)
    draw_divider(STATUS_DIV); draw_status(player, player.bbs_name)

def screen_map(player, world, page=0, page_size=5):
    clear_screen(); draw_art("map"); draw_divider(11); clear_zone(12, 22)
    disc = world.discovered_nodes()
    pg_cnt = max(1, (len(disc) + page_size - 1) // page_size)
    shown = disc[page*page_size : (page+1)*page_size]
    write_at(12, 1, f"  {DG}NETWORK MAP{RST}  Page {page+1}/{pg_cnt}")
    row = 14
    for idx, node in enumerate(shown, 1):
        write_at(row, 1, f"  {C}[{idx}]{RST} {W}{node.name:<24} {node.label:<14}")
        row += 1
    write_at(22, 1, f"  Travel to node [1-{len(shown)}] or Q: ")

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

    # Status bar on row 24 — never write past col 79 to avoid scroll
    move(24, 1); _out(ERASE_LINE)
    _out(f" {DG}HANDLE:{RST} {G}{player.handle}{RST}"
         f"       {DG}CREW:{RST} {W}{player.crew_name}{RST}"
         f"          "
         f"{DG}TURNS{RST} {Y}{player.turns_remaining}{DG}/10{RST}"
         f" {DG}.{RST} {DG}DAY{RST} {W}{player.day}{RST}"
         f" {DG}.{RST} {DG}NODE 1{RST}")
    move(1, 1)  # park cursor at top-left — never leave it at row 24 col 79+

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
    """Redraw the status bar on row 24 after a scan (turns change)."""
    move(24, 1); _out(ERASE_LINE)
    _out(f" {DG}HANDLE:{RST} {G}{player.handle}{RST}"
         f"       {DG}CREW:{RST} {W}{player.crew_name}{RST}"
         f"          "
         f"{DG}TURNS{RST} {Y}{player.turns_remaining}{DG}/10{RST}"
         f" {DG}.{RST} {DG}DAY{RST} {W}{player.day}{RST}"
         f" {DG}.{RST} {DG}NODE 1{RST}")
    move(1, 1)  # park cursor away from last row


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


def screen_trade(player, node):
    """Trade post screen."""
    from player import RESOURCE_NAMES
    screen_base("trade", player, player.bbs_name,
                cmd_hint="[1-7] Select  [B] Buy  [S] Sell  [Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}LOCATION {RST}{B}{node.name}{RST}"
         f"  {DG}|{RST}  {DG}YOUR CREDITS {RST}{Y}{player.phone_credits}{RST}")

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


def screen_messages(messages, player=None):
    """Message board screen."""
    screen_base("messages", player, player.bbs_name if player else "", cmd_hint="[Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'':3}{'FROM':<18}{'SUBJECT':<34}{'DAY'}{RST}")
    move(MENU_TOP + 1, 1)
    _out(DG); _out(b"\xc4" * SCREEN_W); _out(RST)

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


def screen_hof(entries, player_handle, player=None):
    """Hall of Fame screen."""
    screen_base("hof", player, player.bbs_name if player else "", cmd_hint="[Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'HANDLE':<16}{'CREW':<22}"
         f"{'BBS':<18}{'SCORE':>8}{RST}")
    move(MENU_TOP + 1, 1)
    _out(DG); _out(b"\xc4" * SCREEN_W); _out(RST)

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


