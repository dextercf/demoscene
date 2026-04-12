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

def action_travel(player, world, cfg, rng):
    page, pg_sz = 0, 7
    while True:
        disc = world.discovered_nodes()
        pg_cnt = max(1, (len(disc) + pg_sz - 1) // pg_sz)
        shown = disc[page * pg_sz:(page + 1) * pg_sz]
        ansi.screen_map(player, world, page, pg_sz)
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
            if not player.use_turns(1):
                ansi.result(f"{ansi.R}> Not enough turns to travel.{ansi.RST}")
                return
            player.current_node = node.name
            ansi.dial(ansi.RES_TOP + 1, 3, node.name)
            ansi.result(f"{ansi.C}> Connected: {ansi.W}{node.name}{ansi.RST}  {ansi.DG}{node.description}{ansi.RST}")
            if node.crew:
                ansi.result(f"  {ansi.R}{node.crew} is present here.{ansi.RST}")
            ansi.draw_status(player, player.bbs_name)
            time.sleep(1.0)
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
        key = ansi.get_key(valid_keys="1234567BSQbsq").upper()
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
        ).upper()

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
                ansi.result(f"{ansi.G}> Bought {qty} {name} for {total}c.{ansi.RST}")
                ansi.draw_status(player, player.bbs_name)
        elif action == "S":
            have = player.get_resource(res)
            qty  = min(qty, have)
            if qty <= 0:
                ansi.result(f"{ansi.R}> You don't have any {name}.{ansi.RST}")
            else:
                total = sell * qty
                player.adjust_resource(res, -qty)
                player.adjust_resource("phone_credits", total)
                ansi.result(f"{ansi.G}> Sold {qty} {name} for {total}c.{ansi.RST}")
                ansi.draw_status(player, player.bbs_name)

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
    ]

    ansi.screen_produce(player)
    key = ansi.get_key(valid_keys="12345Qq").upper()
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
    ansi.result(f"{ansi.DG}> Starting {label} production...{ansi.RST}")
    ansi.progress_bar(ansi.RES_TOP + 1, 3, "Compiling", width=24, duration=0.8, colour=ansi.G)
    ansi.progress_bar(ansi.RES_TOP + 2, 3, "Linking  ", width=24, duration=0.5, colour=ansi.G)
    ansi.progress_bar(ansi.RES_TOP + 3, 3, "Packing  ", width=24, duration=0.4, colour=ansi.C)

    luck   = rng.uniform(0.8, 1.2)

    # Production can fail — more complex demos have higher failure chance
    fail_chance = {
        "cracktro" : 0.05,
        "4k"       : 0.10,
        "64k"      : 0.15,
        "musicdisk": 0.10,
        "demo"     : 0.20,
    }
    if rng.random() < fail_chance.get(dkey, 0.10):
        ansi.result(f"{ansi.R}> Production failed. Compiler errors. Resources lost.{ansi.RST}")
        ansi.draw_status(player, player.bbs_name)
        return

    gained = int(base_rep * luck)
    player.adjust_resource("reputation", gained)
    player.demos_produced += 1

    ansi.result(f"{ansi.Y}> {label} released! +{gained} reputation.{ansi.RST}")
    if rng.random() < 0.4 and world.npc_crews:
        rival = rng.choice(world.npc_crews)
        ansi.result(f"  {ansi.DG}{rival.name} noticed your release.{ansi.RST}")
    ansi.draw_status(player, player.bbs_name)

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

    ansi.clear_screen()
    ansi.draw_art("raid")
    ansi.draw_divider(ansi.DIV_1)
    ansi.move(ansi.MENU_TOP, 1)
    ansi.writeln(f"  {ansi.C}SELECT TARGET:{ansi.RST}")

    for i, (crew, node) in enumerate(targets):
        agg = "!!!" if crew.aggression == 3 else ("!!" if crew.aggression == 2 else "!")
        col = ansi.R if crew.aggression == 3 else (ansi.Y if crew.aggression == 2 else ansi.W)
        ansi.move(ansi.MENU_TOP + 1 + i, 1)
        ansi.writeln(
            f"  [{i+1:02d}] {col}{crew.name:<16}{ansi.RST}"
            f"  at {ansi.B}{node.name:<24}{ansi.RST}"
            f"  {ansi.DG}aggression: {agg}{ansi.RST}")

    ansi.draw_divider(ansi.DIV_3)
    ansi.clear_zone(ansi.RES_TOP, ansi.RES_BOT)
    ansi.write_at(ansi.RES_TOP, 1, f"  {ansi.DG}Enter number, or 00 to cancel{ansi.RST}")

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
    key = ansi.get_key(valid_keys="ASHQashq").upper()

    if key == "Q":
        player.turns_remaining += 3
        return

    result = combat.resolve_raid(player, target_crew, key, rng)

    ansi.result(f"{ansi.DG}> Launching raid on {target_crew.name}...{ansi.RST}")
    ansi.animate_combat_bars(ansi.RES_TOP + 1, result.player_power, result.enemy_power)
    time.sleep(0.3)

    combat.apply_raid_result(player, result)

    # Store counter_risk on player so end_day() can act on it
    player.pending_counter_raid = result.counter_risk and result.victory

    if result.victory:
        ansi.result(f"{ansi.G}> RAID SUCCESSFUL! +{combat.REP_WIN} rep{ansi.RST}")
        if result.loot:
            from playermod import RESOURCE_NAMES
            parts = [f"{amt} {RESOURCE_NAMES.get(res, res)}"
                     for res, amt in result.loot.items()]
            ansi.result(f"  {ansi.Y}Looted: {', '.join(parts[:3])}{ansi.RST}")
        if result.counter_risk:
            ansi.result(f"  {ansi.R}Warning: {target_crew.name} may counter-raid.{ansi.RST}")
    else:
        ansi.result(f"{ansi.R}> RAID FAILED — {target_crew.name} repelled your crew.{ansi.RST}")
        if result.losses:
            from playermod import RESOURCE_NAMES
            parts = [f"{amt} {RESOURCE_NAMES.get(res, res)}"
                     for res, amt in result.losses.items()]
            ansi.result(f"  {ansi.R}Lost: {', '.join(parts)}{ansi.RST}")

    ansi.result(f"  {ansi.DG}{result.message}{ansi.RST}")
    ansi.draw_status(player, player.bbs_name)

# ---------------------------------------------------------------------------
# Action: Defend
# ---------------------------------------------------------------------------

def action_defend(player, world, cfg, rng):
    if not player.use_turns(1):
        ansi.result(f"{ansi.R}> Not enough turns.{ansi.RST}")
        return
    boost = rng.randint(5, 15)
    player.defense = min(100, player.defense + boost)
    ansi.result(
        f"{ansi.G}> Home board fortified. "
        f"Defense +{boost} (now {player.defense}).{ansi.RST}")
    ansi.draw_status(player, player.bbs_name)

# ---------------------------------------------------------------------------
# Action: Courier missions
# ---------------------------------------------------------------------------

def action_crew_screen(player):
    ansi.screen_crew(player)
    ansi.get_key(valid_keys="Qq")
    """Show the mission board and let player accept/decline."""
    if daily_mission is None:
        ansi.result(f"{ansi.DG}> No courier missions available today.{ansi.RST}")
        return

    if daily_mission.is_expired(player.day):
        ansi.result(f"{ansi.R}> The courier posting has expired.{ansi.RST}")
        return

    if daily_mission.accepted:
        # Already accepted — show delivery status
        if player.current_node == daily_mission.dest:
            # Player is at destination — deliver
            ok = couriermod.deliver_mission(player, daily_mission)
            if ok:
                ansi.result(f"{ansi.G}> Package delivered to {daily_mission.dest}!{ansi.RST}")
                ansi.result(f"  {ansi.Y}Reward: {daily_mission.reward_summary()}{ansi.RST}")
                ansi.draw_status(player, player.bbs_name)
            else:
                ansi.result(f"{ansi.R}> Delivery failed.{ansi.RST}")
        else:
            ansi.screen_courier_active(player, daily_mission)
            ansi.result(
                f"{ansi.DG}> Travel to {ansi.C}{daily_mission.dest}{ansi.DG}"
                f" to complete delivery.{ansi.RST}")
        return

    # Show the mission board
    ansi.screen_courier_board(player, daily_mission)
    key = ansi.get_key(valid_keys="AQaq").upper()
    if key == "Q":
        return

    # Accept
    if not player.use_turns(1):
        ansi.result(f"{ansi.R}> Not enough turns.{ansi.RST}")
        return

    ok = couriermod.accept_mission(player, daily_mission)
    if not ok:
        ansi.result(
            f"{ansi.R}> Not enough {daily_mission.cargo_key.replace('_', ' ')} "
            f"to accept this mission (need {daily_mission.cargo_amt}).{ansi.RST}")
        player.turns_remaining += 1  # refund turn
    else:
        ansi.result(
            f"{ansi.G}> Mission accepted. Travel to "
            f"{ansi.C}{daily_mission.dest}{ansi.G} to deliver.{ansi.RST}")
        ansi.draw_status(player, player.bbs_name)


# ---------------------------------------------------------------------------
# Action: Messages
# ---------------------------------------------------------------------------

def action_messages(player, world, cfg):
    msgs = _generate_messages(player, world, player.day)
    ansi.screen_messages(msgs, player)
    ansi.get_key(valid_keys="Qq")

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
        _random_event(player, world, rng)

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
        key = ansi.get_key(valid_keys="ETPRDBMSCWQetprdbmscwq").upper()

        if key == "E":
            action_explore(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "T":
            action_travel(player, world, cfg, rng)
            # Auto-deliver courier mission if player arrived at destination
            if (daily_mission and daily_mission.accepted
                    and not daily_mission.delivered
                    and player.current_node == daily_mission.dest):
                ok = couriermod.deliver_mission(player, daily_mission)
                if ok:
                    ansi.result(
                        f"{ansi.G}> Auto-delivery: package delivered to "
                        f"{daily_mission.dest}! "
                        f"Reward: {daily_mission.reward_summary()}{ansi.RST}")
                    ansi.draw_status(player, player.bbs_name)
            ansi.screen_hq(player)
        elif key == "P":
            action_produce(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "R":
            action_raid(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "D":
            action_defend(player, world, cfg, rng)
        elif key == "B":
            action_trade(player, world, cfg, rng)
            ansi.screen_hq(player)
        elif key == "C":
            action_courier(player, world, cfg, rng, daily_mission)
            ansi.screen_hq(player)
        elif key == "W":
            action_crew_screen(player)
            ansi.screen_hq(player)
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
            time.sleep(1.0)
            return False

        if player.turns_remaining <= 0:
            # Expire undelivered missions at day end
            if daily_mission and daily_mission.accepted and not daily_mission.delivered:
                couriermod.fail_mission(player, daily_mission)
                ansi.result(f"{ansi.R}> Courier mission expired. Cargo returned. -10 rep.{ansi.RST}")
            ansi.result(f"{ansi.DG}> Day {player.day} is over. Get some sleep.{ansi.RST}")
            time.sleep(0.8)
            end_day(player, world, cfg, rng)
            daily_mission = couriermod.get_daily_mission(player, world, rng)
            ansi.screen_hq(player)

    return True

# ---------------------------------------------------------------------------
# Title / new game
# ---------------------------------------------------------------------------

def title_loop(door_info, cfg):
    while True:
        ansi.screen_title()
        key = ansi.get_key(valid_keys="NCSQncsq").upper()
        if key == "Q":
            ansi.result(f"{ansi.DG}Goodbye. The scene never sleeps.{ansi.RST}")
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
            ansi.result(f"{ansi.DG}No save found. Starting new game...{ansi.RST}")
            time.sleep(1.0)
            return _new_game(door_info, cfg)
        elif key == "N":
            return _new_game(door_info, cfg)


def _new_game(door_info, cfg):
    ansi.clear_screen()
    ansi.draw_art("title")
    ansi.draw_divider(ansi.DIV_1)
    ansi.clear_zone(ansi.MENU_TOP, ansi.MENU_BOT)
    ansi.draw_divider(ansi.DIV_3)
    ansi.clear_zone(ansi.RES_TOP, ansi.RES_BOT)
    ansi.draw_divider(ansi.STATUS_DIV)
    ansi.clear_line(ansi.STATUS)

    ansi.write_at(ansi.MENU_TOP,     1, f"  {ansi.C}Welcome to {GAME_TITLE}{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 1, 1, f"  {ansi.DG}A {DEVELOPER} production{ansi.RST}")
    ansi.write_at(ansi.MENU_TOP + 2, 1, f"  {ansi.W}Handle: {ansi.G}{door_info.handle}{ansi.RST}")

    time.sleep(0.3)

    p = playermod.Player()
    p.handle   = door_info.handle
    p.bbs_name = cfg_str(cfg, "bbs", "bbs_name", door_info.bbs_name)
    p.apply_config(cfg)

    ansi.write_at(ansi.RES_TOP, 1, f"  {ansi.DG}Choose your crew name (max 20 chars){ansi.RST}")
    ansi.move(ansi.RES_TOP + 1, 1)
    crew = ansi.get_input("  Crew name: ")
    p.crew_name = crew[:20] if crew else f"{p.handle}'s Crew"

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

    ansi.show_cursor()
    io = socketio.get_io()
    if io:
        io.getkey()
    ansi.hide_cursor()

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

    player, world = title_loop(door_info, cfg)
    if player is None:
        _exit_cleanly(io)
        return

    game_ended = hq_loop(player, world, cfg, rng)

    if game_ended:
        player.calculate_score()
        playermod.submit_score(player)
        rank = playermod.get_player_rank(player.handle)
        ansi.screen_game_over(player, rank)
        ansi.get_key()

    _exit_cleanly(io)


def _exit_cleanly(io):
    ansi.show_cursor()
    ansi.clear_screen()
    time.sleep(2.0)
    try:
        sock = getattr(io, 'sock', None)
        if sock:
            sock.setblocking(True)
    except Exception:
        pass
    if io:
        io.close()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def _random_event(player, world, rng):
    # Each entry: (weight, colour_code, message, effect_fn)
    # Weight 10 = common, 5 = uncommon, 2 = rare
    # Mix: ~6 positive, ~6 negative, ~6 neutral/flavour
    events = [
        # --- Positive ---
        (10, ansi.G,  "> A courier dropped off a package. +50 floppy disks.",
         lambda: player.adjust_resource("floppy_disks", 50)),
        (10, ansi.G,  "> Someone paid for your last demo. +100 credits.",
         lambda: player.adjust_resource("phone_credits", 100)),
        (8,  ansi.C,  "> Your reputation spreads through the scene. +15 rep.",
         lambda: player.adjust_resource("reputation", 15)),
        (8,  ansi.Y,  "> Found an old box of floppies in the corner. +30 disks.",
         lambda: player.adjust_resource("floppy_disks", 30)),
        (8,  ansi.M,  "> A scener shared source code with you. +40 src.",
         lambda: player.adjust_resource("source_code", 40)),
        (5,  ansi.G,  "> A grateful sysop sends beer. +4 beer.",
         lambda: player.adjust_resource("beer", 4)),
        (3,  ansi.Y,  "> You find working hardware in a skip. +20 hardware.",
         lambda: player.adjust_resource("hardware", 20)),
        # --- Negative ---
        (8,  ansi.R,  "> Phone company auditing. You lose 80 credits in hasty cover-up.",
         lambda: player.adjust_resource("phone_credits", -80)),
        (8,  ansi.R,  "> A floppy shipment went missing. -40 disks.",
         lambda: player.adjust_resource("floppy_disks", -40)),
        (6,  ansi.R,  "> Rival crew spread rumours about your crew. -10 rep.",
         lambda: player.adjust_resource("reputation", -10)),
        (5,  ansi.R,  "> Your modem burned out. -1 turn today.",
         lambda: player.use_turns(1)),
        (4,  ansi.R,  "> A hard drive crash wiped your work. -60 source code.",
         lambda: player.adjust_resource("source_code", -60)),
        (3,  ansi.R,  "> Tools got corrupted in a virus outbreak. -25 tools.",
         lambda: player.adjust_resource("tools", -25)),
        # --- Neutral / flavour ---
        (10, ansi.DG, "> Nothing unusual happened today.",
         lambda: None),
        (8,  ansi.DG, "> You spend the day dialing random numbers. Nothing found.",
         lambda: None),
        (6,  ansi.C,  "> Word reaches you: someone dropped a 64K at a Norwegian party.",
         lambda: None),
        (5,  ansi.DG, "> A new e-zine lands in your mailbox. Interesting reading.",
         lambda: None),
        (3,  ansi.M,  "> An old friend reconnects. They're back in the scene.",
         lambda: None),
    ]

    # Weight the draw — also slightly bias negative events in late game
    weights = [e[0] for e in events]
    if player.day > 35:
        # Increase negative event weight in last act
        weights = [w * (1.3 if events[i][1] == ansi.R else 1.0)
                   for i, w in enumerate(weights)]

    chosen = rng.choices(events, weights=weights, k=1)[0]
    _, col, msg, effect = chosen
    ansi.result(f"{col}{msg}{ansi.RST}")
    effect()
    ansi.draw_status(player, player.bbs_name)


_MSG_TEMPLATES = [
    # --- Always available ---
    ("{crew} thinks your crew is a bunch of lamers. Prove them wrong.",
     lambda p, w, r: r.choice(w.npc_crews).name if w.npc_crews else "Unknown", "Taunt"),
    ("We heard {crew} is planning a raid on your home board. Watch out.",
     lambda p, w, r: r.choice(w.npc_crews).name if w.npc_crews else "Unknown", "Warning"),
    ("Rumour has it {crew} just dropped a killer 64K.",
     lambda p, w, r: r.choice(w.npc_crews).name if w.npc_crews else "Unknown", "Scene News"),
    ("A new node was spotted deep in the network. Very deep.",
     lambda p, w, r: None, "Intel"),
    ("The phone lines are buzzing. Something big is about to drop.",
     lambda p, w, r: None, "Rumour"),
    ("h0ffman is rumoured to be DJing at the next party.",
     lambda p, w, r: None, "Party Buzz"),
    ("Gates of Asgard is said to be back online. Nobody can confirm it.",
     lambda p, w, r: None, "Rumour"),
    ("SysOp of The Dungeon got busted. Board is gone. Moment of silence.",
     lambda p, w, r: None, "Scene News"),
    ("Disk couriers wanted. Good pay. No questions asked.",
     lambda p, w, r: None, "Opportunity"),
    ("Someone's releasing a new art pack. ACiD vs iCE, round 467.",
     lambda p, w, r: None, "Scene News"),
    ("Your crew's name was mentioned in a trade channel. People are watching.",
     lambda p, w, r: None, "Intel"),
    # --- Early game only (day <= 15) ---
    ("Welcome to the scene. Don't screw it up.",
     lambda p, w, r: None if p.day <= 15 else "__skip__", "Welcome"),
    ("A veteran scener offers advice: explore before you trade.",
     lambda p, w, r: None if p.day <= 15 else "__skip__", "Tip"),
    # --- Mid game only (day 15-35) ---
    ("{crew} has been unusually quiet lately. Suspiciously quiet.",
     lambda p, w, r: r.choice(w.npc_crews).name if w.npc_crews and 15 <= p.day <= 35 else "__skip__", "Intel"),
    ("The network is expanding. New nodes reported in the deep zones.",
     lambda p, w, r: None if 15 <= p.day <= 35 else "__skip__", "Intel"),
    # --- Late game only (day > 35) ---
    ("Only {days} days left. The scene is watching. Make it count.",
     lambda p, w, r: str(50 - p.day) if p.day > 35 else "__skip__", "Countdown"),
    ("{crew} is pulling ahead on reputation. Time to act.",
     lambda p, w, r: r.choice(w.npc_crews).name if w.npc_crews and p.day > 35 else "__skip__", "Warning"),
]


def _generate_messages(player, world, current_day, count=7):
    msgs = []
    rng  = random.Random(current_day + hash(player.handle))
    pool = list(_MSG_TEMPLATES)
    rng.shuffle(pool)

    for template, crew_fn, subject in pool:
        try:
            crew_val = crew_fn(player, world, rng)
        except Exception:
            crew_val = None

        if crew_val == "__skip__":
            continue

        sender = "ANONYMOUS"
        if world.npc_crews:
            sc = rng.choice(world.npc_crews)
            sender = (f"{rng.choice(['DARK','ACID','FROST','BYTE','NEON'])}"
                      f"/{sc.name[:8]}")

        try:
            text = template.format(
                crew  = crew_val or (world.npc_crews[0].name if world.npc_crews else "Unknown"),
                node  = (rng.choice(world.discovered_nodes()).name
                         if world.discovered_nodes() else "Unknown Node"),
                party = "the next party",
                days  = crew_val if subject == "Countdown" else "?",
            )
        except (KeyError, IndexError):
            text = template

        day_offset = rng.randint(max(1, current_day - 4), current_day)
        msgs.append({
            "from":    sender,
            "subject": text[:50],
            "day":     day_offset,
            "new":     day_offset >= current_day - 1,
        })
        if len(msgs) >= count:
            break

    msgs.sort(key=lambda m: m["day"], reverse=True)
    return msgs


if __name__ == "__main__":
    main()
