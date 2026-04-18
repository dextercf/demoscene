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

def draw_status(player, bbs_name="", node=1, show_credits=False):
    """
    Draw the status bar on the last row (STATUS=24).
    show_credits=True: right column shows phone credits (trade screen).
    show_credits=False (default): right column shows turns remaining.
    Stops at col 79 to prevent terminal scroll. Parks cursor at (1,1).
    """
    move(STATUS, 1)
    _out(ERASE_LINE)
    handle_crew = f"{player.handle}/{player.crew_name}"
    if show_credits:
        right_label, right_val, right_col = "Credits: ", player.phone_credits, Y
    else:
        right_label, right_val, right_col = "Turns: ", player.turns_remaining, C
    line = (f" {G}{handle_crew:<27}{RST}"
            f"{DG}Node: {RST}{W}{bbs_name:<22}{RST}"
            f"{DG}{right_label}{RST}{right_col}{right_val}{RST}")
    _out(line)
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

def _load_taglines():
    # filename/encoding built from codepoints — survives smart-quote linters
    _f = str().join(map(chr, [116,97,103,108,105,110,101,115,46,116,120,116]))  # taglines.txt
    _e = str().join(map(chr, [97,115,99,105,105]))                              # ascii
    path = os.path.join(ART_PATH, _f)
    try:
        with open(path, encoding=_e) as f:
            return [ln.rstrip() for ln in f if ln.strip()]
    except OSError:
        return []

_TAGLINES = None   # loaded lazily on first call

def _tagline_wrap(text, width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _animate_tagline():
    import random
    global _TAGLINES
    if _TAGLINES is None:
        _TAGLINES = _load_taglines()
    LG = FG["white"]   # light grey

    box_top, box_height = 10, 5
    box_left, box_width = 3, 23

    lines = _tagline_wrap(random.choice(_TAGLINES), box_width)
    lines = lines[:box_height]   # never overflow the box vertically

    # Pre-compute (row, col, char) for every character
    start_row = box_top + (box_height - len(lines)) // 2
    chars = []
    for li, line in enumerate(lines):
        row = start_row + li
        col = box_left + (box_width - len(line)) // 2
        for ci, ch in enumerate(line):
            chars.append((row, col + ci, ch))

    # Animate — only touch the 3 positions that change each step
    for i, (row, col, ch) in enumerate(chars):
        move(row, col);  _out(W  + ch  + RST)
        if i > 0:
            pr,  pc,  pch  = chars[i - 1]; move(pr,  pc);  _out(LG + pch  + RST)
        if i > 1:
            pr2, pc2, pch2 = chars[i - 2]; move(pr2, pc2); _out(DG + pch2 + RST)
        time.sleep(0.055)


def screen_title(version=""):
    clear_screen(); draw_art("title"); hide_cursor()
    if version:
        label = f"copyright cellfish 2026 - demoscene v{version}"
        col = SCREEN_W - len(label) + 1
        write_at_no_clear(1, col, label, DG)
    _animate_tagline()

def screen_hq(player):
    global _result_buf
    clear_screen()
    draw_art("hq")
    _result_buf = [""] * (RES_BOT - RES_TOP + 1)
    draw_divider(STATUS_DIV)
    draw_status(player, player.bbs_name)

def screen_map(player, world, page=0, page_size=5, mission_dest=None):
    clear_screen(); draw_art("map"); draw_divider(DIV_1); clear_zone(MENU_TOP, RES_BOT)
    disc = world.discovered_nodes()
    total = len(disc)
    pg_cnt = max(1, (total + page_size - 1) // page_size)
    shown = disc[page*page_size : (page+1)*page_size]

    # Header row in MENU zone
    write_at(MENU_TOP, 1,
        f"    {DG}NETWORK MAP{RST}  "
        f"{C}Page {page+1}/{pg_cnt}{RST}  "
        f"{DG}({total} nodes discovered){RST}")

    for idx, node in enumerate(shown, 1):
        crew_tag   = f"  {R}{node.crew[:12]}{RST}" if node.crew else ""
        is_current = node.name.lower() == player.current_node.lower()
        is_dest    = mission_dest and node.name.lower() == mission_dest.lower()
        num_col  = DG if is_current else C
        name_col = DG if is_current else (Y if is_dest else W)
        cur_tag  = f"  {DG}(current){RST}" if is_current else ""
        dest_tag = f"  {Y}» deliver{RST}" if is_dest else ""
        write_at(MENU_TOP + 1 + idx, 1,
            f"    {num_col}[{RST}{name_col}{idx}{RST}{num_col}]{RST} {name_col}{node.name:<24}{RST} "
            f"{DG}{node.label:<18}{RST}"
            f"{crew_tag}{cur_tag}{dest_tag}")

    # Prompt on RES_BOT — styled key hints
    has_next = page < pg_cnt - 1
    has_prev = page > 0
    prompt = (
        f"    {DG}BBS to connect to: {C}[{RST}{W}1-{len(shown)}{RST}{C}]{RST}"
        + (f"  {DG}-{RST}  {C}[{RST}{W}N{RST}{C}]{RST} {DG}Next{RST}" if has_next else "")
        + (f"  {DG}-{RST}  {C}[{RST}{W}P{RST}{C}]{RST} {DG}Prev{RST}" if has_prev else "")
        + f"  {DG}-{RST}  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Quit{RST}"
    )
    write_at(RES_BOT, 1, prompt)

    draw_divider(STATUS_DIV)
    draw_status(player, player.bbs_name)

def screen_explore(player):
    """
    Explore screen layout — strictly 24 rows:
      Rows  1-14  Art zone (explore.ans or map.ans fallback)
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
    if not load_art("explore"):
        draw_art("map")

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
    # Clear Node and Info rows before each new scan so stale results
    # from the previous scan don't linger while the bar is running.
    move(EXP_NODE, 1); _out(ERASE_LINE); _out(f"   {DG}Node:{RST}")
    move(EXP_INFO, 1); _out(ERASE_LINE); _out(f"   {DG}Info:{RST}")

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


def screen_courier_board(player, mission, warn_turns=False):
    """Courier mission board screen."""
    screen_base("courier", player, player.bbs_name)

    diff_stars = "*" * mission.difficulty + " " * (3 - mission.difficulty)
    cargo  = mission.cargo_key.replace("_", " ")
    reward = mission.reward_summary()[:40]
    have   = player.get_resource(mission.cargo_key)

    write_at(MENU_TOP,     1, f"  {Y}{mission.label}{RST}  {R}[{diff_stars}]{RST}  {DG}costs {mission.turn_cost} turns{RST}")
    clear_line(DIV_3)

    write_at(RES_TOP,     1, f"  {W}{mission.desc[:70]}{RST}")
    write_at(RES_TOP + 2, 1, f"  {DG}Origin:{RST}   {C}{mission.origin[:24]}{RST}")
    write_at(RES_TOP + 3, 1, f"  {DG}Deliver:{RST}  {C}{mission.dest[:24]}{RST}")
    write_at(RES_TOP + 4, 1,
        f"  {DG}Cargo:{RST}   {Y}{mission.cargo_amt} {cargo}{RST}"
        f"  {DG}(you have {RST}{G if have >= mission.cargo_amt else R}{have}{RST}{DG}){RST}")
    write_at(RES_TOP + 5, 1, f"  {DG}Reward:{RST}  {G}{reward}{RST}")
    write_at(RES_TOP + 6, 1, f"  {DG}Expires:{RST} {R}end of day {mission.expires_day}{RST}")
    if warn_turns:
        write_at(RES_TOP + 7, 1,
            f"  {R}Warning: only {player.turns_remaining} turn(s) left — may not complete today.{RST}")

    draw_divider(RES_BOT - 1)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}A{RST}{C}]{RST} {DG}Accept{RST}  "
        f"{C}[{RST}{W}H{RST}{C}]{RST} {DG}Help{RST}  "
        f"{C}[{RST}{W}Q{RST}{C}]{RST} {DG}Decline{RST}")


def screen_courier_active(player, mission):
    """Active mission status — full screen."""
    screen_base("courier", player, player.bbs_name)

    diff_stars = "*" * mission.difficulty + " " * (3 - mission.difficulty)
    cargo = mission.cargo_key.replace("_", " ")

    write_at(MENU_TOP, 1,
        f"  {Y}{mission.label}{RST}  {R}[{diff_stars}]{RST}  {DG}ACTIVE{RST}")
    clear_line(DIV_3)

    write_at(RES_TOP,     1, f"  {W}{mission.desc[:70]}{RST}")
    write_at(RES_TOP + 2, 1, f"  {DG}Deliver to:{RST}  {C}{mission.dest}{RST}")
    write_at(RES_TOP + 3, 1, f"  {DG}Cargo:{RST}       {Y}{mission.cargo_amt} {cargo}{RST}")
    write_at(RES_TOP + 4, 1, f"  {DG}Reward:{RST}      {G}{mission.reward_summary()}{RST}")
    write_at(RES_TOP + 5, 1, f"  {DG}Expires:{RST}     {R}end of day {mission.expires_day}{RST}")
    write_at(RES_TOP + 6, 1,
        f"  {DG}You are at:{RST}  {W}{player.current_node}{RST}  "
        f"{DG}— travel to {C}{mission.dest}{DG} to deliver{RST}")

    draw_divider(RES_BOT - 1)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


def screen_courier_complete(player, mission):
    """Mission completion screen — shown after successful delivery."""
    screen_base("courier", player, player.bbs_name)

    diff_stars = "*" * mission.difficulty + " " * (3 - mission.difficulty)
    cargo = mission.cargo_key.replace("_", " ")

    write_at(MENU_TOP, 1,
        f"  {G}MISSION COMPLETE{RST}  {Y}{mission.label}{RST}  {R}[{diff_stars}]{RST}")
    clear_line(DIV_3)

    write_at(RES_TOP,     1, f"  {W}{mission.desc[:70]}{RST}")
    write_at(RES_TOP + 2, 1, f"  {DG}Delivered to:{RST}  {C}{mission.dest}{RST}")
    write_at(RES_TOP + 3, 1, f"  {DG}Cargo:{RST}         {Y}{mission.cargo_amt} {cargo}{RST}")
    write_at(RES_TOP + 5, 1, f"  {DG}Reward:{RST}")
    write_at(RES_TOP + 6, 1, f"  {G}{mission.reward_summary()}{RST}")
    write_at(RES_TOP + 8, 1, f"  {DG}A new mission will be available tomorrow.{RST}")

    draw_divider(RES_BOT - 1)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


def screen_courier_help(player):
    """Courier help screen — explains the mechanic."""
    screen_base("courier", player, player.bbs_name)
    clear_line(DIV_3)

    lines = [
        f"  {C}How courier jobs work:{RST}",
        "",
        f"  {DG}Each day a new job is posted. You supply the cargo from your own{RST}",
        f"  {DG}inventory and deliver it to the destination node for payment.{RST}",
        "",
        f"  {W}To accept:{RST} {DG}you need the listed cargo in your inventory.{RST}",
        f"  {DG}Accepting deducts the cargo and costs 1 turn.{RST}",
        "",
        f"  {W}To deliver:{RST} {DG}travel to the destination node. Delivery is{RST}",
        f"  {DG}automatic on arrival — no extra action needed.{RST}",
        "",
        f"  {R}Fail:{RST} {DG}if the day ends before delivery, cargo is returned{RST}",
        f"  {DG}but you lose 10 reputation.{RST}",
    ]
    for i, line in enumerate(lines):
        write_at(RES_TOP + i, 1, line)

    draw_divider(RES_BOT - 1)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


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
    """Trade post screen — 7 items directly under column headers."""
    from player import RESOURCE_NAMES
    screen_base("trade", player, player.bbs_name)
    draw_status(player, player.bbs_name, show_credits=True)

    # Column headers in MENU zone (row 10); rows 11-13 cleared
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"      {DG}{'#':<3} {'ITEM':<15} {'BUY':>7}  {'SELL':>6}  {'YOURS':>6}{RST}")
    for r in (MENU_TOP + 1, MENU_TOP + 2, DIV_3):
        move(r, 1); _out(ERASE_LINE)

    # Item list starts at MENU_TOP+1 (row 11) — directly under column headers
    trade_keys = ["floppy_disks", "source_code", "artwork",
                  "mod_music", "hardware", "tools", "beer"]
    for i, key in enumerate(trade_keys):
        row = MENU_TOP + 1 + i
        if row > RES_BOT - 2:
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
        _out(f"      {C}[{i+1}]{RST}{spec_tag}{col}{name:<15}{RST}"
             f"  {G}{buy:>6}c{RST}"
             f"  {R}{sell:>5}c{RST}"
             f"  {Y}{yours:>6}{RST}")

    # Divider between item list and prompt area
    draw_divider(RES_BOT - 1)

    # Default prompt on last row above status
    write_at(RES_BOT, 1,
        f"      {C}[{RST}{W}1-7{RST}{C}]{RST} {DG}Select {RST}"
        f" {C}[{RST}{W}B{RST}{C}]{RST} {DG}Buy {RST}"
        f" {C}[{RST}{W}S{RST}{C}]{RST} {DG}Sell {RST}"
        f" {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


# Row constants for produce screen — used by both ansi.py and game.py
PROD_LIST_TOP  = RES_TOP        # rows 14-18: the 5 demo options
PROD_DIVIDER   = RES_TOP + 5    # row 19: divider between list and detail
PROD_DETAIL    = RES_TOP + 6    # rows 20-21: confirmation detail
PROD_PROMPT    = RES_BOT        # row 22: [1-5]/[Y/Q] prompt


def screen_produce_animation(label, dkey, gained, failed, rival_name=None, rng=None):
    """
    Full-screen production animation.
    Steps overwrite each other on a single row to save space.
    Random humorous interruptions can occur between steps.
    """
    import random as _rnd
    if rng is None:
        rng = _rnd.Random()

    # Steps per demo type — each is (label, bar_colour, duration)
    # More complex demos have more steps and longer durations
    STEPS = {
        "cracktro" : [
            ("Firing up TASM    ", G,  1.2),
            ("Compiling         ", G,  1.5),
            ("Linking           ", G,  1.0),
            ("Crunching         ", C,  1.2),
        ],
        "4k"       : [
            ("Loading editor    ", G,  1.0),
            ("Compiling         ", G,  2.0),
            ("Linking           ", G,  1.5),
            ("Crunching to 4096b", C,  2.5),
            ("Size check        ", Y,  1.0),
        ],
        "64k"      : [
            ("Booting MSDOS     ", G,  1.0),
            ("Compiling         ", G,  2.5),
            ("Linking           ", G,  2.0),
            ("Running effects   ", G,  1.5),
            ("Crunching to 64kb ", C,  2.5),
            ("Size check        ", Y,  1.0),
        ],
        "musicdisk" : [
            ("Loading tracker   ", G,  1.0),
            ("Rendering MODs    ", G,  3.0),
            ("Encoding          ", G,  2.0),
            ("Building player   ", C,  1.5),
            ("Packing           ", C,  1.5),
        ],
        "demo"     : [
            ("Booting machine   ", G,  1.0),
            ("Compiling effects ", G,  3.5),
            ("Compiling music   ", G,  2.5),
            ("Linking           ", G,  2.0),
            ("Running test      ", Y,  2.0),
            ("Fixing last bug   ", R,  2.5),
            ("Crunching         ", C,  2.0),
            ("Final size check  ", Y,  1.0),
        ],
    }

    # Humorous interruptions — shown randomly between steps
    INTERRUPTIONS = [
        (f"{Y}Going for a 5K run first...{RST}",          2.5),
        (f"{C}Quickly checking mIRC...{RST}",             2.0),
        (f'{DG}LOAD "$",8,1{RST}',                      2.5),
        (f"{Y}Swapping floppy disk 3 of 7...{RST}",       2.0),
        (f"{DG}Waiting for 28.8k modem to connect...{RST}", 3.0),
        (f"{R}Out of beer. BRB.{RST}",                    2.5),
        (f"{C}Rebooting into DOS mode...{RST}",           2.0),
        (f"{DG}Pizza arrived. One moment.{RST}",          2.5),
        (f"{Y}Checking if Gates of Asgard is online...{RST}", 2.0),
        (f"{DG}FORMAT C: /Q ... just kidding.{RST}",      2.5),
        (f"{C}Defragging drive C...{RST}",                2.0),
        (f"{R}Segmentation fault (core dumped){RST}",     1.5),
        (f"{DG}Running SCANDISK first, just to be safe...{RST}", 2.5),
        (f"{Y}Arguing about tabs vs spaces on Usenet...{RST}", 2.0),
        (f"{C}IRQ conflict. Rearranging jumpers.{RST}",   2.5),
    ]

    steps = STEPS.get(dkey, STEPS["4k"])
    BAR_ROW   = RES_TOP + 2   # single row for all progress bars
    LOG_START = RES_TOP + 4   # scrolling log below the bar
    LOG_LINES = 4             # how many log lines to show
    log_buf   = []

    def add_log(text):
        """Add a line to the scrolling log area."""
        log_buf.append(text)
        shown = log_buf[-LOG_LINES:]
        for i in range(LOG_LINES):
            row = LOG_START + i
            if row >= RES_BOT - 1:
                break
            move(row, 1); _out(ERASE_LINE)
            if i < len(shown):
                _out(f"  {DG}>{RST} {shown[i]}")

    # Draw static chrome
    clear_screen()
    draw_art("hq")
    draw_divider(DIV_1)
    clear_zone(MENU_TOP, RES_BOT)
    draw_divider(STATUS_DIV)

    write_at(MENU_TOP,     1, f"  {C}PRODUCING:{RST} {W}{label}{RST}")
    write_at(MENU_TOP + 1, 1, f"  {DG}Firing up the toolchain. Do not disturb.{RST}")
    draw_divider(DIV_3)

    # Column header for the progress area
    write_at(RES_TOP, 1, f"  {DG}STEP                    PROGRESS{RST}")
    move(RES_TOP + 1, 1); _out(ERASE_LINE); _out(DG + b"\xc4".decode("cp437") * (SCREEN_W - 1) + RST)

    # Run steps — each overwrites the same BAR_ROW
    for step_idx, (step_label, step_col, step_dur) in enumerate(steps):
        # Random interruption — ~25% chance, not on first or last step
        if 0 < step_idx < len(steps) - 1 and rng.random() < 0.25:
            msg, delay = rng.choice(INTERRUPTIONS)
            add_log(msg)
            time.sleep(delay)

        progress_bar(BAR_ROW, 3, step_label, width=28, duration=step_dur, colour=step_col)
        add_log(f"{step_col}{step_label.strip()}{RST} {DG}... done.{RST}")
        time.sleep(0.15)

    time.sleep(0.4)

    # Result — written below the log
    result_row = LOG_START + LOG_LINES + 1
    if result_row > RES_BOT - 1:
        result_row = RES_BOT - 1

    move(result_row - 1, 1); _out(DG + b"\xc4".decode("cp437") * (SCREEN_W - 1) + RST)

    if failed:
        write_at(result_row, 1, f"  {R}*** PRODUCTION FAILED ***{RST}")
        typewriter(result_row + 1 if result_row + 1 <= RES_BOT else result_row,
                   3, "Compiler errors. Resources wasted. The scene saw nothing.",
                   colour=R, delay=0.03)
    else:
        write_at(result_row, 1, f"  {Y}*** {label.upper()} RELEASED! ***{RST}")
        typewriter(result_row + 1 if result_row + 1 <= RES_BOT else result_row,
                   3, f"The scene notices. +{gained} reputation earned.",
                   colour=G, delay=0.03)
        if rival_name and result_row + 2 <= RES_BOT:
            time.sleep(0.4)
            write_at(result_row + 2, 1,
                f"  {DG}{rival_name} clocks your release. Respect.{RST}")

    time.sleep(0.5)

    if not failed:
        # Upload sequence — dial a release board and upload
        _produce_upload_sequence(label, dkey, rng)
    else:
        write_at(RES_BOT, 1, f"  {DG}Press any key to continue...{RST}")
        show_cursor()
        io = _sio.get_io()
        if io:
            io.getkey()
        hide_cursor()


# Release boards to dial into — mix of real and fictional BBS names
# Cellfi.sh BBS is always the home board — always dialled first
_HOME_BOARD = ("Cellfi.sh BBS", "+47-32-75-42-50", "Drammen, NO")

_RELEASE_BOARDS = [
    ("The Humble Origins",   "+1-312-555-0142",  "Chicago, US"),
    ("Gates of Asgard",      "+47-22-555-0187",  "Oslo, NO"),
    ("Speed of Light",       "+49-30-555-0193",  "Berlin, DE"),
    ("Apocalypse Now",       "+1-415-555-0167",  "San Francisco, US"),
    ("Metal ANet",           "+44-171-555-0134", "London, UK"),
    ("The Underground",      "+1-212-555-0178",  "New York, US"),
    ("Point of No Return",   "+358-9-555-0156",  "Helsinki, FI"),
    ("XTC Systems",          "+46-8-555-0145",   "Stockholm, SE"),
    ("Cloud Nine Elite",     "+1-213-555-0189",  "Los Angeles, US"),
    ("Southern Comfort",     "+61-2-555-0123",   "Sydney, AU"),
    ("The Void",             "+31-20-555-0167",  "Amsterdam, NL"),
    ("Violent Playground",   "+1-416-555-0134",  "Toronto, CA"),
]

# Modem connect strings
_CONNECT_STRINGS = [
    "CONNECT 2400",
    "CONNECT 9600",
    "CONNECT 14400",
    "CONNECT 28800",
    "CONNECT 33600",
]

# Virus scanner results — always clean (it's your release after all)
_VIRUS_SCANNERS = [
    ("McAfee VirusScan 2.x",   "Scanning...  No viruses found."),
    ("F-PROT 2.24",            "No infection found."),
    ("TBAV 6.xx",              "No viruses or trojans detected."),
    ("NAV 3.0",                "Norton AntiVirus: Item is clean."),
    ("SCAN 115",               "No viruses detected."),
]

# Sysop reactions — normal, enthusiastic, and l33tsp34k variants
_SYSOP_REACTIONS = [
    # Normal
    "Listed. Nice work.",
    "File received. Added to incoming.",
    "Got it. Will be in the next NFO.",
    "Cheers. Board will spread it tonight.",
    "Received. The scene will know by morning.",
    "Clean transfer. You are on the board.",
    "Verified. +ratio credited.",
    "Good stuff. Spreading to affiliates now.",
    "Uploaded. Sysop verified. You are legit.",
    # Enthusiastic
    "HOLY COW this is good. Listed immediately.",
    "Best release this week. Bar none.",
    "Already getting requests for this one.",
    "This one is going everywhere. Well done.",
    # L33tsp34k
    "n1c3 r3l34s3 d00d!! 4dd3d 2 th3 b04rd!!",
    "0mg th1s 1s s1ck!! l1st3d 4s 3l1t3!!",
    "ph34r th3 cr3w!! r4t10 +50 cr3d1t3d!!",
    "w00t!! f1l3_1d.d1z ch3ck3d 0ut!! l33t!!",
    "r3sp3ct d00d. spr34d1ng 2 4ll 4ff1l14t3z.",
]


def _produce_upload_sequence(label, dkey, rng):
    """
    Post-production upload sequence.
    Always dials Cellfi.sh BBS first (home board), then one random affiliate.
    Includes virus scan and file_id.diz verification steps.
    """
    # Home board is always first, then a random affiliate
    boards_to_dial = [_HOME_BOARD, rng.choice(_RELEASE_BOARDS)]
    sysop_reply  = rng.choice(_SYSOP_REACTIONS)
    av_name, av_result = rng.choice(_VIRUS_SCANNERS)
    connect      = rng.choice(_CONNECT_STRINGS)

    # File size and name by type
    sizes = {
        "cracktro" : rng.randint(2,   12),
        "4k"       : 4,
        "64k"      : 64,
        "musicdisk": rng.randint(120, 400),
        "demo"     : rng.randint(400, 1200),
    }
    kb       = sizes.get(dkey, rng.randint(10, 100))
    ext      = rng.choice([".zip", ".lha", ".arj"])
    filename = (label.lower().replace(" ", "")[:12]) + ext

    # DIZ line — what shows in the file listing
    diz_lines = [
        f"{label} by Cellfish",
        f"Released {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][rng.randint(0,11)]} 199{rng.randint(2,9)}",
        "Spread it.",
    ]

    def _dial_board(board_name, phone, location, is_home):
        """
        Dial one board and upload.
        The area between DIV_3 and RES_BOT acts as a scrolling terminal —
        new lines appear at the bottom, old ones scroll up and off the top.
        A fixed progress bar row sits just above RES_BOT for scan/upload bars.
        """
        # Terminal window: DIV_3+1 (row 14) .. RES_BOT-2 (row 20) = 7 visible lines
        # Row RES_BOT-1 (row 21) = dedicated progress bar row
        # Row RES_BOT   (row 22) = status line
        TERM_TOP  = RES_TOP        # row 14 — top of scrolling area
        TERM_BOT  = RES_BOT - 2   # row 20 — bottom of scrolling area
        BAR_ROW   = RES_BOT - 1   # row 21 — progress bar (fixed)
        STAT_ROW  = RES_BOT        # row 22 — status

        TERM_H = TERM_BOT - TERM_TOP + 1   # 7 lines

        term_buf = []   # list of (text, colour) tuples

        def _redraw_terminal():
            """Redraw the visible terminal lines from the buffer."""
            shown = term_buf[-TERM_H:]
            for i in range(TERM_H):
                row = TERM_TOP + i
                move(row, 1); _out(ERASE_LINE)
                if i < len(shown):
                    txt, col = shown[i]
                    _out(f"  {col}{txt}{RST}")

        def log(text, colour=DG, delay=0.4):
            """Append a line to the scrolling terminal and redraw."""
            term_buf.append((text, colour))
            _redraw_terminal()
            if delay:
                time.sleep(delay)

        def bar(label_text, duration, colour=C, width=22):
            """Run a progress bar on BAR_ROW (doesn't scroll)."""
            progress_bar(BAR_ROW, 3, f"{label_text:<20}", width=width,
                         duration=duration, colour=colour)

        # ── Draw chrome ──────────────────────────────────────────────
        clear_screen()
        draw_art("hq")
        draw_divider(DIV_1)
        clear_zone(MENU_TOP, RES_BOT)
        draw_divider(STATUS_DIV)

        tag = "HOME BOARD" if is_home else "AFFILIATE"
        write_at(MENU_TOP,     1, f"  {C}UPLOADING TO {tag}:{RST} {W}{board_name}{RST}")
        write_at(MENU_TOP + 1, 1, f"  {DG}{location}{RST}")
        draw_divider(DIV_3)

        # Clear bar and status rows
        move(BAR_ROW,  1); _out(ERASE_LINE)
        move(STAT_ROW, 1); _out(ERASE_LINE)

        # ── Modem init ───────────────────────────────────────────────
        log("ATZ", W, 0.3)
        log("OK", G, 0.4)

        # Dial with digits typed out one by one — directly on terminal bottom
        term_buf.append((f"ATDT {phone}", W))
        _redraw_terminal()
        # Now overwrite the last terminal line with the animated dial
        last_row = TERM_TOP + min(len(term_buf) - 1, TERM_H - 1)
        move(last_row, 1); _out(ERASE_LINE)
        _out(f"  {W}ATDT {phone}  {DG}")
        for digit in phone.replace("+","").replace("-",""):
            _out(digit)
            time.sleep(0.09)
        _out(RST)
        time.sleep(0.8)

        log("RINGING...", DG, 1.0)
        log(f"{connect}", G, 0.5)
        log(f"Connected to {board_name}", C, 0.6)
        log("Logging in...", DG, 0.6)
        log("Upload area. Ready.", DG, 0.5)

        # ── Virus scan ───────────────────────────────────────────────
        log(f"Running {av_name}...", DG, 0.3)
        bar(av_name[:20], duration=2.0, colour=Y)
        log(f"{av_result}", G, 0.5)

        # ── FILE_ID.DIZ ──────────────────────────────────────────────
        log("Checking FILE_ID.DIZ...", DG, 0.5)
        log("FILE_ID.DIZ found:", DG, 0.3)
        for diz in diz_lines:
            log(f"  {diz}", W, 0.3)

        # ── Upload ───────────────────────────────────────────────────
        log(f"Sending {filename} ({kb}kb)...", W, 0.3)
        bar(f"Uploading {filename[:14]}", duration=max(2.0, kb * 0.018), colour=C)
        log(f"Transfer OK. {kb}kb. CRC verified.", G, 0.5)

        if is_home:
            log(f'Sysop: "{sysop_reply}"', Y, 0.6)

        log("NO CARRIER", R, 0.4)
        time.sleep(0.6)

    # Dial both boards
    for i, (bname, bphone, bloc) in enumerate(boards_to_dial):
        _dial_board(bname, bphone, bloc, is_home=(i == 0))
        if i < len(boards_to_dial) - 1:
            write_at(RES_BOT, 1, f"  {DG}Dialling next board...{RST}")
            time.sleep(1.0)

    # Final summary screen
    clear_screen()
    draw_art("hq")
    draw_divider(DIV_1)
    clear_zone(MENU_TOP, RES_BOT)
    draw_divider(STATUS_DIV)

    write_at(MENU_TOP, 1, f"  {Y}RELEASE COMPLETE{RST}")
    draw_divider(DIV_3)
    write_at(RES_TOP,     1, f"  {W}{label}{RST}")
    write_at(RES_TOP + 1, 1, f"  {DG}File:     {RST}{C}{filename}{RST}  {DG}({kb}kb){RST}")
    write_at(RES_TOP + 2, 1, f"  {DG}Listed on:{RST} {G}{boards_to_dial[0][0]}{RST}")
    write_at(RES_TOP + 3, 1, f"  {DG}Spread to:{RST} {G}{boards_to_dial[1][0]}{RST}")
    write_at(RES_TOP + 5, 1, f"  {Y}{sysop_reply}{RST}")
    move(RES_BOT - 1, 1); _out(DG + b"\xc4".decode("cp437") * (SCREEN_W - 1) + RST)
    write_at(RES_BOT, 1, f"  {DG}Press any key to continue...{RST}")

    show_cursor()
    io = _sio.get_io()
    if io:
        io.getkey()
    hide_cursor()


def screen_produce(player, detail_lines=None, prompt=None):
    """Demo production screen — resources top, list middle, detail+prompt bottom."""
    screen_base("produce", player, player.bbs_name)

    demos = [
        ("1", "Cracktro",  {"source_code": 50,  "artwork": 20},         40,  5),
        ("2", "4K Intro",  {"source_code": 120, "artwork": 40},        120, 10),
        ("3", "64K Intro", {"source_code": 200, "artwork": 80},        280, 15),
        ("4", "Musicdisk", {"source_code": 80,  "mod_music": 300},     200, 10),
        ("5", "Full Demo", {"source_code": 400, "artwork": 200,
                            "mod_music": 150},                          600, 20),
    ]

    # MENU zone — resources (row 10), column headers (row 11)
    # Overwrite DIV_3 (row 13) with the list header divider so there's only one
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {DG}src:{RST}{W}{player.source_code:>5}{RST}  "
         f"{DG}art:{RST}{W}{player.artwork:>5}{RST}  "
         f"{DG}mod:{RST}{W}{player.mod_music:>5}{RST}  "
         f"{DG}turns: 3  rep:{RST}{C}{player.reputation:>5}{RST}")
    move(MENU_TOP + 1, 1); _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'TYPE':<13}{'COST':<28}{'REP':>5}  {'FAIL%':>5}{RST}")
    # Use MENU_TOP+2 (row 12) as divider and clear DIV_3 (row 13) to remove double line
    move(MENU_TOP + 2, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)
    move(DIV_3, 1); _out(ERASE_LINE)

    # RES zone — demo list (rows 14-18)
    for i, (key, label, costs, rep, fail_pct) in enumerate(demos):
        row = PROD_LIST_TOP + i
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

    # Divider below list (row 19)
    move(PROD_DIVIDER, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)

    # Detail area (rows 20-21) — filled by game.py after selection, blank by default
    for row in range(PROD_DETAIL, PROD_PROMPT):
        move(row, 1); _out(ERASE_LINE)
    if detail_lines:
        for i, line in enumerate(detail_lines[:2]):
            move(PROD_DETAIL + i, 1); _out(ERASE_LINE); _out(line)

    # Prompt row (row 22)
    move(PROD_PROMPT, 1); _out(ERASE_LINE)
    if prompt:
        _out(prompt)
    else:
        _out(f"  {C}[{RST}{W}1-5{RST}{C}]{RST} {DG}Select{RST}  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


def screen_raid_targets(player, targets):
    """Target selection screen — styled key list, prompt at RES_BOT."""
    screen_base("raid", player, player.bbs_name)
    write_at(MENU_TOP, 1,
        f"  {R}RAID{RST}  {DG}Select a target — costs 3 turns{RST}")
    write_at(MENU_TOP + 1, 1,
        f"  {DG}     {'CREW':<17}{'TYPE':<11}{'LOCATION':<22}AGG{RST}")

    shown = targets[:7]
    for i, (crew, node) in enumerate(shown):
        agg_col = R if crew.aggression == 3 else (Y if crew.aggression == 2 else DG)
        agg_str = "!!!" if crew.aggression == 3 else ("!!" if crew.aggression == 2 else "!")
        name_col = R if crew.aggression == 3 else (Y if crew.aggression == 2 else W)
        tag = getattr(crew, 'personality_tag', crew.style.upper())
        write_at(RES_TOP + i, 1,
            f"  {C}[{RST}{W}{i+1}{RST}{C}]{RST} "
            f"{name_col}{crew.name:<16}{RST}"
            f"{DG}{tag:<11}{RST}"
            f"{B}{node.name:<22}{RST}"
            f"{agg_col}{agg_str}{RST}")
    if len(targets) > 7:
        write_at(RES_TOP + 7, 1, f"  {DG}({len(targets) - 7} more targets not shown){RST}")

    draw_divider(RES_BOT - 1)
    n = min(len(shown), 9)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}1-{n}{RST}{C}]{RST} {DG}Select{RST}  "
        f"{C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


def screen_raid(player, npc_crew, taunt=""):
    """Raid / combat tactic screen."""
    screen_base("raid", player, player.bbs_name)

    agg_col = R if npc_crew.aggression == 3 else (Y if npc_crew.aggression == 2 else DG)
    agg_str = "!!!" if npc_crew.aggression == 3 else ("!!" if npc_crew.aggression == 2 else "!")

    write_at(MENU_TOP, 1,
        f"  {DG}RAIDING {RST}{R}{npc_crew.name:<20}{RST}"
        f"  {agg_col}{agg_str}{RST}"
        f"  {DG}Str:{RST} {R}{npc_crew.strength}{RST}"
        f"  {DG}Def:{RST} {B}{npc_crew.defense}{RST}")

    # Strength and defense bars side by side in MENU zone rows 11-12
    # Player at col 2 (cols 2-39), enemy at col 42 (cols 42-79)
    combat_bar(MENU_TOP + 1, 2,  "Your Str ",
               player.tools * 2 + 20, 100, colour=G)
    combat_bar(MENU_TOP + 1, 42, "Their Str",
               npc_crew.strength,     100, colour=R)
    combat_bar(MENU_TOP + 2, 2,  "Your Def ",
               player.defense,        100, colour=B)
    combat_bar(MENU_TOP + 2, 42, "Their Def",
               npc_crew.defense,      100, colour=R)

    loot_c = npc_crew.resources.get("phone_credits", 0) // 3
    loot_d = npc_crew.resources.get("floppy_disks",  0) // 3
    loot_s = npc_crew.resources.get("source_code",   0) // 3
    write_at(RES_TOP, 1,
        f"  {DG}Potential loot: {RST}"
        f"{Y}~{loot_c}c{RST}  "
        f"{W}~{loot_d} disks{RST}  "
        f"{C}~{loot_s} source{RST}")
    if taunt:
        write_at(RES_TOP + 2, 1, f"  {DG}\"{taunt}\"{RST}")

    draw_divider(RES_BOT - 1)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}A{RST}{C}]{RST} {DG}Assault{RST}  "
        f"{C}[{RST}{W}S{RST}{C}]{RST} {DG}Sneak{RST}  "
        f"{C}[{RST}{W}H{RST}{C}]{RST} {DG}Hit&run{RST}  "
        f"{C}[{RST}{W}Q{RST}{C}]{RST} {DG}Retreat{RST}")


def screen_oneliners(entries, player=None):
    """Oneliner wall — entries start immediately after DIV_1, prompt at RES_BOT."""
    screen_base("oneliners", player, player.bbs_name if player else "")
    clear_line(DIV_3)  # remove the mid-screen divider screen_base draws

    # Fill from MENU_TOP through RES zone — 11 rows available (10-20)
    all_rows = list(range(MENU_TOP, RES_BOT - 1))
    shown = entries[:len(all_rows)]
    for i, e in enumerate(shown):
        write_at(all_rows[i], 1,
            f"  {C}{e['handle']:<16}{RST}"
            f"{W}{e['text'][:60]}{RST}")

    draw_divider(RES_BOT - 1)
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}W{RST}{C}]{RST} {DG}Write{RST}  "
        f"{C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")


def screen_hof(entries, player_handle, player=None):
    """Hall of Fame screen — uses full RES zone for up to 9 entries."""
    screen_base("hof", player, player.bbs_name if player else "")

    # Header in MENU zone
    move(MENU_TOP, 1); _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'HANDLE':<14}{'CREW':<20}{'BBS':<16}{'SCORE':>8}{'  DAY':>6}{RST}")
    move(MENU_TOP + 1, 1)
    _out(DG); _out(b"\xc4" * (SCREEN_W - 1)); _out(RST)
    clear_line(MENU_TOP + 2)
    clear_line(DIV_3)

    # Entries start at MENU_TOP + 2 — directly under the divider
    for i, e in enumerate(entries[:9]):
        row = MENU_TOP + 2 + i
        if row > RES_BOT:
            break
        is_player = e["handle"].upper() == player_handle.upper()
        name_col  = G if is_player else G
        rank_col  = Y if i == 0 else (C if i == 1 else (W if i < 5 else DG))
        move(row, 1); _out(ERASE_LINE)
        _out(f"  {rank_col}{str(i+1)+'.':<4}{RST}"
             f"{name_col}{e['handle']:<14}{RST}"
             f"{DG}{e['crew']:<20}{RST}"
             f"{DG}{e['bbs'][:15]:<16}{RST}"
             f"{Y}{e['score']:>8}{RST}"
             f"{DG}{str(e.get('day','?')):>6}{RST}")

    # Prompt
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Quit{RST}")

    draw_divider(STATUS_DIV)
    if player: draw_status(player, player.bbs_name)

    # Prompt
    write_at(RES_BOT, 1,
        f"  {C}[{RST}{W}Q{RST}{C}]{RST} {DG}Back{RST}")

    draw_divider(STATUS_DIV)
    if player: draw_status(player, player.bbs_name)


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