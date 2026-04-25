"""
game.py — Main game loop and screen routing
Demoscene: The Exploration of Art
A Cellfish Production
"""

import os
import sys
import random
import configparser
import time

import door
import player as playermod
import world  as worldmod
import ansi
import combat
import socketio
import courier as couriermod

GAME_TITLE, DEVELOPER, VERSION = "Demoscene: The Exploration of Art", "Cellfish", "0.1"

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config():
    cfg = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(__file__), "config.ini")
    if os.path.isfile(path):
        cfg.read(path, encoding="cp437")
    cfg["cellfish"] = {"game_title": GAME_TITLE, "developer": DEVELOPER, "version": VERSION}
    return cfg

def cfg_int(cfg, sec, key, d):
    try:
        return int(cfg[sec].get(key, d))
    except (KeyError, ValueError):
        return d

def cfg_str(cfg, sec, key, d):
    try:
        return cfg[sec].get(key, d)
    except KeyError:
        return d

def cfg_bool(cfg, sec, key, default=True):
    val = cfg_str(cfg, sec, key, str(default)).lower()
    return val in ("yes", "true", "1")

# ---------------------------------------------------------------------------
# Random events config
# ---------------------------------------------------------------------------

def _load_random_events(cfg, rng):
    path = cfg_str(cfg, "events", "events_file", "").strip()
    if not path:
        return None
    path = os.path.join(os.path.dirname(__file__), path)
    if not os.path.isfile(path):
        return None

    events = []
    try:
        with open(path, "r", encoding="cp437") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",")
                if len(parts) >= 5:
                    try:
                        weight = int(parts[0].strip())
                        colour = parts[1].strip()
                        msg = parts[2].strip()
                        res = parts[3].strip()
                        amt = int(parts[4].strip())
                        node_type = parts[5].strip() if len(parts) > 5 else ""
                        events.append((weight, colour, msg, res, amt, node_type))
                    except ValueError:
                        continue
    except OSError:
        return None

    return events if events else None

# ---------------------------------------------------------------------------
# Action: Explore
# ---------------------------------------------------------------------------

def action_explore(player, world, cfg, rng):
    # Draw screen once — results persist until player leaves
    ansi.screen_explore(player)
    while True:
        key = ansi.get_key(valid_keys="SQ")
        if key == "Q":
            return
        if player.use_turns(2):
            # Resolve what will be found
            curr = world.get_node_by_name(player.current_node)
            found = world.explore(curr.index if curr else 0, rng)

            # Animate progress bar (~7-8s), node name revealed at ~3s
            # animate_scan_bar redraws the scanner row itself from scratch
            ansi.animate_scan_bar(found)

            # After bar completes, animate info line
            if found:
                ansi.animate_explore_line(ansi.EXP_INFO,
                    found.description)
                if found.is_legendary:
                    ansi.animate_explore_line(ansi.EXP_INFO + 1,
                        "*** LEGENDARY NODE! +50 reputation ***")
                    player.adjust_resource("reputation", 50)
                # Save world immediately so discovered flag persists
                # even if player disconnects before end of day
                world.save(player.handle)
            else:
                ansi.animate_explore_line(ansi.EXP_INFO,
                    "Nothing found on this frequency.")
        else:
            # Flash error on scanner row, leave other results intact
            ansi.move(ansi.EXP_SCAN, 1); ansi._out(ansi.ERASE_LINE)
            ansi._out(f"   {ansi.R}Not enough turns to scan (costs 2).{ansi.RST}")
            time.sleep(1.5)
            ansi._draw_exp_labels()  # restore labels
        ansi._draw_explore_status(player)

# ---------------------------------------------------------------------------
# Action: Travel
# ---------------------------------------------------------------------------

def action_travel(player, world, cfg, rng, daily_mission=None):
    page, pg_sz = 0, 9
    mission_dest = (daily_mission.dest
                    if daily_mission and daily_mission.accepted and not daily_mission.delivered
                    else None)
    while True:
        disc = world.discovered_nodes()
        pg_cnt = max(1, (len(disc) + pg_sz - 1) // pg_sz)
        shown = disc[page * pg_sz:(page + 1) * pg_sz]
        ansi.screen_map(player, world, page, pg_sz, mission_dest)
        valid = "QNP" + "".join(str(i) for i in range(1, len(shown) + 1))
        key = ansi.get_key(valid_keys=valid).upper()
        if key == "Q":
            return
        if key == "N" and page < pg_cnt - 1:
            page += 1
            continue
        if key == "P" and page > 0:
            page -= 1
            continue
        if key.isdigit() and 0 < int(key) <= len(shown):
            node = shown[int(key) - 1]
            if node.name.lower() == player.current_node.lower():
                continue
            if not player.use_turns(1):
                ansi.result(f"{ansi.R}> Not enough turns to travel.{ansi.RST}")
                return
            player.current_node = node.name

            # Full-screen dial-up sequence
            ansi.clear_screen()
            ansi.draw_art("travel")
            ansi.draw_divider(ansi.DIV_1)
            ansi.clear_zone(ansi.MENU_TOP, ansi.RES_BOT)
            ansi.draw_divider(ansi.STATUS_DIV)
            ansi.draw_status(player, player.bbs_name)

            ansi.write_at(ansi.DIV_1 + 1,   1, f"    {ansi.C}CONNECTING TO:{ansi.RST} {ansi.W}{node.name}{ansi.RST}")
            ansi.write_at(ansi.DIV_1 + 2,   1, f"    {ansi.DG}{node.label}  ·  {node.description}{ansi.RST}")

            # Scrolling terminal log starts one row earlier
            TERM_TOP = ansi.DIV_3
            TERM_BOT = ansi.RES_BOT - 1
            TERM_H   = TERM_BOT - TERM_TOP + 1
            term_buf = []

            def _redraw_term():
                shown_lines = term_buf[-TERM_H:]
                for i in range(TERM_H):
                    ansi.move(TERM_TOP + i, 1)
                    ansi._out(ansi.ERASE_LINE)
                    if i < len(shown_lines):
                        ansi._out(f"    {shown_lines[i]}{ansi.RST}")

            def _log(text, delay=0.4):
                term_buf.append(text)
                _redraw_term()
                if delay: time.sleep(delay)

            connect_strings = ["CONNECT 2400", "CONNECT 9600", "CONNECT 14400", "CONNECT 28800", "CONNECT 33600"]
            connect = rng.choice(connect_strings)
            phone   = f"+{rng.randint(1,99)}-{rng.randint(100,999)}-{rng.randint(1000,9999)}"

            _log(f"{ansi.G}ATZ{ansi.RST}", 0.3)
            _log(f"{ansi.G}OK{ansi.RST}", 0.4)

            # Type phone number digit by digit
            term_buf.append(f"{ansi.G}ATDT {phone}{ansi.RST}")
            _redraw_term()
            last_row = TERM_TOP + min(len(term_buf) - 1, TERM_H - 1)
            ansi.move(last_row, 1); ansi._out(ansi.ERASE_LINE)
            ansi._out(f"    {ansi.G}ATDT {ansi.RST}")
            for digit in phone:
                ansi._out(ansi.G + digit + ansi.RST)
                time.sleep(0.08)
            time.sleep(0.6)

            _log(f"{ansi.G}RINGING...{ansi.RST}", 1.0)
            _log(f"{ansi.W}{connect}{ansi.RST}", 0.5)
            _log(f"{ansi.G}Connected to {ansi.RST}{ansi.W}{node.name}{ansi.RST}", 0.5)
            _log(f"{ansi.G}Board type: {ansi.RST}{ansi.G}{node.label}{ansi.RST}", 0.4)
            _log(f"{ansi.G}{node.description}{ansi.RST}", 0.4)

            if node.crew:
                _log(f"{ansi.Y}*** {ansi.W}{node.crew}{ansi.Y} is present here ***{ansi.RST}", 0.6)

            ansi.write_at(ansi.RES_BOT, 1,
                f"    {ansi.DG}Press any key to continue...{ansi.RST}")
            ansi.show_cursor()
            io = socketio.get_io()
            if io: io.getkey()
            ansi.hide_cursor()
            ansi.clear_screen()
            ansi.draw_status(player, player.bbs_name)
            return

# ---------------------------------------------------------------------------
# Action: Trade
# ---------------------------------------------------------------------------

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
        key = ansi.get_key(valid_keys="1234567Qq").upper()
        if key == "Q":
            break
        if not key.isdigit():
            continue
        idx = int(key) - 1
        if idx < 0 or idx >= len(trade_keys):
            continue

        res  = trade_keys[idx]
        from player import RESOURCE_NAMES
        name = RESOURCE_NAMES.get(res, res)
        buy  = node.prices.get(res, 0)
        sell = node.sell_price(res)

        # Item detail + action prompt on RES_BOT (single row, below divider)
        ansi.write_at(ansi.RES_BOT, 1,
            f"  {ansi.W}{name:<15}{ansi.RST}  "
            f"{ansi.G}Buy:{buy}c{ansi.RST}  "
            f"{ansi.R}Sell:{sell}c{ansi.RST}  "
            f"  {ansi.C}[{ansi.RST}{ansi.W}B{ansi.RST}{ansi.C}]{ansi.RST} {ansi.DG}Buy{ansi.RST}  "
            f"{ansi.C}[{ansi.RST}{ansi.W}S{ansi.RST}{ansi.C}]{ansi.RST} {ansi.DG}Sell{ansi.RST}  "
            f"{ansi.C}[{ansi.RST}{ansi.W}Q{ansi.RST}{ansi.C}]{ansi.RST} {ansi.DG}Cancel{ansi.RST}")

        action = ansi.get_key(valid_keys="BSQbsq").upper()

        if action == "Q":
            continue

        def trade_err(msg):
            ansi.write_at(ansi.RES_BOT, 1,
                f"  {ansi.R}{msg}{ansi.RST}  {ansi.DG}[any key]{ansi.RST}")
            ansi.get_key()

        if action == "B":
            max_qty = player.phone_credits // buy if buy > 0 else 0
            if max_qty == 0:
                trade_err(f"Not enough credits ({player.phone_credits}c, need {buy}c each).")
                continue
            ansi.write_at(ansi.RES_BOT, 1, "")
            qty_str = ansi.get_input(f"  How many (max: {max_qty})? ")
            try:
                qty = max(1, min(int(qty_str), max_qty))
            except ValueError:
                continue
            total = buy * qty
            player.adjust_resource("phone_credits", -total)
            player.adjust_resource(res, qty)
            ansi.result(f"{ansi.G}> Bought {qty} {name} for {total}c.{ansi.RST}")
            ansi.draw_status(player, player.bbs_name, show_credits=True)

        elif action == "S":
            have = player.get_resource(res)
            if have == 0:
                trade_err(f"You don't have any {name}.")
                continue
            ansi.write_at(ansi.RES_BOT, 1, "")
            qty_str = ansi.get_input(f"  How many (max: {have})? ")
            try:
                qty = max(1, min(int(qty_str), have))
            except ValueError:
                continue
            total = sell * qty
            player.adjust_resource(res, -qty)
            player.adjust_resource("phone_credits", total)
            ansi.result(f"{ansi.G}> Sold {qty} {name} for {total}c.{ansi.RST}")
            ansi.draw_status(player, player.bbs_name, show_credits=True)

# ---------------------------------------------------------------------------
# Action: Produce
# ---------------------------------------------------------------------------

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
        ("ansipack",  "ANSI Art Pack",
         {"artwork": 150},  60),
        ("modmusic",  "MOD Music",
         {"mod_music": 200}, 80),
        ("chiptune",  "Chiptune",
         {"mod_music": 80},  40),
        ("wild",      "Wild Demo",
         {"source_code": 300, "artwork": 250, "mod_music": 200}, 900),
    ]

    while True:
        ansi.screen_produce(player)
        key = ansi.get_key(valid_keys="123456789Qq").upper()
        if key == "Q":
            return

        idx = int(key) - 1
        if idx < 0 or idx >= len(demo_defs):
            continue

        dkey, label, costs, base_rep = demo_defs[idx]

        from player import RESOURCE_NAMES
        cost_parts = [f"{v} {RESOURCE_NAMES.get(k, k)}" for k, v in costs.items()]
        cost_str   = "  +  ".join(cost_parts)
        fail_pct   = {"cracktro":5,"4k":10,"64k":15,"musicdisk":10,"demo":20,"ansipack":8,"modmusic":10,"chiptune":8,"wild":25}.get(dkey,10)

        detail = (f"  {ansi.C}{label}{ansi.RST}  "
                  f"{ansi.DG}costs:{ansi.RST} {ansi.Y}{cost_str}{ansi.RST}  "
                  f"{ansi.DG}gain:{ansi.RST} {ansi.G}~{base_rep}rep{ansi.RST}  "
                  f"{ansi.DG}fail:{ansi.RST} {ansi.R}{fail_pct}%{ansi.RST}  "
                  f"{ansi.DG}turns:{ansi.RST} {ansi.Y}3{ansi.RST}")

        if not player.can_afford(costs):
            ansi.screen_produce(player,
                detail_lines=[f"  {ansi.R}Not enough resources — {cost_str}{ansi.RST}"],
                prompt=f"  {ansi.DG}Press any key to go back...{ansi.RST}")
            ansi.get_key()
            continue

        if player.turns_remaining < 3:
            ansi.screen_produce(player,
                detail_lines=[f"  {ansi.R}Not enough turns — costs 3.{ansi.RST}"],
                prompt=f"  {ansi.DG}Press any key to go back...{ansi.RST}")
            ansi.get_key()
            continue

        ansi.screen_produce(player,
            detail_lines=[detail],
            prompt=(f"  {ansi.C}[Y]{ansi.RST} Produce  "
                    f"{ansi.C}[Q]{ansi.RST} Cancel: "))
        confirm = ansi.get_key(valid_keys="YQyq").upper()
        if confirm == "Q":
            continue

        player.use_turns(3)
        player.spend(costs)

        luck        = rng.uniform(0.8, 1.2)
        fail_chance = {"cracktro":0.05,"4k":0.10,"64k":0.15,"musicdisk":0.10,"demo":0.20,"ansipack":0.08,"modmusic":0.10,"chiptune":0.08,"wild":0.25}
        failed      = rng.random() < fail_chance.get(dkey, 0.10)
        gained      = 0 if failed else int(base_rep * luck)
        rival_name  = None

        if not failed:
            player.adjust_resource("reputation", gained)
            player.demos_produced += 1
            if rng.random() < 0.4 and world.npc_crews:
                rival_name = rng.choice(world.npc_crews).name

        # Full-screen animation — replaces produce list, waits for keypress
        ansi.screen_produce_animation(label, dkey, gained, failed, rival_name)
        ansi.draw_status(player, player.bbs_name)
        return

# ---------------------------------------------------------------------------
# Action: Raid
# ---------------------------------------------------------------------------

def action_raid(player, world, cfg, rng):
    targets = []
    for crew in world.npc_crews:
        if crew.home_node is not None:
            node = world.get_node(crew.home_node)
            if node and node.discovered:
                targets.append((crew, node))

    if not targets:
        ansi.result(f"{ansi.DG}> No known rival crews to raid. Explore more.{ansi.RST}")
        return

    # --- Target selection ---
    ansi.screen_raid_targets(player, targets)
    n = min(len(targets), 7)
    valid = "".join(str(i + 1) for i in range(n)) + "Qq"
    key = ansi.get_key(valid_keys=valid).upper()
    if key == "Q":
        return
    target_crew, target_node = targets[int(key) - 1]

    # --- Tactic selection ---
    taunt = getattr(target_crew, 'taunt', '')
    ansi.screen_raid(player, target_crew, taunt)
    key = ansi.get_key(valid_keys="ASHQashq").upper()

    if key == "Q":
        return

    if not player.use_turns(5):
        ansi.result(f"{ansi.R}> Not enough turns to raid (costs 5).{ansi.RST}")
        return

    # --- Combat ---
    result = combat.resolve_raid(player, target_crew, key, rng)
    events = combat.generate_raid_events(key, rng)

    ansi.clear_zone(ansi.RES_TOP, ansi.RES_BOT)
    ansi.write_at(ansi.RES_TOP, 1,
        f"  {ansi.DG}Launching raid on {ansi.R}{target_crew.name}{ansi.DG}...{ansi.RST}")
    time.sleep(0.6)
    for i, event in enumerate(events):
        ansi.write_at(ansi.RES_TOP + 1 + i, 1, f"  {ansi.DG}{event}{ansi.RST}")
        time.sleep(1.8)
    time.sleep(0.3)
    ansi.animate_combat_bars(ansi.RES_TOP + 5, result.player_power, result.enemy_power)
    time.sleep(0.3)

    combat.apply_raid_result(player, result)
    player.pending_counter_raid = result.counter_risk and result.victory

    if result.victory:
        ansi.result(f"{ansi.G}> RAID SUCCESSFUL! +{combat.REP_WIN} rep{ansi.RST}")
        if result.loot:
            from player import RESOURCE_NAMES
            parts = [f"{amt} {RESOURCE_NAMES.get(res, res)}"
                     for res, amt in result.loot.items()]
            ansi.result(f"  {ansi.Y}Looted: {', '.join(parts[:3])}{ansi.RST}")
        if result.counter_risk:
            ansi.result(f"  {ansi.R}Warning: {target_crew.name} may counter-raid.{ansi.RST}")
    else:
        ansi.result(f"{ansi.R}> RAID FAILED — {target_crew.name} repelled your crew.{ansi.RST}")
        if result.losses:
            from player import RESOURCE_NAMES
            parts = [f"{amt} {RESOURCE_NAMES.get(res, res)}"
                     for res, amt in result.losses.items()]
            ansi.result(f"  {ansi.R}Lost: {', '.join(parts)}{ansi.RST}")

    ansi.result(f"  {ansi.DG}{result.message}{ansi.RST}")
    ansi.draw_status(player, player.bbs_name)
    ansi.write_at(ansi.RES_BOT, 1,
        f"  {ansi.C}[{ansi.RST}{ansi.W}Q{ansi.RST}{ansi.C}]{ansi.RST} {ansi.DG}Back{ansi.RST}")
    ansi.get_key(valid_keys="Qq")

# ---------------------------------------------------------------------------
# Action: Defend
# ---------------------------------------------------------------------------

def action_defend(player, world, cfg, rng):
    if not player.use_turns(1):
        ansi.result(f"{ansi.R}> Not enough turns.{ansi.RST}")
        time.sleep(1.5)
        return
    boost = rng.randint(5, 15)
    player.defense = min(100, player.defense + boost)
    ansi.result(
        f"{ansi.G}> Home board fortified. "
        f"Defense +{boost} (now {player.defense}).{ansi.RST}")
    ansi.draw_status(player, player.bbs_name)
    time.sleep(1.5)

# ---------------------------------------------------------------------------
# Action: Courier missions
# ---------------------------------------------------------------------------

def action_crew_screen(player):
    ansi.screen_crew(player)
    ansi.get_key(valid_keys="Qq")


def action_courier(player, world, cfg, rng, daily_mission):
    """Show the mission board and let player accept/decline."""
    if daily_mission is None:
        ansi.write_at(ansi.RES_BOT, 1,
            f"  {ansi.DG}> No courier missions available today.{ansi.RST}")
        ansi.get_key(valid_keys="Qq")
        return

    if daily_mission.is_expired(player.day):
        ansi.write_at(ansi.RES_BOT, 1,
            f"  {ansi.R}> The courier posting has expired.{ansi.RST}")
        ansi.get_key(valid_keys="Qq")
        return

    if daily_mission.delivered:
        ansi.screen_courier_complete(player, daily_mission)
        ansi.get_key(valid_keys="Qq")
        return

    if daily_mission.accepted:
        if player.current_node == daily_mission.dest:
            ok = couriermod.deliver_mission(player, daily_mission)
            if ok:
                ansi.draw_status(player, player.bbs_name)
                ansi.screen_courier_complete(player, daily_mission)
                ansi.get_key(valid_keys="Qq")
            return
        ansi.screen_courier_active(player, daily_mission)
        ansi.get_key(valid_keys="Qq")
        return

    # Mission board — warn if turns are tight
    warn = player.turns_remaining <= daily_mission.turn_cost
    ansi.screen_courier_board(player, daily_mission, warn_turns=warn)
    key = ansi.get_key(valid_keys="AHQahq").upper()

    if key == "H":
        ansi.screen_courier_help(player)
        ansi.get_key(valid_keys="Qq")
        return

    if key == "Q":
        return

    # Accept
    if not player.use_turns(1):
        ansi.write_at(ansi.RES_BOT, 1, f"  {ansi.R}> Not enough turns.{ansi.RST}")
        ansi.get_key(valid_keys="Qq")
        return

    ok = couriermod.accept_mission(player, daily_mission)
    if not ok:
        cargo = daily_mission.cargo_key.replace('_', ' ')
        ansi.write_at(ansi.RES_BOT, 1,
            f"  {ansi.R}> Need {daily_mission.cargo_amt} {cargo} in inventory.{ansi.RST}")
        player.turns_remaining += 1
        ansi.get_key(valid_keys="Qq")
    else:
        ansi.write_at(ansi.RES_BOT, 1,
            f"  {ansi.G}> Accepted. Travel to "
            f"{ansi.C}{daily_mission.dest}{ansi.G} to deliver.{ansi.RST}")
        ansi.draw_status(player, player.bbs_name)
        ansi.get_key(valid_keys="Qq")


# ---------------------------------------------------------------------------
# Action: Messages
# ---------------------------------------------------------------------------

def action_messages(player, world, cfg):
    while True:
        entries = playermod.load_oneliners()
        ansi.screen_oneliners(entries, player)

        key = ansi.get_key(valid_keys="WQwq").upper()
        if key == "Q":
            return

        # Write a new oneliner
        ansi.write_at(ansi.RES_BOT - 1, 1, "")
        max_oneliner_len = cfg_int(cfg, "scores", "max_oneliner_length", 60)
        text = ansi.get_input("  Write: ", max_len=max_oneliner_len)
        if text.strip():
            playermod.save_oneliner(
                player.handle, player.bbs_name, player.day, text.strip())

# ---------------------------------------------------------------------------
# Action: Hall of Fame
# ---------------------------------------------------------------------------

def action_hof(player, cfg):
    entries = playermod.load_leaderboard()
    ansi.screen_hof(entries, player.handle, player)
    ansi.get_key(valid_keys="Qq")

# ---------------------------------------------------------------------------
# Action: Party
# ---------------------------------------------------------------------------

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
        key = ansi.get_key(valid_keys=valid).upper()

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
                ansi.draw_status(player, player.bbs_name)

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
            ansi.draw_status(player, player.bbs_name)

        elif key == "K" and "5k_run" in party.special:
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
            ansi.draw_status(player, player.bbs_name)

        elif key.isdigit():
            idx = int(key) - 1
            if 0 <= idx < len(party.compos):
                compo_key = party.compos[idx]
                cdef = worldmod.COMPO_DEFS.get(compo_key, {})
                if not cdef:
                    continue
                if not player.can_afford(cdef["costs"]):
                    ansi.result(f"{ansi.R}> Not enough resources for this compo.{ansi.RST}")
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
                ansi.draw_status(player, player.bbs_name)

# ---------------------------------------------------------------------------
# End of day
# ---------------------------------------------------------------------------

def end_day(player, world, cfg, rng):
    ap = cfg_int(cfg, "gameplay", "action_points_per_day", 10)
    player.end_day(ap)

    # Apply daily defense decay — home board slowly degrades without upkeep
    combat.apply_defense_decay(player)

    # Replenish NPC resources slightly so raiding stays worthwhile all game
    combat.apply_npc_daily_trickle(world.npc_crews, rng)

    # Check for counter-raid: triggered if player won a raid this day
    # and the enemy had high aggression (counter_risk flag was set).
    # Falls back to a random 15% chance for unprovoked raids.
    counter_triggered = getattr(player, 'pending_counter_raid', False)
    player.pending_counter_raid = False  # always reset

    do_raid = counter_triggered or (world.npc_crews and rng.random() < 0.15)
    if do_raid and world.npc_crews:
        # Prefer aggressive crews for counter-raids
        if counter_triggered:
            aggressive = [c for c in world.npc_crews if c.aggression >= 2]
            raider = rng.choice(aggressive) if aggressive else rng.choice(world.npc_crews)
            ansi.result(f"{ansi.R}> Intel: a rival crew is moving on your board tonight...{ansi.RST}")
        else:
            raider = rng.choice(world.npc_crews)
        if counter_triggered or raider.aggression >= 2:
            defence = combat.resolve_defence(player, raider, rng)
            ansi.result(
                f"{ansi.G if defence['success'] else ansi.R}"
                f"> Overnight: {defence['message']}{ansi.RST}")
            ansi.draw_status(player, player.bbs_name)

    event_chance = cfg_int(cfg, "gameplay", "random_event_chance", 25)
    if rng.randint(1, 100) <= event_chance:
        _random_event(player, world, rng, cfg)

    party = world.party_on_day(player.day)
    if party and not party.attended:
        ansi.result(f"{ansi.Y}*** {party.name} starts today! ***{ansi.RST}")
        ansi.result(f"  {ansi.DG}{party.flavour}{ansi.RST}")
        key = ansi.get_key(
            prompt=f"  {ansi.C}[A] Attend  [S] Skip: {ansi.RST}",
            valid_keys="ASas"
        ).upper()
        if key == "A":
            action_party(player, world, cfg, rng, party)

    player.save()
    world.save(player.handle)

# ---------------------------------------------------------------------------
# HQ loop
# ---------------------------------------------------------------------------

def hq_loop(player, world, cfg, rng):
    game_len = cfg_int(cfg, "gameplay", "game_length_days", 50)
    daily_mission = couriermod.get_daily_mission(player, world, rng)
    ansi.screen_hq(player)
    while not player.is_game_over(game_len):
        key = ansi.get_key(valid_keys="ETPRDBSCWOQetprdbscwoq").upper()

        if key == "E":
            action_explore(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "T":
            action_travel(player, world, cfg, rng, daily_mission)
            ansi.screen_hq(player)
            if (daily_mission and daily_mission.accepted
                    and not daily_mission.delivered
                    and player.current_node == daily_mission.dest):
                action_courier(player, world, cfg, rng, daily_mission)
                ansi.screen_hq(player)
        elif key == "P":
            action_produce(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "R":
            action_raid(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "D":
            action_defend(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "B":
            action_trade(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "C":
            action_courier(player, world, cfg, rng, daily_mission)
            ansi.screen_hq(player)
        elif key == "W":
            action_crew_screen(player)
            ansi.screen_hq(player)
        elif key == "O":
            action_messages(player, world, cfg)
            ansi.screen_hq(player)
        elif key == "S":
            action_hof(player, cfg)
            ansi.screen_hq(player)
        elif key == "Q":
            ansi.write_at(ansi.RES_BOT, 1,
                f"  {ansi.DG}Save & Quit? "
                f"{ansi.C}[{ansi.RST}{ansi.W}Y{ansi.RST}{ansi.C}/{ansi.RST}{ansi.W}N{ansi.RST}{ansi.C}]{ansi.RST}{ansi.DG}:{ansi.RST}")
            confirm = ansi.get_key(valid_keys="YyNn").upper()
            if confirm == "Y":
                player.calculate_score()
                playermod.submit_score(player)
                player.save()
                world.save(player.handle)
                ansi.write_at(ansi.RES_BOT, 1,
                    f"  {ansi.DG}Game saved. Returning to title screen...{ansi.RST}")
                time.sleep(1.0)
                return False
            else:
                ansi.write_at(ansi.RES_BOT, 1, "")

        if player.turns_remaining <= 0:
            # Expire undelivered missions at day end
            if daily_mission and daily_mission.accepted and not daily_mission.delivered:
                couriermod.fail_mission(player, daily_mission)
                ansi.result(f"{ansi.R}> Courier mission expired. Cargo returned. -10 rep.{ansi.RST}")
                time.sleep(0.8)
            ansi.screen_end_day(player, rng)
            end_day(player, world, cfg, rng)
            daily_mission = couriermod.get_daily_mission(player, world, rng)
            ansi.screen_hq(player)

    return True

# ---------------------------------------------------------------------------
# Title / new game
# ---------------------------------------------------------------------------

def title_loop(door_info, cfg, rng):
    while True:
        ansi.screen_title(VERSION)
        key = ansi.title_lightbar_menu()
        if key == "Q":
            ansi.screen_quit()
            return None, None
        elif key == "S":
            entries = playermod.load_leaderboard()
            ansi.screen_hof(entries, door_info.handle)
            ansi.get_key(valid_keys="Qq")
        elif key == "H":
            ansi.screen_tutorial()
        elif key == "C":
            p = playermod.Player()
            p.handle = door_info.handle
            if p.load():
                w = worldmod.World()
                if w.load(p.handle):
                    return p, w
            ansi.clear_screen()
            ansi.write_at(12, 1, f"  {ansi.Y}No save found for {p.handle}{ansi.RST}")
            ansi.write_at(13, 1, f"  {ansi.DG}Press [N] to start a new game.{ansi.RST}")
            ansi.get_key()
            continue
        elif key == "N":
            p = playermod.Player()
            p.handle = door_info.handle
            if p.load():
                ansi.clear_screen()
                ansi.write_at(12, 1, f"  {ansi.R}WARNING: Existing save found for {p.handle}{ansi.RST}")
                ansi.write_at(13, 1, f"  {ansi.DG}Starting new game will overwrite it.{ansi.RST}")
                ansi.write_at(15, 1, f"  {ansi.C}[{ansi.W}Y{ansi.C}]{ansi.DG} Start anyway  {ansi.C}[{ansi.W}Q{ansi.C}]{ansi.DG} Cancel{ansi.RST}")
                confirm = ansi.get_key(valid_keys="YyQq")
                if confirm == "Q":
                    continue
            return _new_game(door_info, cfg, rng)


def _new_game(door_info, cfg, rng):
    ansi.clear_screen()
    ansi.draw_art("title")
    ansi.draw_divider(ansi.DIV_1)
    ansi.clear_zone(ansi.MENU_TOP, ansi.MENU_BOT)
    ansi.draw_divider(ansi.DIV_3)
    ansi.clear_zone(ansi.RES_TOP, ansi.RES_BOT)
    ansi.draw_divider(ansi.STATUS_DIV)
    ansi.clear_line(ansi.STATUS)

    p = playermod.Player()
    max_handle = cfg_int(cfg, "scores", "max_handle_length", 20)
    p.handle = door_info.handle[:max_handle].strip() or "Player"
    p.bbs_name = cfg_str(cfg, "bbs", "bbs_name", door_info.bbs_name)
    p.apply_config(cfg)

    ansi.write_at(ansi.MENU_TOP,     1, f"  {ansi.C}Welcome to {GAME_TITLE}{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 1, 1, f"  {ansi.DG}A {DEVELOPER} production{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 2, 1, f"  {ansi.W}Handle: {ansi.G}{p.handle}{ansi.RST}")

    time.sleep(0.3)

    max_crew_len = cfg_int(cfg, "scores", "max_crew_name_length", 20)
    ansi.write_at(ansi.RES_TOP, 1, f"  {ansi.DG}Choose your crew name (max {max_crew_len} chars){ansi.RST}")
    ansi.move(ansi.RES_TOP + 1, 1)
    crew = ansi.get_input("  Crew name: ", max_len=max_crew_len)
    p.crew_name = crew[:max_crew_len] if crew else f"{p.handle}'s Crew"

    ansi.dots(ansi.RES_TOP + 2, 3, "Generating network map", count=6)
    ansi.dots(ansi.RES_TOP + 3, 3, "Placing rival crews",    count=6)

    w = worldmod.World()
    w.generate(p.handle, p.bbs_name, cfg)

    ansi.dots(ansi.RES_BOT - 1, 3, "Scheduling demoparties", count=6)

    if w.home_node:
        w.home_node.name = p.bbs_name
    p.home_node    = p.bbs_name
    p.current_node = p.bbs_name

    ansi.write_at(ansi.MENU_TOP + 4, 1, f"  {ansi.Y}Home board : {ansi.W}{p.bbs_name}{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 5, 1, f"  {ansi.Y}Crew name  : {ansi.W}{p.crew_name}{ansi.RST}")
    ansi.write_at(ansi.RES_BOT, 1,      f"  {ansi.DG}Press any key to enter the scene...{ansi.RST}")
    ansi.get_key()

    p.save()
    w.save(p.handle)
    return p, w

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    cfg = load_config()
    art_path = cfg_str(cfg, "display", "art_path", "art")
    ansi.set_art_path(art_path)

    sock_handle = socketio.parse_socket_handle()
    io = socketio.init(sock_handle)

    door_info = door.load()
    rng = random.Random()
    rng.seed(hash(door_info.handle) ^ id(rng))

    while True:
        player, world = title_loop(door_info, cfg, rng)
        if player is None:
            break

        game_ended = hq_loop(player, world, cfg, rng)

        if game_ended:
            player.calculate_score()
            playermod.submit_score(player)
            rank = playermod.get_player_rank(player.handle)
            ansi.screen_game_over(player, rank)
            ansi.get_key()
            break
        # user quit with Q → loop back to title screen

    _exit_cleanly(io)


def _exit_cleanly(io):
    ansi.show_cursor()
    if io:
        io.close()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def _random_event(player, world, rng, cfg):
    events = _load_random_events(cfg, rng)
    if not events:
        events = [
            (10, "G", "> A courier dropped off a package. +50 floppy disks.", "floppy_disks", 50, ""),
            (10, "G", "> Someone paid for your last demo. +100 credits.", "phone_credits", 100, ""),
            (8,  "C", "> Your reputation spreads through the scene. +15 rep.", "reputation", 15, ""),
            (8,  "Y", "> Found an old box of floppies in the corner. +30 disks.", "floppy_disks", 30, ""),
            (8,  "M", "> A scener shared source code with you. +40 src.", "source_code", 40, ""),
            (5,  "G", "> A grateful sysop sends beer. +4 beer.", "beer", 4, ""),
            (3,  "Y", "> You find working hardware in a skip. +20 hardware.", "hardware", 20, ""),
            (8,  "R", "> Phone company auditing. You lose 80 credits in hasty cover-up.", "phone_credits", -80, ""),
            (8,  "R", "> A floppy shipment went missing. -40 disks.", "floppy_disks", -40, ""),
            (6,  "R", "> Rival crew spread rumours about your crew. -10 rep.", "reputation", -10, ""),
            (5,  "R", "> Your modem burned out. -1 turn today.", "turns", -1, ""),
            (4,  "R", "> A hard drive crash wiped your work. -60 source code.", "source_code", -60, ""),
            (3,  "R", "> Tools got corrupted in a virus outbreak. -25 tools.", "tools", -25, ""),
            (10, "DG", "> Nothing unusual happened today.", "", 0, ""),
            (8,  "DG", "> You spend the day dialing random numbers. Nothing found.", "", 0, ""),
            (6,  "C", "> Word reaches you: someone dropped a 64K at a Norwegian party.", "", 0, ""),
            (5,  "DG", "> A new e-zine lands in your mailbox. Interesting reading.", "", 0, ""),
            (3,  "M", "> An old friend reconnects. They are back in the scene.", "", 0, ""),
        ]

    colour_map = {"G": ansi.G, "R": ansi.R, "Y": ansi.Y, "C": ansi.C, "M": ansi.M, "DG": ansi.DG}

    weights = [e[0] for e in events]
    if player.day > 35:
        weights = [w * (1.3 if events[i][1] == "R" else 1.0)
                   for i, w in enumerate(weights)]

    chosen = rng.choices(events, weights=weights, k=1)[0]
    weight, col, msg, res, amt = chosen[:6]

    curr_node = world.get_node_by_name(player.current_node)
    node_type = curr_node.node_type if curr_node else ""

    if chosen[5] and chosen[5] != node_type:
        return

    colour = colour_map.get(col, ansi.DG)
    ansi.result(f"{colour}{msg}{ansi.RST}")

    if res == "turns":
        player.use_turns(abs(amt) if amt < 0 else -amt)
    elif res and amt:
        player.adjust_resource(res, amt)

    ansi.draw_status(player, player.bbs_name)



if __name__ == "__main__":
    main()
