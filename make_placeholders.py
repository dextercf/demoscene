"""
make_placeholders.py  —  v2  (nicer placeholders)
Generates visually rich placeholder .ans files for:
  Demoscene: The Exploration of Art  —  A Cellfish Production

Each file: 80 cols wide, 8 rows tall, CP437 + ANSI colour, SAUCE record.
Run from C:\demoscene:   python make_placeholders.py
"""

import os, struct, datetime

OUT_DIR = os.path.join(os.path.dirname(__file__), "art")
ESC = "\x1b"

# ── Colour helpers ────────────────────────────────────────────────────────────
def fg(n): return f"{ESC}[{n}m"
def bg(n): return f"{ESC}[{n}m"

RST  = f"{ESC}[0m";  BLD = f"{ESC}[1m"
K    = fg(30);  R  = fg(31);  G  = fg(32);  Y  = fg(33)
B    = fg(34);  M  = fg(35);  C  = fg(36);  W  = fg(37)
BK   = fg(90);  BR = fg(91);  BG = fg(92);  BY = fg(93)
BB   = fg(94);  BM = fg(95);  BC = fg(96);  BW = fg(97)
# backgrounds
BGK  = bg(40);  BGR= bg(41);  BGG= bg(42);  BGY= bg(43)
BGB  = bg(44);  BGM= bg(45);  BGC= bg(46);  BGWH= bg(47)

# ── CP437 characters ──────────────────────────────────────────────────────────
SH   = "\xc4"   # ─   single horizontal
SV   = "\xb3"   # │   single vertical
STL  = "\xda"   # ┌
STR  = "\xbf"   # ┐
SBL  = "\xc0"   # └
SBR  = "\xd9"   # ┘
DH   = "\xcd"   # ═   double horizontal
DV   = "\xba"   # ║   double vertical
DTL  = "\xc9"   # ╔
DTR  = "\xbb"   # ╗
DBL  = "\xc8"   # ╚
DBR  = "\xbc"   # ╝
# mixed
MRT  = "\xb9"   # ╣   double-V + single-H right-T
MLT  = "\xcc"   # ╠   double-V + single-H left-T
# blocks
FB   = "\xdb"   # █   full block
HB   = "\xb2"   # ▓   dark shade
MB   = "\xb1"   # ▒   medium shade
LB   = "\xb0"   # ░   light shade
LH   = "\xdf"   # ▀   upper half
LO   = "\xdc"   # ▄   lower half
# misc
BULL = "\xf9"   # ·   bullet
DIAm = "\x04"   # ♦   diamond
STAR = "\x0f"   # ☼   sun/star
SPADE= "\x06"   # ♠
CLUB = "\x05"   # ♣

def col(text, *codes):
    return "".join(codes) + text + RST

def row(text):
    """Append CR+LF to a row string."""
    return text + "\r\n"

def pad(text, visible_len, width=80):
    """Right-pad with spaces so total visible width == width."""
    return text + " " * max(0, width - visible_len)

def centre_plain(text, width=80):
    p = max(0, width - len(text))
    return " " * (p // 2) + text + " " * (p - p // 2)

# ── SAUCE record ─────────────────────────────────────────────────────────────
def make_sauce(title="Placeholder", author="Cellfish", width=80, height=8):
    date  = datetime.date.today().strftime("%Y%m%d").encode("ascii")
    rec   = b"SAUCE00"
    rec  += title.encode("ascii")[:35].ljust(35)
    rec  += author.encode("ascii")[:20].ljust(20)
    rec  += b"Cellfish            "   # group (20 bytes)
    rec  += date
    rec  += struct.pack("<I", 0)
    rec  += bytes([1, 1])             # datatype=char, filetype=ANSI
    rec  += struct.pack("<HH", width, height)
    rec  += bytes([0, 0, 0])
    rec  += b" " * 22
    return rec

def write_ans(filename, lines, title="Placeholder"):
    path    = os.path.join(OUT_DIR, filename)
    content = "".join(lines)
    data    = content.encode("cp437", errors="replace")
    data   += b"\x1a" + make_sauce(title=title, height=len(lines))
    with open(path, "wb") as f:
        f.write(data)
    print(f"  {filename:<22}  {len(data):>5} bytes  ({len(lines)} rows)")


# ══════════════════════════════════════════════════════════════════════════════
#  TITLE  —  big spaced-letter logo + tagline
# ══════════════════════════════════════════════════════════════════════════════
def make_title():
    # 8 rows.  Use block-letter D-E-M-O spread across rows 1-5, meta rows 6-8.
    # Build a compact 5-row block logo for "DEMOSCENE"
    # Each letter is 5 cols wide + 1 space gap; 9 letters * 6 = 54 cols, starts col 14
    # We'll do a simpler but punchy 3-row block representation

    lines = []

    # Row 1 – top shadow bar
    lines.append(row(
        col(FB*80, BK)
    ))

    # Row 2 – "DEMOSCENE" in large spaced caps with colour sweep
    colours = [BC,BC, BW,BW, BY,BY, BG,BG, BC]
    letters = " D E M O S C E N E "
    logo    = ""
    ci = 0
    for ch in letters:
        logo += colours[ci % len(colours)] + BLD + ch + RST
        if ch != " ": ci += 1
    # pad to 80
    vis = len(letters)
    pad_l = (80 - vis) // 2
    lines.append(row(
        " " * pad_l + logo + " " * max(0, 80 - vis - pad_l)
    ))

    # Row 3 – subtitle spaced
    sub = "T H E   E X P L O R A T I O N   O F   A R T"
    lines.append(row(
        col(centre_plain(sub, 80), C)
    ))

    # Row 4 – double rule
    lines.append(row(
        col(DH * 80, BC)
    ))

    # Row 5 – block art band  ░▒▓█ colour gradient █▓▒░
    band = ""
    grad = [BK, BK, BB, BB, BC, BC, BW, BW, BC, BC, BB, BB, BK, BK]
    segs = [LB, LB, MB, MB, HB, HB, FB, FB, FB, FB, HB, HB, MB, MB, LB, LB]
    total = 80
    step  = total // len(segs)
    for i, seg in enumerate(segs):
        c = grad[i % len(grad)]
        lines.append  # oops — build string instead
    band = ""
    for i in range(80):
        t = i / 79.0
        if   t < 0.25: c = BK
        elif t < 0.45: c = BB
        elif t < 0.55: c = BC
        elif t < 0.75: c = BW
        elif t < 0.85: c = BC
        else:           c = BK
        ch = FB if 0.35 < t < 0.65 else (HB if 0.2 < t < 0.8 else MB)
        band += c + ch
    band += RST
    lines.append(row(band))

    # Row 6 – tagline
    tag = f"  {col(BULL, BK)}  {col('A  C E L L F I S H  P R O D U C T I O N', BK)}  {col(BULL, BK)}"
    lines.append(row(centre_plain(
        f"{col(BULL*3, BC)}  {col('A  C E L L F I S H  P R O D U C T I O N', BK)}  {col(BULL*3, BC)}",
        80
    )))

    # Row 7 – version / placeholder note
    note = col("[ art/title.ans  —  80 x 8  —  replace with final ANSI art ]", R)
    lines.append(row(centre_plain("[ art/title.ans  |  80x8  |  replace with final ANSI ]", 80)
                     .replace("[ art/title.ans  |  80x8  |  replace with final ANSI ]", note)))

    # Row 8 – bottom shadow
    lines.append(row(col(LB * 80, BK)))

    write_ans("title.ans", lines, "DEMOSCENE Title")


# ══════════════════════════════════════════════════════════════════════════════
#  HQ  —  ASCII computer-room scene
# ══════════════════════════════════════════════════════════════════════════════
def make_hq():
    lines = []

    # Row 1 – ceiling / top border
    lines.append(row(col(STL + SH*78 + STR, BC)))

    # Row 2 – room top with hanging cables
    cables = (col(SV, BC) + "  " +
              col("~", BK) + col("~", BK) + col("~", BK) +
              "                " +
              col(BULL + " monitor " + BULL, BW) +
              "                " +
              col("~", BK) + col("~", BK) +
              "  " + col(SV, BC))
    lines.append(row(pad(cables, 4 + 3 + 16 + 11 + 16 + 3 + 2 + 2)))

    # Row 3 – desk with monitor
    mon   = col(STL + SH*14 + STR, BK)
    scrn  = col(SV, BK) + col(" >_ READY     ", BG) + col(SV, BK)
    desk  = (col(SV, BC) + "  " + mon +
             "   " + col(FB*12, BK) + "   " +
             col("[ " + SH*10 + " ]", BW) +
             "   " + col(SH*16, BK) +
             "  " + col(SV, BC))
    lines.append(row(pad(desk, 2 + 2 + 16 + 3 + 12 + 3 + 14 + 3 + 16 + 2 + 2)))

    # Row 4 – screen content + keyboard
    scr2  = (col(SV, BC) + "  " +
             col(SV, BK) + col(" >_ HQ ONLINE  ", BG) + col(SV, BK) +
             "   " + col(LB*12, BK) +
             "   " + col("[" + SH*12 + "]", BK) +
             "   " + col(LB*16, BK) +
             "  " + col(SV, BC))
    lines.append(row(pad(scr2, 2 + 2 + 1 + 15 + 1 + 3 + 12 + 3 + 14 + 3 + 16 + 2 + 2)))

    # Row 5 – desk surface line
    deskline = (col(SV, BC) + "  " +
                col(SBL + SH*14 + SBR, BK) +
                col(SH*50, BK) +
                "  " + col(SV, BC))
    lines.append(row(pad(deskline, 2 + 2 + 16 + 50 + 2 + 2)))

    # Row 6 – floor with floppy disks scattered
    floor = (col(SV, BC) +
             col("  " + LB*6 + "  ", BK) +
             col(BULL + " floppy " + BULL, BY) +
             col("  " + MB*4 + "  ", BK) +
             col(BULL + " src " + BULL, BG) +
             col("  " + LB*6 + "  ", BK) +
             col(BULL + " beer " + BULL, BY) +
             col("  " + MB*4 + "  ", BK) +
             col(SV, BC))
    lines.append(row(pad(floor, 1 + 8 + 10 + 8 + 8 + 8 + 9 + 8 + 1)))

    # Row 7 – placeholder note
    note = "art/hq.ans  |  80x8  |  reused on produce / upload / raid screens"
    lines.append(row(col(SV, BC) + col(centre_plain(note, 78), R) + col(SV, BC)))

    # Row 8 – floor border
    lines.append(row(col(SBL + SH*78 + SBR, BC)))

    write_ans("hq.ans", lines, "DEMOSCENE HQ")


# ══════════════════════════════════════════════════════════════════════════════
#  MAP  —  ASCII network diagram with nodes and links
# ══════════════════════════════════════════════════════════════════════════════
def make_map():
    lines = []

    N  = lambda name, c=BC: col(f"[{name}]", c)   # node box
    LK = lambda: col(SH*3, BK)                     # link

    # Row 1
    lines.append(row(col(DTL + DH*78 + DTR, BB)))

    # Row 2 – title
    lines.append(row(
        col(DV, BB) +
        col("  NETWORK MAP  ", BC) + col(BULL, BK) +
        col("  nodes discovered  ", BK) + col(BULL, BK) +
        col("  connections charted  ", BK) + col(BULL, BK) +
        col("  routes planned      ", BK) +
        col(DV, BB)
    ))

    # Row 3 – top node row
    lines.append(row(
        col(DV, BB) +
        "    " + N("THE DUNGEON") + LK() + N("SPEED OF LIGHT") + LK() +
        N("GATES OF ASGARD") + LK() + N("???",BK) +
        "    " + col(DV, BB)
    ))

    # Row 4 – vertical links
    lines.append(row(
        col(DV, BB) +
        "    " + col("      " + SV + "              ", BK) +
        "      " + col(SV, BK) +
        "               " + col(SV, BK) +
        "                   " + col(SV, BK) +
        "       " + col(DV, BB)
    ))

    # Row 5 – middle node row
    lines.append(row(
        col(DV, BB) +
        "  " + N("HOME BBS", BG) + LK() + N("THE SWAP SHOP") + LK() +
        N("ACID BOARDS") + LK() + N("WAREZ DEN") +
        "   " + col(DV, BB)
    ))

    # Row 6 – vertical links row 2
    lines.append(row(
        col(DV, BB) +
        "           " + col(SV, BK) +
        "              " + col(SV, BK) +
        "              " + col(SV, BK) +
        "                           " + col(DV, BB)
    ))

    # Row 7 – placeholder note
    note = "art/map.ans  |  80x8  |  replace with hand-drawn network map"
    lines.append(row(col(DV, BB) + col(centre_plain(note, 78), R) + col(DV, BB)))

    # Row 8
    lines.append(row(col(DBL + DH*78 + DBR, BB)))

    write_ans("map.ans", lines, "DEMOSCENE Map")


# ══════════════════════════════════════════════════════════════════════════════
#  RAID  —  two crews facing off
# ══════════════════════════════════════════════════════════════════════════════
def make_raid():
    lines = []

    crew_l = col("YOUR CREW", BG)
    crew_r = col("RIVAL CREW", BR)
    vs     = col("  ><  ", BY)

    # Row 1
    lines.append(row(col(STL + SH*78 + STR, BR)))

    # Row 2 – header
    lines.append(row(
        col(SV, BR) +
        col("  R A I D  ", BY) + col(BULL, BK) +
        col("  rep at stake  ", BK) + col(BULL, BK) +
        col("  loot on the table  ", BK) + col(BULL, BK) +
        col("  choose your tactic              ", BK) +
        col(SV, BR)
    ))

    # Row 3 – divider with VS
    left_bar  = col(HB * 28, BR)
    right_bar = col(HB * 28, BG)
    lines.append(row(
        col(SV, BR) + "  " + left_bar +
        col("  V S  ", BY) +
        right_bar + "  " + col(SV, BR)
    ))

    # Row 4 – crew labels
    lines.append(row(
        col(SV, BR) +
        col("  " + FB*3 + "  YOUR  CREW  " + FB*3 + "  ", BG) +
        " " * 30 +
        col("  " + FB*3 + "  RIVAL CREW  " + FB*3 + "  ", BR) +
        col(SV, BR)
    ))

    # Row 5 – strength bars
    pbar = col("[" + FB*18 + LB*6 + "]", BG)
    ebar = col("[" + FB*12 + LB*12 + "]", BR)
    lines.append(row(
        col(SV, BR) +
        "  STR " + pbar + "           " +
        "STR " + ebar +
        "     " + col(SV, BR)
    ))

    # Row 6 – tactics hint
    lines.append(row(
        col(SV, BR) +
        col("  [A] Assault  ", BC) +
        col("[S] Sneak  ", BC) +
        col("[H] Hit+Run  ", BC) +
        col("[Q] Retreat  ", BK) +
        " " * 24 +
        col(SV, BR)
    ))

    # Row 7 – placeholder note
    note = "art/raid.ans  |  80x8  |  replace with crew confrontation art"
    lines.append(row(col(SV, BR) + col(centre_plain(note, 78), R) + col(SV, BR)))

    # Row 8
    lines.append(row(col(SBL + SH*78 + SBR, BR)))

    write_ans("raid.ans", lines, "DEMOSCENE Raid")


# ══════════════════════════════════════════════════════════════════════════════
#  TRADE  —  market stall with item icons
# ══════════════════════════════════════════════════════════════════════════════
def make_trade():
    lines = []

    # item icons (CP437-style)
    icons = {
        "DISKS":  col("\x7f\x7f", BY),    # small squares
        "SOURCE": col("</>" , BG),
        "ART":    col(DIAm*2, BC),
        "MODS":   col("\x0e\x0e", BM),    # musical notes
        "TOOLS":  col("\x1e\x1e", BW),    # up arrow tools
        "HW":     col("\xfe\xfe", BK),    # small squares
        "BEER":   col("\xf0\xf0", BY),    # approx
    }

    # Row 1
    lines.append(row(col(DTL + DH*78 + DTR, BY)))

    # Row 2 – header
    lines.append(row(
        col(DV, BY) +
        col("  T R A D E   P O S T  ", BY) + col(BULL, BK) +
        col("  buy low  sell high  barter everything  ", BK) +
        "             " + col(DV, BY)
    ))

    # Row 3 – item shelf top
    lines.append(row(
        col(DV, BY) +
        col("  " + STL + SH*10 + STR + "  " + STL + SH*10 + STR +
            "  " + STL + SH*10 + STR + "  " + STL + SH*10 + STR +
            "  " + STL + SH*10 + STR + "  " + STL + SH*8  + STR + "  ", BK) +
        col(DV, BY)
    ))

    # Row 4 – item shelf contents
    def shelf_item(label, icon, price_col=BY):
        return (col(SV, BK) + icon + " " +
                col(f"{label:<7}", BW) +
                col(SV, BK))
    shelf = ("  " +
             shelf_item("DISKS",  col(LB*2, BY)) +
             " " + shelf_item("SOURCE", col("</>", BG)) +
             " " + shelf_item("ART",    col(DIAm*2, BC)) +
             " " + shelf_item("MODS",   col("\x0e\x0e", BM)) +
             " " + shelf_item("TOOLS",  col("\x1e\x1e", BW)) +
             " " + col(SV, BK) + col("BEER   ", BY) + col(SV, BK) +
             "  ")
    lines.append(row(col(DV, BY) + shelf + col(DV, BY)))

    # Row 5 – shelf bottom + prices
    lines.append(row(
        col(DV, BY) +
        col("  " + SBL + SH*10 + SBR + "  " + SBL + SH*10 + SBR +
            "  " + SBL + SH*10 + SBR + "  " + SBL + SH*10 + SBR +
            "  " + SBL + SH*10 + SBR + "  " + SBL + SH*8  + SBR + "  ", BK) +
        col(DV, BY)
    ))

    # Row 6 – credit balance hint
    lines.append(row(
        col(DV, BY) +
        col("  Credits: ", BK) + col("----", BY) +
        col("   [1-7] select item   [B] buy   [S] sell   [Q] back", BK) +
        "                    " +
        col(DV, BY)
    ))

    # Row 7 – placeholder note
    note = "art/trade.ans  |  80x8  |  replace with market / trade post art"
    lines.append(row(col(DV, BY) + col(centre_plain(note, 78), R) + col(DV, BY)))

    # Row 8
    lines.append(row(col(DBL + DH*78 + DBR, BY)))

    write_ans("trade.ans", lines, "DEMOSCENE Trade")


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCE  —  compiler output mid-run
# ══════════════════════════════════════════════════════════════════════════════
def make_produce():
    lines = []

    def codeline(text, c=BK): return col(text, c)

    # Row 1
    lines.append(row(col(STL + SH*78 + STR, BM)))

    # Row 2 – header
    lines.append(row(
        col(SV, BM) +
        col("  P R O D U C E  ", BM) + col(BULL, BK) +
        col("  cracktro  4k  64k  musicdisk  full demo  ", BK) +
        "              " + col(SV, BM)
    ))

    # Row 3 – fake compiler output line 1
    lines.append(row(
        col(SV, BM) +
        col("  C:\\TASM\\TASM.EXE ", BW) + col("demo.asm", BY) +
        col(" /z /l /la /zi", BK) + col(" ... Turbo Assembler  v4.1", BG) +
        "               " + col(SV, BM)
    ))

    # Row 4 – fake compiler output line 2
    lines.append(row(
        col(SV, BM) +
        col("  Assembling ", BK) + col("EFFECTS.ASM", BY) +
        col("  Pass 1...Pass 2... ", BK) +
        col("0 errors, 0 warnings", BG) +
        "                     " + col(SV, BM)
    ))

    # Row 5 – linker + cruncher
    lines.append(row(
        col(SV, BM) +
        col("  TLINK: ", BW) + col("Linking... ", BK) +
        col("CRUNCH> ", BY) + col("Input: 68432 bytes  ", BK) +
        col("Output: ", BY) + col("63981 bytes  ", BG) +
        col("[", BK) + col(FB*14 + LB*6, BM) + col("]", BK) +
        " " * 8 + col(SV, BM)
    ))

    # Row 6 – size check + release
    lines.append(row(
        col(SV, BM) +
        col("  Size OK ", BG) + col(BULL, BK) +
        col(" DEMO.EXE ", BW) + col("64000 bytes ", BK) +
        col(BULL, BK) + col(" Ready to release! ", BY) +
        col(BULL, BK) + col(" The scene will notice.", BG) +
        "           " + col(SV, BM)
    ))

    # Row 7 – placeholder note
    note = "art/produce.ans  |  80x8  |  replace with compiler / coder art"
    lines.append(row(col(SV, BM) + col(centre_plain(note, 78), R) + col(SV, BM)))

    # Row 8
    lines.append(row(col(SBL + SH*78 + SBR, BM)))

    write_ans("produce.ans", lines, "DEMOSCENE Produce")


# ══════════════════════════════════════════════════════════════════════════════
#  COURIER  —  route map with origin/destination
# ══════════════════════════════════════════════════════════════════════════════
def make_courier():
    lines = []

    node = lambda n, c=BC: col(f"({n})", c)

    # Row 1
    lines.append(row(col(STL + SH*78 + STR, BC)))

    # Row 2 – header
    lines.append(row(
        col(SV, BC) +
        col("  C O U R I E R  ", BC) + col(BULL, BK) +
        col("  pick up  ", BK) + col(BULL, BK) +
        col("  deliver  ", BK) + col(BULL, BK) +
        col("  get paid  ", BK) + col(BULL, BK) +
        col("  time is credits                 ", BK) +
        col(SV, BC)
    ))

    # Row 3 – origin node
    lines.append(row(
        col(SV, BC) +
        "   " + node("ORIGIN NODE", BG) +
        col(SH*3 + ">" , BK) + col(SH*3, BK) +
        col(BULL + " CARGO " + BULL, BY) +
        col(SH*3 + ">", BK) + col(SH*3, BK) +
        node("DESTINATION", BC) +
        "                    " +
        col(SV, BC)
    ))

    # Row 4 – route line
    lines.append(row(
        col(SV, BC) +
        col("   " + " "*12 + SH*32, BK) +
        col(">", BY) +
        col(SH*18 + "   ", BK) +
        "           " +
        col(SV, BC)
    ))

    # Row 5 – cargo detail
    lines.append(row(
        col(SV, BC) +
        col("  Cargo: ", BK) + col("--- floppy disks  ", BY) +
        col("Reward: ", BK) + col("--- credits  ", BG) +
        col("Expires: ", BK) + col("day --  ", BR) +
        col("Difficulty: ", BK) + col("***  ", BY) +
        "         " + col(SV, BC)
    ))

    # Row 6 – accept / decline hint
    lines.append(row(
        col(SV, BC) +
        col("  [A] Accept mission  ", BG) +
        col("[Q] Decline  ", BR) +
        col(BULL + "  Must have cargo in inventory to accept  " + BULL, BK) +
        "             " + col(SV, BC)
    ))

    # Row 7 – placeholder note
    note = "art/courier.ans  |  80x8  |  replace with courier / route art"
    lines.append(row(col(SV, BC) + col(centre_plain(note, 78), R) + col(SV, BC)))

    # Row 8
    lines.append(row(col(SBL + SH*78 + SBR, BC)))

    write_ans("courier.ans", lines, "DEMOSCENE Courier")


# ══════════════════════════════════════════════════════════════════════════════
#  PARTY  —  big screen + crowd silhouette
# ══════════════════════════════════════════════════════════════════════════════
def make_party():
    lines = []

    # Row 1 – roof
    lines.append(row(col(FB*80, BK)))

    # Row 2 – big screen on the wall (centre)
    screen_top = ("  " + col(DTL + DH*36 + DTR, BY) + "  ")
    lines.append(row(
        col(FB*2, BK) +
        screen_top +
        col(" " * 36, BK) +
        col(FB*2, BK)
    ))

    # Row 3 – screen content
    scr = col(DV, BY) + col(centre_plain("* COMPO RUNNING — VOTE NOW *", 36), BW) + col(DV, BY)
    lines.append(row(
        col(FB*2, BK) + "  " + scr + "  " + col(FB*2, BK) +
        col("  " + STL + SH*8 + STR + "  " + STL + SH*10 + STR, BK) +
        "        "
    ))

    # Row 4 – screen bottom + speakers
    scr_bot = "  " + col(DBL + DH*36 + DBR, BY) + "  "
    lines.append(row(
        col(FB*2, BK) +
        scr_bot +
        col(" " * 10, BK) +
        col(FB*2, BK) +
        col("  " + SBL + SH*8 + SBR + "  " + SBL + SH*10 + SBR, BK) +
        "        "
    ))

    # Row 5 – crowd row 1 (heads as small blocks)
    crowd1 = ""
    import random as _r; rng = _r.Random(42)
    for i in range(78):
        if rng.random() < 0.3:
            crowd1 += col(LH, rng.choice([BW, BK, BY, BC, BG]))
        else:
            crowd1 += " "
    lines.append(row(col(SV, BK) + crowd1 + col(SV, BK)))

    # Row 6 – crowd row 2 (denser — shoulders/bodies)
    crowd2 = ""
    for i in range(78):
        if rng.random() < 0.5:
            crowd2 += col(FB, rng.choice([BK, BK, BK, BW, BY]))
        else:
            crowd2 += col(HB, BK)
    lines.append(row(col(SV, BK) + crowd2 + col(SV, BK)))

    # Row 7 – placeholder note
    note = "art/party.ans  |  80x8  |  replace with demoparty scene art"
    lines.append(row(col(SV, BK) + col(centre_plain(note, 78), R) + col(SV, BK)))

    # Row 8 – floor
    lines.append(row(col(LO*80, BK)))

    write_ans("party.ans", lines, "DEMOSCENE Party")


# ══════════════════════════════════════════════════════════════════════════════
#  MESSAGES  —  teletype / terminal aesthetic
# ══════════════════════════════════════════════════════════════════════════════
def make_messages():
    lines = []

    prompt = col(">_ ", BG)

    # Row 1
    lines.append(row(col(STL + SH*78 + STR, BW)))

    # Row 2 – header
    lines.append(row(
        col(SV, BW) +
        col("  M E S S A G E   B O A R D  ", BW) + col(BULL, BK) +
        col("  scene gossip  ", BK) + col(BULL, BK) +
        col("  intel  ", BK) + col(BULL, BK) +
        col("  warnings               ", BK) +
        col(SV, BW)
    ))

    # Row 3 – column headers
    lines.append(row(
        col(SV, BW) +
        col("  NEW  ", BC) +
        col("FROM               ", BB) +
        col("SUBJECT                              ", BW) +
        col("DAY  ", BY) +
        col(SV, BW)
    ))

    # Row 4 – divider
    lines.append(row(
        col(SV, BW) +
        col("  " + SH*74 + "  ", BK) +
        col(SV, BW)
    ))

    # Row 5 – sample message 1
    lines.append(row(
        col(SV, BW) +
        col("  NEW  ", BC) +
        col("DARK/RAZOR1911     ", BB) +
        col("Your crew is a bunch of lamers        ", BW) +
        col("D3   ", BY) +
        col(SV, BW)
    ))

    # Row 6 – sample message 2
    lines.append(row(
        col(SV, BW) +
        col("       ", BK) +
        col("ACID/FUTURE CREW   ", BB) +
        col("Intel: new node deep in the network   ", BK) +
        col("D2   ", BK) +
        col(SV, BW)
    ))

    # Row 7 – placeholder note
    note = "art/messages.ans  |  80x8  |  replace with teletype / BBS terminal art"
    lines.append(row(col(SV, BW) + col(centre_plain(note, 78), R) + col(SV, BW)))

    # Row 8
    lines.append(row(col(SBL + SH*78 + SBR, BW)))

    write_ans("messages.ans", lines, "DEMOSCENE Messages")


# ══════════════════════════════════════════════════════════════════════════════
#  HOF  —  podium / trophy feel
# ══════════════════════════════════════════════════════════════════════════════
def make_hof():
    lines = []

    # Row 1
    lines.append(row(col(DTL + DH*78 + DTR, BY)))

    # Row 2 – header
    lines.append(row(
        col(DV, BY) +
        col("  H A L L   O F   F A M E  ", BY) + col(BULL, BK) +
        col("  the scene remembers the best  ", BK) + col(BULL, BK) +
        col("  glory lasts forever        ", BK) +
        col(DV, BY)
    ))

    # Row 3 – podium art (3-2-1 block columns)
    p3 = col("     2nd     ", BC)
    p1 = col("     1st     ", BY)
    p2 = col("     3rd     ", BW)
    lines.append(row(
        col(DV, BY) +
        " " * 8 +
        col(STL + SH*13 + STR, BY) + "  " +          # 1st – tallest
        col(STL + SH*13 + STR, BC) + "  " +          # 2nd
        col(STL + SH*13 + STR, BW) +                 # 3rd
        " " * 20 + col(DV, BY)
    ))

    # Row 4 – podium faces
    lines.append(row(
        col(DV, BY) +
        " " * 8 +
        col(SV + "  " + STAR + "  1 s t  " + STAR + "  " + SV, BY) + "  " +
        col(SV + "  " + STAR + "  2 n d  " + STAR + "  " + SV, BC) + "  " +
        col(SV + "  " + STAR + "  3 r d  " + STAR + "  " + SV, BW) +
        " " * 20 + col(DV, BY)
    ))

    # Row 5 – table header
    lines.append(row(
        col(DV, BY) + col(DH*78, BK) + col(DV, BY)
    ))

    # Row 6 – column headers
    lines.append(row(
        col(DV, BY) +
        col("  #   HANDLE        CREW                BBS              SCORE   DAY  ", BK) +
        col(DV, BY)
    ))

    # Row 7 – placeholder note
    note = "art/hof.ans  |  80x8  |  replace with trophy / hall of fame art"
    lines.append(row(col(DV, BY) + col(centre_plain(note, 78), R) + col(DV, BY)))

    # Row 8
    lines.append(row(col(DBL + DH*78 + DBR, BY)))

    write_ans("hof.ans", lines, "DEMOSCENE HoF")


# ══════════════════════════════════════════════════════════════════════════════
#  GAMEOVER  —  dramatic darkness, modem falling silent
# ══════════════════════════════════════════════════════════════════════════════
def make_gameover():
    lines = []

    # Row 1 – black top bar
    lines.append(row(col(FB*80, BK)))

    # Row 2 – fading signal
    fade = ""
    for i in range(78):
        t = 1.0 - i / 77.0
        ch = FB if t > 0.7 else (HB if t > 0.4 else (MB if t > 0.2 else LB))
        c  = BR if t > 0.5 else (R if t > 0.25 else BK)
        fade += col(ch, c)
    lines.append(row(col(SV, BR) + fade + col(SV, BR)))

    # Row 3 – big GAME OVER text
    go = "  G  A  M  E     O  V  E  R  "
    lines.append(row(
        col(SV, BR) +
        col(BLD + centre_plain(go, 78), BR) +
        col(SV, BR)
    ))

    # Row 4 – score line
    lines.append(row(
        col(SV, BR) +
        col(centre_plain("your legacy is written · the scene remembers", 78), BK) +
        col(SV, BR)
    ))

    # Row 5 – modem falling silent
    modem = "NO CARRIER"
    lines.append(row(
        col(SV, BR) +
        col("  ", BK) +
        col(LB*10, BK) + col(MB*8, BK) + col(HB*6, BK) + col(FB*4, BK) +
        col("  " + modem + "  ", BR) +
        col(FB*4, BK) + col(HB*6, BK) + col(MB*8, BK) + col(LB*10, BK) +
        col("  ", BK) +
        col(SV, BR)
    ))

    # Row 6 – stats hint
    lines.append(row(
        col(SV, BR) +
        col("  Demos  ", BK) + col("--", BW) +
        col("   Raids won  ", BK) + col("--", BG) +
        col("   Parties  ", BK) + col("--", BC) +
        col("   Beers  ", BK) + col("--", BY) +
        col("   Score  ", BK) + col("------", BY) +
        "             " + col(SV, BR)
    ))

    # Row 7 – placeholder note
    note = "art/gameover.ans  |  80x8  |  replace with dramatic game-over art"
    lines.append(row(col(SV, BR) + col(centre_plain(note, 78), R) + col(SV, BR)))

    # Row 8 – black bottom bar
    lines.append(row(col(FB*80, BK)))

    write_ans("gameover.ans", lines, "DEMOSCENE Game Over")


# ══════════════════════════════════════════════════════════════════════════════
#  EXPLORE  —  radar / scanner aesthetic
# ══════════════════════════════════════════════════════════════════════════════
def make_explore():
    lines = []

    import math

    # Build a small 7x7 ASCII radar circle in the left portion
    def radar_char(x, y, cx=6, cy=3, r=3):
        d = math.sqrt((x-cx)**2 + (y-cy)**2)
        if abs(d - r) < 0.7:   return col(BULL, BK)
        if abs(d - r*0.6) < 0.6: return col(BULL, BK)
        if d < 0.8:             return col("+", BC)
        return " "

    radar_rows = []
    for ry in range(7):
        rrow = ""
        for rx in range(13):
            rrow += radar_char(rx, ry)
        radar_rows.append(rrow)

    # Row 1
    lines.append(row(col(STL + SH*78 + STR, BC)))

    # Row 2 – header
    lines.append(row(
        col(SV, BC) +
        col("  E X P L O R E  ", BC) + col(BULL, BK) +
        col("  scan the network  ", BK) + col(BULL, BK) +
        col("  discover new nodes  ", BK) + col(BULL, BK) +
        col("  go deeper          ", BK) +
        col(SV, BC)
    ))

    # Rows 3-7 – radar on left, scanner text on right
    scan_lines = [
        col("  Network scanner ready.       ", BK),
        col("  Frequency: 28.800 kHz   ", BK) + col("[scanning]", BG),
        col("  Last node: ", BK) + col("unknown         ", BW),
        col("  Signal:    ", BK) + col(LB*6 + MB*4 + HB*2, BC),
        col("  [S] Scan   [Q] Back to HQ   ", BK),
    ]

    for i in range(5):
        rdr = radar_rows[i] if i < len(radar_rows) else " " * 13
        lines.append(row(
            col(SV, BC) +
            "  " + rdr + "  " +
            scan_lines[i] +
            " " * max(0, 78 - 2 - 13 - 2 - 40) +
            col(SV, BC)
        ))

    # Row 7 – placeholder note (row index 6, which is the 7th row)
    note = "art/explore.ans  |  80x8  |  replace with radar / scanner art"
    lines.append(row(col(SV, BC) + col(centre_plain(note, 78), R) + col(SV, BC)))

    # Row 8
    lines.append(row(col(SBL + SH*78 + SBR, BC)))

    write_ans("explore.ans", lines, "DEMOSCENE Explore")


# ══════════════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Writing v2 placeholder .ans files to: {OUT_DIR}\n")
    make_title()
    make_hq()
    make_map()
    make_raid()
    make_trade()
    make_produce()
    make_courier()
    make_party()
    make_messages()
    make_hof()
    make_gameover()
    make_explore()
    print("\nDone!  header.ans left untouched.")
    print("\nArtist brief for final art:")
    print("  80 cols x 8 rows  |  CP437 charset  |  ANSI colour codes  |  SAUCE record")
    print("  Replace files one by one — game picks them up immediately on next run.")
    print("\nPriority order for a real artist:")
    print("  1. hq.ans       — reused on most screens")
    print("  2. title.ans    — first impression")
    print("  3. party.ans    — most atmospheric moment")
    print("  4. raid.ans     — high tension")
    print("  5. gameover.ans — last impression")
    print("  6-12. rest in any order")
