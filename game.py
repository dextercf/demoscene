"""
game.py — Main game loop and screen routing
Demoscene: The Exploration of Art
A Cellfish Production

Entry point for the game. Reads BBS drop file, loads config,
runs the main game loop. All screens use cursor placement —
nothing scrolls, everything draws in place.

Run this file to start the game:
    python game.py
Or from a BBS door launcher:
    python game.py NODE_NUM SOCKET_HANDLE
"""

import os
import sys
import random
import configparser

import door
import player as playermod
import world  as worldmod
import ansi
import combat
import socketio

# ---------------------------------------------------------------------------
# Version — locked to Cellfish. Do not change.
# ---------------------------------------------------------------------------
GAME_TITLE = "Demoscene: The Exploration of Art"
DEVELOPER  = "Cellfish"
VERSION    = "0.1"

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config():
    cfg = configparser.ConfigParser()
    cfg_path = os.path.join(os.path.dirname(__file__), "config.ini")
    if os.path.isfile(cfg_path):
        cfg.read(cfg_path, encoding="cp437")
    if "cellfish" not in cfg:
        cfg["cellfish"] = {}
    cfg["cellfish"]["game_title"] = GAME_TITLE
    cfg["cellfish"]["developer"]  = DEVELOPER
    cfg["cellfish"]["version"]    = VERSION
    return cfg


def cfg_int(cfg, section, key, default):
    try:
        return int(cfg[section].get(key, default))
    except (KeyError, ValueError):
        return default


def cfg_str(cfg, section, key, default):
    try:
        return cfg[section].get(key, default)
    except KeyError:
        return default


def cfg_bool(cfg, section, key, default=True):
    val = cfg_str(cfg, section, key, str(default)).lower()
    return val in ("yes", "true", "1")


# ---------------------------------------------------------------------------
# NPC message generator
# ---------------------------------------------------------------------------

_MSG_TEMPLATES = [
    ("{crew} thinks your crew is a bunch of lamers. Prove them wrong.",
     lambda p, w: w.npc_crews[0].name if w.npc_crews else None, "Taunt"),
    ("We heard {crew} is planning a raid on your home board. Watch out.",
     lambda p, w: random.choice(w.npc_crews).name if w.npc_crews else None,
     "Warning"),
    ("Rumour has it {crew} just dropped a killer 64K at {node}.",
     lambda p, w: random.choice(w.npc_crews).name if w.npc_crews else None,
     "Scene News"),
    ("A new node was spotted deep in the network. Very deep.",
     lambda p, w: None, "Intel"),
    ("The phone lines are buzzing. Something big is about to drop.",
     lambda p, w: None, "Rumour"),
    ("Your demo got noticed. People are talking.",
     lambda p, w: None if p.demos_produced == 0 else "Scene", "Scene News"),
    ("Don't forget — {party} is coming up. Start stacking resources now.",
     lambda p, w: None, "Party Buzz"),
    ("h0ffman is rumoured to be DJing at the next party. Clear your schedule.",
     lambda p, w: None, "Party Buzz"),
    ("Gates of Asgard is said to be back online. Nobody can confirm it.",
     lambda p, w: None, "Rumour"),
    ("Point of No Return went dark three days ago. Nobody knows why.",
     lambda p, w: None, "Rumour"),
    ("SysOp of The Dungeon got busted. Board is gone. Moment of silence.",
     lambda p, w: None, "Scene News"),
    ("Disk couriers wanted. Good pay. No questions asked.",
     lambda p, w: None, "Opportunity"),
]


def generate_messages(player, world, current_day, count=5):
    msgs = []
    rng  = random.Random(current_day + hash(player.handle))
    pool = list(_MSG_TEMPLATES)
    rng.shuffle(pool)

    upcoming   = world.upcoming_parties(current_day, lookahead=10)
    party_name = upcoming[0].name if upcoming else "the next party"

    for template, crew_fn, subject in pool[:count * 2]:
        try:
            crew_val = crew_fn(player, world)
        except Exception:
            crew_val = None

        if world.npc_crews:
            sender_crew = rng.choice(world.npc_crews)
            sender = (f"{rng.choice(['DARK','ACID','FROST','BYTE','NEON','GRID'])}"
                      f"/{sender_crew.name[:8]}")
        else:
            sender = "ANONYMOUS"

        try:
            text = template.format(
                crew  = crew_val or (
                    world.npc_crews[0].name if world.npc_crews else "Unknown"),
                node  = (rng.choice(world.discovered_nodes()).name
                         if world.discovered_nodes() else "Unknown Node"),
                party = party_name,
            )
        except (KeyError, IndexError):
            text = template

        day_offset = rng.randint(max(1, current_day - 4), current_day)
        msgs.append({
            "from"   : sender,
            "subject": text[:50],
            "day"    : day_offset,
            "new"    : day_offset >= current_day - 1,
        })
        if len(msgs) >= count:
            break

    msgs.sort(key=lambda m: m["day"], reverse=True)
    return msgs


# ---------------------------------------------------------------------------
# New game setup
# ---------------------------------------------------------------------------

def new_game(door_info, cfg):
    import time

    # Draw base chrome using the title art
    ansi.clear_screen()
    ansi.draw_art("title")
    ansi.draw_divider(ansi.DIV_1)
    ansi.clear_line(ansi.STATUS)
    ansi.draw_divider(ansi.DIV_2)
    ansi.clear_zone(ansi.MENU_TOP, ansi.MENU_BOT)
    ansi.draw_divider(ansi.DIV_3)
    ansi.clear_zone(ansi.RES_TOP, ansi.RES_BOT)

    # Header in menu zone
    ansi.write_at(ansi.MENU_TOP,     1,
                  f"  {ansi.C}Welcome to {GAME_TITLE}{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 1, 1,
                  f"  {ansi.DG}A {DEVELOPER} production{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 2, 1,
                  f"  {ansi.W}Handle: {ansi.G}{door_info.handle}{ansi.RST}")

    time.sleep(0.3)

    p = playermod.Player()
    p.handle   = door_info.handle
    p.bbs_name = cfg_str(cfg, "bbs", "bbs_name", door_info.bbs_name)
    p.apply_config(cfg)

    # Crew name input in result zone
    ansi.write_at(ansi.RES_TOP, 1,
                  f"  {ansi.DG}Choose your crew name (max 20 chars){ansi.RST}")
    ansi.move(ansi.RES_TOP + 1, 1)
    crew = ansi.get_input("  Crew name: ")
    p.crew_name = crew[:20] if crew else f"{p.handle}'s Crew"

    # Generation progress — fixed rows in result zone
    ansi.write_at(ansi.RES_TOP + 2, 1, "")
    ansi.dots(ansi.RES_TOP + 2, 3, "Generating network map", count=6)
    ansi.dots(ansi.RES_TOP + 3, 3, "Placing rival crews",    count=6)

    w = worldmod.World()
    w.generate(p.handle, p.bbs_name, cfg)

    ansi.dots(ansi.RES_BOT - 1, 3, "Scheduling demoparties", count=6)

    if w.home_node:
        w.home_node.name = p.bbs_name
    p.home_node    = p.bbs_name
    p.current_node = p.bbs_name

    # Results in menu zone
    ansi.write_at(ansi.MENU_TOP + 4, 1,
                  f"  {ansi.Y}Home board : {ansi.W}{p.bbs_name}{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 5, 1,
                  f"  {ansi.Y}Crew name  : {ansi.W}{p.crew_name}{ansi.RST}")

    # Press any key prompt at bottom
    ansi.write_at(ansi.RES_BOT, 1,
                  f"  {ansi.DG}Press any key to enter the scene...{ansi.RST}")
    ansi.show_cursor()
    from socketio import get_io
    io = get_io()
    if io:
        io.getkey()
    ansi.hide_cursor()

    p.save()
    w.save(p.handle)
    return p, w


# ---------------------------------------------------------------------------
# Action handlers
# ---------------------------------------------------------------------------

def action_explore(player, world, cfg, rng):
    if not player.use_turns(2):
        ansi.result(f"{ansi.R}> Not enough turns to explore (costs 2).{ansi.RST}")
        return

    ansi.result(f"{ansi.DG}> Scanning the network...{ansi.RST}")
    ansi.spinner(ansi.RES_BOT, 3, "Scanning", duration=1.5)

    found = world.explore(
        world.get_node_by_name(player.current_node).index
        if world.get_node_by_name(player.current_node) else 0,
        rng
    )

    if found:
        ansi.result(f"{ansi.C}> Node discovered: {ansi.W}{found.name}{ansi.RST}")
        ansi.typewriter(ansi.RES_BOT, 3,
                        f"  {found.description}  ·  {found.hops} hops from home",
                        colour=ansi.DG, delay=0.03)
        if found.is_legendary:
            ansi.result(
                f"{ansi.Y}*** LEGENDARY NODE FOUND! The scene will remember this. ***{ansi.RST}")
            player.adjust_resource("reputation", 50)
    else:
        ansi.result(f"{ansi.DG}> Nothing found. The network stays quiet.{ansi.RST}")

    ansi.draw_status(player, player.bbs_name)


def action_travel(player, world, cfg, rng):
    discovered = world.discovered_nodes()
    if not discovered:
        ansi.result(f"{ansi.R}> No nodes discovered yet.{ansi.RST}")
        return

    def show_invalid(input_col):
        ansi.move(ansi.RES_BOT, input_col)
        ansi._out(f"{ansi.R}Invalid selection.{ansi.RST}" + " " * 20)
        ansi.pause(0.7)

    page = 0
    page_size = ansi.map_rows_per_page()

    while True:
        discovered = world.discovered_nodes()
        total_pages = ansi.map_page_count(len(discovered))
        page = max(0, min(page, total_pages - 1))
        start = page * page_size
        end = start + page_size
        page_nodes = discovered[start:end]

        ansi.screen_map(player, world, page=page)
        prompt_text = f"  Travel to node [1-{len(page_nodes)}]"
        if total_pages > 1:
            prompt_text += ", N, P, or Q:"
        else:
            prompt_text += " or Q:"
        input_col = len(prompt_text) + 1
        ansi.move(ansi.RES_BOT, input_col)
        choice = ansi.get_input("", max_len=2).strip().upper()

        if choice in ("", "Q", "00"):
            return
        if choice == "N":
            if total_pages > 1 and page < total_pages - 1:
                page += 1
            else:
                show_invalid(input_col)
            continue
        if choice == "P":
            if total_pages > 1 and page > 0:
                page -= 1
            else:
                show_invalid(input_col)
            continue
        if not choice.isdigit():
            show_invalid(input_col)
            continue

        slot = int(choice)
        if slot < 1 or slot > len(page_nodes):
            show_invalid(input_col)
            continue

        node = page_nodes[slot - 1]

        if not player.use_turns(1):
            ansi.write_at(ansi.RES_BOT, 1,
                          f"  {ansi.R}Not enough turns to travel.{ansi.RST}")
            ansi.pause(0.8)
            return

        player.current_node = node.name

        ansi.write_at(ansi.RES_BOT - 1, 1,
                      f"  {ansi.DG}Dialling {node.name}...{ansi.RST}")
        ansi.dial(ansi.RES_BOT, 3, node.name)
        ansi.write_at(ansi.RES_BOT, 1,
                      f"  {ansi.C}Connected: {ansi.W}{node.name}{ansi.RST}"
                      f"  {ansi.DG}{node.description}{ansi.RST}")
        if node.crew:
            ansi.write_at(ansi.RES_BOT - 1, 1,
                          f"  {ansi.R}{node.crew} is present here.{ansi.RST}")

        ansi.draw_status(player)
        import time
        time.sleep(1.0)
        return


def action_trade(player, world, cfg, rng):
    node = world.get_node_by_name(player.current_node)
    if not node:
        ansi.result(f"{ansi.R}> No trade post at this location.{ansi.RST}")
        return

    if not player.use_turns(1):
        ansi.result(f"{ansi.R}> Not enough turns to trade (costs 1).{ansi.RST}")
        return

    trade_keys = ["floppy_disks", "source_code", "artwork",
                  "mod_music", "hardware", "tools", "beer"]

    while True:
        ansi.screen_trade(player, node)
        key = ansi.get_key(valid_keys="1234567BSQbsq")

        if key == "Q":
            break

        if not key.isdigit():
            continue

        idx = int(key) - 1
        if idx < 0 or idx >= len(trade_keys):
            continue

        res  = trade_keys[idx]
        from playermod import RESOURCE_NAMES
        name = RESOURCE_NAMES.get(res, res)
        buy  = node.prices.get(res, 0)
        sell = node.sell_price(res)

        ansi.result(
            f"  {ansi.W}{name}{ansi.RST}  "
            f"{ansi.G}Buy: {buy}c{ansi.RST}  "
            f"{ansi.R}Sell: {sell}c{ansi.RST}")

        action = ansi.get_key(
            prompt=f"  {ansi.DG}[B] Buy  [S] Sell  [Q] Cancel: {ansi.RST}",
            valid_keys="BSQbsq"
        )

        if action == "Q":
            continue

        qty_str = ansi.get_input("  Quantity: ")
        try:
            qty = max(1, int(qty_str))
        except ValueError:
            continue

        if action == "B":
            total = buy * qty
            if player.phone_credits < total:
                ansi.result(f"{ansi.R}> Not enough phone credits.{ansi.RST}")
            else:
                player.adjust_resource("phone_credits", -total)
                player.adjust_resource(res, qty)
                ansi.result(
                    f"{ansi.G}> Bought {qty} {name} for {total}c.{ansi.RST}")
                ansi.draw_status(player)

        elif action == "S":
            have = player.get_resource(res)
            qty  = min(qty, have)
            if qty <= 0:
                ansi.result(f"{ansi.R}> You don't have any {name}.{ansi.RST}")
            else:
                total = sell * qty
                player.adjust_resource(res, -qty)
                player.adjust_resource("phone_credits", total)
                ansi.result(
                    f"{ansi.G}> Sold {qty} {name} for {total}c.{ansi.RST}")
                ansi.draw_status(player)


def action_produce(player, world, cfg, rng):
    demo_defs = [
        ("cracktro",  "Cracktro",
         {"source_code": 50,  "artwork": 20},  40),
        ("4k",        "4K Intro",
         {"source_code": 120, "artwork": 40},  120),
        ("64k",       "64K Intro",
         {"source_code": 200, "artwork": 80},  280),
        ("musicdisk", "Musicdisk",
         {"source_code": 80,  "mod_music": 300}, 200),
        ("demo",      "Full Demo",
         {"source_code": 400, "artwork": 200, "mod_music": 150}, 600),
    ]

    ansi.screen_produce(player)
    key = ansi.get_key(valid_keys="12345Qq")

    if key == "Q":
        return

    idx = int(key) - 1
    if idx < 0 or idx >= len(demo_defs):
        return

    dkey, label, costs, base_rep = demo_defs[idx]

    if not player.can_afford(costs):
        ansi.result(f"{ansi.R}> Not enough resources to produce {label}.{ansi.RST}")
        return

    if not player.use_turns(3):
        ansi.result(f"{ansi.R}> Not enough turns (costs 3).{ansi.RST}")
        return

    player.spend(costs)

    # Production animation
    ansi.result(f"{ansi.DG}> Starting {label} production...{ansi.RST}")
    ansi.progress_bar(ansi.RES_TOP + 1, 3, "Compiling",
                      width=24, duration=0.8, colour=ansi.G)
    ansi.progress_bar(ansi.RES_TOP + 2, 3, "Linking  ",
                      width=24, duration=0.5, colour=ansi.G)
    ansi.progress_bar(ansi.RES_TOP + 3, 3, "Packing  ",
                      width=24, duration=0.4, colour=ansi.C)

    luck   = rng.uniform(0.8, 1.2)
    gained = int(base_rep * luck)
    player.adjust_resource("reputation", gained)
    player.demos_produced += 1

    ansi.result(f"{ansi.Y}> {label} released! +{gained} reputation.{ansi.RST}")

    if rng.random() < 0.4 and world.npc_crews:
        rival = rng.choice(world.npc_crews)
        ansi.result(f"  {ansi.DG}{rival.name} noticed your release.{ansi.RST}")

    ansi.draw_status(player)


def action_raid(player, world, cfg, rng):
    targets = []
    for crew in world.npc_crews:
        if crew.home_node is not None:
            node = world.get_node(crew.home_node)
            if node and node.discovered:
                targets.append((crew, node))

    if not targets:
        ansi.result(
            f"{ansi.DG}> No known rival crews to raid. Explore more.{ansi.RST}")
        return

    # Target selection screen
    ansi.clear_screen()
    ansi.draw_art("raid")
    ansi.draw_divider(ansi.DIV_1)
    ansi.move(ansi.STATUS, 1)
    ansi.writeln(f"  {ansi.C}SELECT TARGET:{ansi.RST}")
    ansi.draw_divider(ansi.DIV_2)

    for i, (crew, node) in enumerate(targets):
        agg = "!!!" if crew.aggression == 3 else \
              ("!!"  if crew.aggression == 2 else "!")
        col = ansi.R if crew.aggression == 3 else \
              (ansi.Y if crew.aggression == 2 else ansi.W)
        ansi.move(ansi.MENU_TOP + i, 1)
        ansi.writeln(
            f"  [{i+1:02d}] {col}{crew.name:<16}{ansi.RST}"
            f"  at {ansi.B}{node.name:<24}{ansi.RST}"
            f"  {ansi.DG}aggression: {agg}{ansi.RST}")

    ansi.draw_divider(ansi.DIV_3)
    ansi.clear_zone(ansi.RES_TOP, ansi.RES_BOT)
    ansi.write_at(ansi.RES_TOP, 1,
                  f"  {ansi.DG}Enter number, or 00 to cancel{ansi.RST}")

    num_str = ansi.get_input("  Enter number: ")
    try:
        num = int(num_str)
    except ValueError:
        return
    if num == 0:
        return

    idx = num - 1
    if idx < 0 or idx >= len(targets):
        return

    target_crew, target_node = targets[idx]

    if not player.use_turns(3):
        ansi.result(f"{ansi.R}> Not enough turns to raid (costs 3).{ansi.RST}")
        return

    ansi.screen_raid(player, target_crew)
    key = ansi.get_key(valid_keys="ASHQashq")

    if key == "Q":
        player.turns_remaining += 3
        return

    # Resolve combat via combat.py
    result = combat.resolve_raid(player, target_crew, key, rng)

    # Animate combat bars using the resolved power values
    ansi.result(f"{ansi.DG}> Launching raid on {target_crew.name}...{ansi.RST}")
    ansi.animate_combat_bars(ansi.RES_TOP + 1,
                             result.player_power, result.enemy_power)

    import time
    time.sleep(0.3)

    # Apply result to player (resources + reputation + stats)
    combat.apply_raid_result(player, result)

    # Display outcome
    if result.victory:
        ansi.result(f"{ansi.G}> RAID SUCCESSFUL! +{combat.REP_WIN} rep{ansi.RST}")
        if result.loot:
            loot_parts = []
            for res, amt in result.loot.items():
                from playermod import RESOURCE_NAMES
                loot_parts.append(
                    f"{amt} {RESOURCE_NAMES.get(res, res)}")
            ansi.result(
                f"  {ansi.Y}Looted: {', '.join(loot_parts[:3])}{ansi.RST}")
        if result.counter_risk:
            ansi.result(
                f"  {ansi.R}Warning: {target_crew.name} may counter-raid.{ansi.RST}")
    else:
        ansi.result(
            f"{ansi.R}> RAID FAILED — {target_crew.name} repelled your crew.{ansi.RST}")
        if result.losses:
            loss_parts = []
            for res, amt in result.losses.items():
                from playermod import RESOURCE_NAMES
                loss_parts.append(
                    f"{amt} {RESOURCE_NAMES.get(res, res)}")
            ansi.result(
                f"  {ansi.R}Lost: {', '.join(loss_parts)}{ansi.RST}")

    ansi.result(f"  {ansi.DG}{result.message}{ansi.RST}")
    ansi.draw_status(player, player.bbs_name)


def action_defend(player, world, cfg, rng):
    if not player.use_turns(1):
        ansi.result(f"{ansi.R}> Not enough turns.{ansi.RST}")
        return
    boost = rng.randint(5, 15)
    player.defense = min(100, player.defense + boost)
    ansi.result(
        f"{ansi.G}> Home board fortified. "
        f"Defense +{boost} (now {player.defense}).{ansi.RST}")
    ansi.draw_status(player)


def action_party(player, world, cfg, rng, party):
    travel_cost = cfg_int(cfg, "parties", "party_travel_cost", 80)

    if player.phone_credits < travel_cost:
        ansi.result(
            f"{ansi.R}> Not enough credits to travel to {party.name} "
            f"(costs {travel_cost}c).{ansi.RST}")
        return

    player.adjust_resource("phone_credits", -travel_cost)
    player.parties_attended += 1
    party.attended = True

    while True:
        ansi.screen_party(party, player)
        valid = "DRQdrq" + "".join(str(i+1) for i in range(len(party.compos)))
        if "5k_run" in party.special:
            valid += "Kk"
        key = ansi.get_key(valid_keys=valid)

        if key == "Q":
            break

        elif key == "D":
            if player.beer <= 0:
                ansi.result(f"{ansi.R}> No beer left!{ansi.RST}")
            else:
                player.adjust_resource("beer", -1)
                player.beers_drunk += 1
                effects = [
                    (f"{ansi.G}> Good conversation. +10 reputation.{ansi.RST}", "rep"),
                    (f"{ansi.Y}> You traded src for artwork. Creative.{ansi.RST}", None),
                    (f"{ansi.R}> One too many. Missed a compo deadline.{ansi.RST}", None),
                    (f"{ansi.G}> Old scener gave you 50 credits.{ansi.RST}", "creds"),
                ]
                msg, bonus = rng.choice(effects)
                ansi.result(msg)
                if bonus == "rep":
                    player.adjust_resource("reputation", 10)
                elif bonus == "creds":
                    player.adjust_resource("phone_credits", 50)
                ansi.draw_status(player)

        elif key == "R" and cfg_bool(cfg, "parties", "rave_events", True):
            if rng.randint(1, 100) <= party.rave_chance:
                dj = rng.choice(worldmod.RAVE_DJS)
                ansi.result(f"{ansi.M}*** RAVE ***  DJ: {dj['handle']}{ansi.RST}")
                ansi.result(f"  {ansi.DG}{dj['flavour']}{ansi.RST}")
                player.raves_attended += 1
                player.adjust_resource("reputation", dj["rep_bonus"])
                ansi.result(f"  {ansi.C}+{dj['rep_bonus']} reputation{ansi.RST}")
            else:
                ansi.result(f"{ansi.DG}> No rave tonight. Early night for once.{ansi.RST}")
            ansi.draw_status(player)

        elif key == "K" and "5k_run" in party.special:
            if not cfg_bool(cfg, "parties", "revision_5k_run", True):
                ansi.result(f"{ansi.DG}> 5K run disabled on this board.{ansi.RST}")
                continue
            position = rng.randint(1, 40)
            ansi.result(f"{ansi.C}*** REVISION 5K RUN ***{ansi.RST}")
            ansi.dots(ansi.RES_BOT, 3, "Running", count=8, delay=0.2)
            ansi.result(f"  {ansi.W}You finished in position {position}.{ansi.RST}")
            if position <= 10:
                ansi.result(f"  {ansi.Y}Top 10! +25 reputation.{ansi.RST}")
                player.adjust_resource("reputation", 25)
            else:
                ansi.result(f"  {ansi.G}You finished. Sausages afterwards.{ansi.RST}")
            setattr(player, "5k_runs", getattr(player, "5k_runs", 0) + 1)
            ansi.draw_status(player)

        elif key.isdigit():
            idx = int(key) - 1
            if 0 <= idx < len(party.compos):
                compo_key = party.compos[idx]
                cdef = worldmod.COMPO_DEFS.get(compo_key, {})
                if not cdef:
                    continue
                if not player.can_afford(cdef["costs"]):
                    ansi.result(
                        f"{ansi.R}> Not enough resources for this compo.{ansi.RST}")
                    continue
                player.spend(cdef["costs"])
                luck = rng.random()
                if luck > 0.85:
                    place, rep = 1, cdef["rep_1st"]
                elif luck > 0.65:
                    place, rep = 2, cdef["rep_2nd"]
                elif luck > 0.45:
                    place, rep = 3, cdef["rep_3rd"]
                else:
                    place, rep = rng.randint(4, 12), 10

                ansi.result(f"{ansi.DG}> Submitting entry...{ansi.RST}")
                ansi.dots(ansi.RES_BOT, 3, "Waiting for results", count=6)
                if place <= 3:
                    ansi.result(
                        f"{ansi.Y}*** {cdef['label']} — "
                        f"{_ordinal(place)} PLACE! +{rep} rep ***{ansi.RST}")
                else:
                    ansi.result(
                        f"{ansi.W}> {cdef['label']} — "
                        f"{_ordinal(place)} place. +{rep} rep.{ansi.RST}")
                player.adjust_resource("reputation", rep)
                player.demos_produced += 1
                ansi.draw_status(player)


def action_messages(player, world, cfg):
    msgs = generate_messages(player, world, player.day)
    ansi.screen_messages(msgs)
    ansi.get_key(valid_keys="RQrq")


def action_hof(player, cfg):
    entries = playermod.load_leaderboard()
    ansi.screen_hof(entries, player.handle)
    ansi.get_key(valid_keys="Qq")


# ---------------------------------------------------------------------------
# End of day
# ---------------------------------------------------------------------------

def end_day(player, world, cfg, rng):
    ap = cfg_int(cfg, "gameplay", "action_points_per_day", 10)
    player.end_day(ap)

    if world.npc_crews and rng.random() < 0.15:
        raider = rng.choice(world.npc_crews)
        if raider.aggression >= 2:
            defence = combat.resolve_defence(player, raider, rng)
            ansi.result(
                f"{ansi.R if defence['success'] else ansi.G}"
                f"> Overnight: {defence['message']}{ansi.RST}")
            ansi.draw_status(player, player.bbs_name)

    event_chance = cfg_int(cfg, "gameplay", "random_event_chance", 25)
    if rng.randint(1, 100) <= event_chance:
        _random_event(player, world, rng)

    party = world.party_on_day(player.day)
    if party and not party.attended:
        ansi.result(f"{ansi.Y}*** {party.name} starts today! ***{ansi.RST}")
        ansi.result(f"  {ansi.DG}{party.flavour}{ansi.RST}")
        key = ansi.get_key(
            prompt=f"  {ansi.C}[A] Attend  [S] Skip: {ansi.RST}",
            valid_keys="ASas"
        )
        if key == "A":
            action_party(player, world, cfg, rng, party)

    player.save()
    world.save(player.handle)


def _random_event(player, world, rng):
    events = [
        (f"{ansi.G}> A courier dropped off a package. +50 floppy disks.{ansi.RST}",
         lambda: player.adjust_resource("floppy_disks", 50)),
        (f"{ansi.G}> Someone paid for your last demo. +100 credits.{ansi.RST}",
         lambda: player.adjust_resource("phone_credits", 100)),
        (f"{ansi.C}> Your reputation spreads. +15 reputation.{ansi.RST}",
         lambda: player.adjust_resource("reputation", 15)),
        (f"{ansi.Y}> Found an old box of floppies. +30 disks.{ansi.RST}",
         lambda: player.adjust_resource("floppy_disks", 30)),
        (f"{ansi.M}> A scener shared source code with you. +40 src.{ansi.RST}",
         lambda: player.adjust_resource("source_code", 40)),
        (f"{ansi.DG}> Nothing unusual happened today.{ansi.RST}",
         lambda: None),
    ]
    msg, effect = rng.choice(events)
    ansi.result(msg)
    effect()
    ansi.draw_status(player)


# ---------------------------------------------------------------------------
# Main HQ loop
# ---------------------------------------------------------------------------

def hq_loop(player, world, cfg, rng):
    game_length = cfg_int(cfg, "gameplay", "game_length_days", 50)

    # Draw the HQ screen once
    ansi.screen_hq(player)

    while not player.is_game_over(game_length):
        key = ansi.get_key(valid_keys="ETPRDBMSQetpRdbmsq")

        if key == "E":
            action_explore(player, world, cfg, rng)
        elif key == "T":
            action_travel(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "B":
            action_trade(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "P":
            action_produce(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "R":
            action_raid(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "D":
            action_defend(player, world, cfg, rng)
        elif key == "M":
            action_messages(player, world, cfg)
            ansi.screen_hq(player)
        elif key == "S":
            action_hof(player, cfg)
            ansi.screen_hq(player)
        elif key == "Q":
            player.save()
            world.save(player.handle)
            ansi.result(f"{ansi.DG}> Game saved. Returning to BBS...{ansi.RST}")
            import time
            time.sleep(1.0)
            return False

        # End of day when turns run out
        if player.turns_remaining <= 0:
            ansi.result(
                f"{ansi.DG}> Day {player.day} is over. Get some sleep.{ansi.RST}")
            import time
            time.sleep(0.8)
            end_day(player, world, cfg, rng)
            # Redraw HQ for new day
            ansi.screen_hq(player)

    return True


# ---------------------------------------------------------------------------
# Title screen loop
# ---------------------------------------------------------------------------

def title_loop(door_info, cfg):
    while True:
        ansi.screen_title()
        key = ansi.get_key(valid_keys="NCSQncsq")

        if key == "Q":
            ansi.result(f"{ansi.DG}Goodbye. The scene never sleeps.{ansi.RST}")
            import time
            time.sleep(0.8)
            return None, None

        elif key == "S":
            entries = playermod.load_leaderboard()
            ansi.screen_hof(entries, door_info.handle)
            ansi.get_key(valid_keys="Qq")

        elif key == "C":
            p = playermod.Player()
            p.handle = door_info.handle
            if p.load():
                w = worldmod.World()
                if w.load(p.handle):
                    return p, w
            ansi.result(
                f"{ansi.DG}No save found. Starting new game...{ansi.RST}")
            import time
            time.sleep(1.0)
            return new_game(door_info, cfg)

        elif key == "N":
            return new_game(door_info, cfg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    cfg = load_config()

    art_path = cfg_str(cfg, "display", "art_path", "art")
    ansi.set_art_path(art_path)

    # Initialise socket I/O — must happen before any output
    sock_handle = socketio.parse_socket_handle()
    io          = socketio.init(sock_handle)

    # Log socket status
    import time
    log_path = os.path.join(
        os.environ.get("TEMP", "C:\\mystic\\temp1"), "demoscene_io.log")
    try:
        with open(log_path, "w") as f:
            f.write(f"Socket handle: {sock_handle}\n")
            f.write(f"IO type: {type(io).__name__}\n")
            f.write(f"Time: {time.time()}\n")
    except Exception:
        pass

    door_info = door.load()

    rng = random.Random()
    rng.seed(hash(door_info.handle) ^ id(rng))

    player, world = title_loop(door_info, cfg)
    if player is None:
        return

    game_length = cfg_int(cfg, "gameplay", "game_length_days", 50)

    game_ended = hq_loop(player, world, cfg, rng)

    if game_ended:
        player.calculate_score()
        playermod.submit_score(player)
        rank = playermod.get_player_rank(player.handle)
        ansi.screen_game_over(player, rank)
        ansi.get_key()

    ansi.show_cursor()
    ansi.clear_screen()
    # Give Mystic time to detect process exit and redraw menu
    # before the socket closes
    import time
    time.sleep(3.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _draw_status(player):
    """Helper — draws status with player's bbs_name."""
    ansi.draw_status(player, player.bbs_name)


if __name__ == "__main__":
    main()