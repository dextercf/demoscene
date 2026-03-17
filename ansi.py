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

SCREEN_W, SCREEN_H = 80, 24
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
    if row >= STATUS_DIV: return
    move(row, col)
    _out(ERASE_LINE)
    out = colour + text + (RST if reset and colour else "")
    _out(_truncate_ansi(out, SCREEN_W - col + 1))

def write_at_no_clear(row, col, text, colour="", reset=True):
    if row >= STATUS_DIV: return
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

def draw_divider(row, char="─", colour=DG):
    move(row, 1)
    _out(ERASE_LINE); _out(colour + char * SCREEN_W + RST)

def draw_status(player, bbs_name="", node=1):
    move(STATUS, 1)
    _out(ERASE_LINE)
    left = (f" {DG}CREW {RST}{W}{player.crew_name}{RST}"
            f"  {DG}·{RST}  " f"{DG}HANDLE {RST}{G}{player.handle}{RST}"
            f"  {DG}·{RST}  " f"{DG}TURNS {RST}{Y}{player.turns_remaining}{DG}/10{RST}"
            f"  {DG}·{RST}  " f"{DG}DAY {RST}{W}{player.day}{RST}")
    right = f"{DG}NODE {node}{RST} "
    left_plain = f" CREW {player.crew_name}  ·  HANDLE {player.handle}  ·  TURNS {player.turns_remaining}/10  ·  DAY {player.day}"
    right_plain = f"NODE {node} "
    pad = SCREEN_W - len(left_plain) - len(right_plain)
    _out(left + " " * max(0, pad) + right)

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
        _out(DG + "─" * (pad // 2) + RST + hint + DG + "─" * (pad - pad // 2) + RST)
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
    clear_screen(); draw_art("hq"); draw_divider(9); clear_zone(10, 22)
    rows = [
        [("[E]", "Explore"), ("[T]", "Travel"), ("[P]", "Produce")],
        [("[R]", "Raid"),    ("[D]", "Defend"), ("[B]", "Trade")],
        [("[M]", "Messages"), ("[S]", "Scores"), ("[Q]", "Quit / save")],
    ]
    col_starts, start_row = [3, 30, 57], 19
    for r_idx, items in enumerate(rows):
        row = start_row + r_idx
        for col, (hk, lbl) in zip(col_starts, items):
            move(row, col); _out(f"{C}{hk}{RST} {W}{lbl}{RST}")
    draw_divider(18); draw_divider(23); draw_status(player, player.bbs_name)

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
    clear_screen(); draw_art("map"); draw_divider(11); clear_zone(12, 22)
    write_at(13, 1, f"  {DG}[X] Scan network   [Q] Back{RST}")
    draw_divider(14); draw_divider(23); draw_status(player, player.bbs_name)