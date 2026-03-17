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
    """
    HQ screen. Menu lives in MENU_TOP..MENU_BOT (rows 10-12) so the
    result zone (rows 14-22) never overwrites it when result() is called.
    """
    clear_screen()
    draw_art("hq")
    draw_divider(DIV_1)          # row 9

    # Menu in rows 10-12 (MENU_TOP..MENU_BOT) -- safe from result() redraws
    actions = [
        ("[E] Explore", "[T] Travel",   "[P] Produce"),
        ("[R] Raid",    "[D] Defend",   "[B] Trade"),
        ("[M] Messages","[S] Scores",   "[Q] Quit/Save"),
    ]
    col_starts = [3, 29, 55]
    for r_idx, row_items in enumerate(actions):
        row = MENU_TOP + r_idx
        for col, item in zip(col_starts, row_items):
            # Split "[X]" from label
            bracket_end = item.index("]") + 1
            key_part   = item[:bracket_end]
            label_part = item[bracket_end:]
            move(row, col)
            _out(f"{C}{key_part}{RST}{W}{label_part}{RST}")

    draw_divider(DIV_3)          # row 13
    clear_zone(RES_TOP, RES_BOT) # rows 14-22
    draw_divider(STATUS_DIV)     # row 23
    draw_status(player, player.bbs_name)
    global _result_buf
    _result_buf = [""] * (RES_BOT - RES_TOP + 1)

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
    Explore screen. Uses screen_base() so the result zone is properly
    cleared, _result_buf is reset, and result() output has full space.
    """
    screen_base("map", player, player.bbs_name,
                cmd_hint="[X] Scan network   [Q] Back")

# ---------------------------------------------------------------------------
# Animation primitives (restored)
# ---------------------------------------------------------------------------

SPINNER_FRAMES = ["/", "-", "\\", "|"]


def spinner(row, col, message, duration=1.5, colour=None):
    if colour is None: colour = C
    hide_cursor()
    end = time.time() + duration
    i   = 0
    while time.time() < end:
        frame = SPINNER_FRAMES[i % 4]
        write_at_no_clear(row, col, f"{colour}[{frame}]{RST} {DG}{message}{RST}")
        time.sleep(0.1)
        i += 1
    move(row, col)
    _out(" " * (len(message) + 5))


def dots(row, col, message, count=8, delay=0.15, colour=None):
    if colour is None: colour = DG
    hide_cursor()
    for i in range(count + 1):
        write_at_no_clear(row, col,
                          f"{colour}{message}{'.' * i}{RST}"
                          + " " * (count - i))
        time.sleep(delay)


def progress_bar(row, col, label, width=24, duration=1.2, colour=None):
    if colour is None: colour = G
    hide_cursor()
    for i in range(width + 1):
        filled = "\u2588" * i
        empty  = "\u2591" * (width - i)
        pct    = int((i / width) * 100)
        bar    = f"{colour}[{filled}{empty}]{RST} {W}{pct:>3}%{RST}"
        write_at_no_clear(row, col, f"{DG}{label} {RST}{bar}")
        time.sleep(duration / width)


def typewriter(row, col, text, colour=None, delay=0.04):
    if colour is None: colour = W
    hide_cursor()
    for i in range(len(text) + 1):
        move(row, col)
        _out(colour + text[:i] + RST + " ")
        time.sleep(delay)


def combat_bar(row, col, label, value, max_val, width=20, colour=None):
    if colour is None: colour = G
    pct    = max(0, min(1.0, value / max_val)) if max_val > 0 else 0
    filled = int(pct * width)
    bar    = "\u2588" * filled + "\u2591" * (width - filled)
    write_at_no_clear(row, col,
                      f"{DG}{label:<12}{RST}{colour}[{bar}]{RST}"
                      f" {W}{value:>3}{RST}")


def animate_combat_bars(row, player_power, enemy_power):
    hide_cursor()
    max_p = 100
    steps = 20
    for i in range(steps + 1):
        pp = int((i / steps) * player_power)
        ep = int((i / steps) * enemy_power)
        combat_bar(row,     2, "Your crew",  pp, max_p, colour=G)
        combat_bar(row + 1, 2, "Enemy crew", ep, max_p, colour=R)
        time.sleep(0.05)
    time.sleep(0.3)


# ---------------------------------------------------------------------------
# Screen builders — trade, produce, raid, messages, hof, party, game over
# ---------------------------------------------------------------------------

def screen_trade(player, node):
    from player import RESOURCE_NAMES
    screen_base("trade", player, player.bbs_name,
                cmd_hint="[1-7] Select  [B] Buy  [S] Sell  [Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}LOCATION {RST}{B}{node.name}{RST}"
         f"  {DG}·{RST}  {DG}YOUR CREDITS {RST}{Y}{player.phone_credits}{RST}")

    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'ITEM':<16}  {'BUY':>7}  {'SELL':>7}  {'YOURS':>6}{RST}")

    trade_keys = ["floppy_disks", "source_code", "artwork",
                  "mod_music", "hardware", "tools", "beer"]
    for i, key in enumerate(trade_keys):
        row = MENU_TOP + 2 + i
        if row >= STATUS_DIV:
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
             f"  {Y}{yours:>6}{RST}")


def screen_produce(player):
    screen_base("produce", player, player.bbs_name,
                cmd_hint="[1-5] Select  [Q] Back")

    demos = [
        ("1", "Cracktro",  {"source_code": 50,  "artwork": 20},       40),
        ("2", "4K Intro",  {"source_code": 120, "artwork": 40},       120),
        ("3", "64K Intro", {"source_code": 200, "artwork": 80},       280),
        ("4", "Musicdisk", {"source_code": 80,  "mod_music": 300},    200),
        ("5", "Full Demo", {"source_code": 400, "artwork": 200,
                            "mod_music": 150},                         600),
    ]

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'':4}{'TYPE':<16}{'COST':<32}{'REP':>8}{RST}")

    for i, (key, label, costs, rep) in enumerate(demos):
        row = MENU_TOP + 1 + i
        if row >= STATUS_DIV:
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

    # Resource hint row
    hint_row = MENU_TOP + len(demos) + 2
    if hint_row < STATUS_DIV:
        move(hint_row, 1)
        _out(ERASE_LINE)
        _out(f"  {DG}src:{RST}{W}{player.source_code:>5}{RST}  "
             f"{DG}art:{RST}{W}{player.artwork:>5}{RST}  "
             f"{DG}mod:{RST}{W}{player.mod_music:>5}{RST}  "
             f"{DG}rep:{RST}{C}{player.reputation:>5}{RST}")


def screen_raid(player, npc_crew):
    screen_base("raid", player, player.bbs_name,
                cmd_hint="[A] Assault  [S] Sneak  [H] Hit&run  [Q] Retreat")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}RAIDING {RST}{R}{npc_crew.name}{RST}")

    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'YOUR CREW':<38}{'ENEMY CREW'}{RST}")

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
    row = MENU_TOP + 5
    if row < STATUS_DIV:
        move(row, 1)
        _out(ERASE_LINE)
        _out(f"  {DG}Potential loot: {RST}"
             f"{Y}~{loot_c} credits{RST}  "
             f"{W}~{loot_d} disks{RST}")


def screen_messages(messages, player=None):
    screen_base("messages", player, player.bbs_name if player else "",
                cmd_hint="[Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'':3}{'FROM':<18}{'SUBJECT':<34}{'DAY'}{RST}")
    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(DG + "\xb7" * SCREEN_W + RST)

    row = MENU_TOP + 2
    for msg in (messages or []):
        if row >= STATUS_DIV:
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
    screen_base("hof", player, player.bbs_name if player else "",
                cmd_hint="[Q] Back")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{'#':<4}{'HANDLE':<16}{'CREW':<22}"
         f"{'BBS':<18}{'SCORE':>8}{RST}")
    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(DG + "\xb7" * SCREEN_W + RST)

    row = MENU_TOP + 2
    for i, e in enumerate(entries[:5]):
        if row >= STATUS_DIV:
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
    from world import COMPO_DEFS
    screen_base("party", player, player.bbs_name,
                cmd_hint=f"[1-{len(party.compos)}] Compo  [D] Bar  [R] Rave  [Q] Leave")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {Y}{party.name}{RST}  {DG}\xb7{RST}  {DG}{party.location}{RST}")
    move(MENU_TOP + 1, 1)
    _out(ERASE_LINE)
    _out(f"  {DG}{party.flavour}{RST}")

    row = MENU_TOP + 2
    for i, key in enumerate(party.compos):
        if row >= STATUS_DIV:
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
    screen_base("gameover")

    move(MENU_TOP, 1)
    _out(ERASE_LINE)
    _out(f"  {Y}GAME OVER \u2014 YOUR LEGACY IS WRITTEN{RST}")

    stats = [
        ("Handle",           player.handle,              W),
        ("Crew",             player.crew_name,            W),
        ("Days played",      str(player.day),             W),
        ("Final score",      str(player.total_score),     Y),
        ("Hall of Fame",     f"#{rank}" if rank else "unranked", G),
        ("Demos produced",   str(player.demos_produced),  W),
        ("Raids won",        str(player.raids_won),       W),
        ("Parties attended", str(player.parties_attended), W),
        ("Beers drunk",      str(player.beers_drunk),     Y),
    ]
    row = MENU_TOP + 1
    for label, value, col in stats:
        if row >= STATUS_DIV:
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
