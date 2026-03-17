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

GAME_TITLE, DEVELOPER, VERSION = "Demoscene: The Exploration of Art", "Cellfish", "0.1"

def load_config():
    cfg = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(__file__), "config.ini")
    if os.path.isfile(path): cfg.read(path, encoding="cp437")
    cfg["cellfish"] = {"game_title": GAME_TITLE, "developer": DEVELOPER, "version": VERSION}
    return cfg

def cfg_int(cfg, sec, key, d):
    try: return int(cfg[sec].get(key, d))
    except (KeyError, ValueError): return d

def action_explore(player, world, cfg, rng):
    while True:
        ansi.screen_explore(player)
        key = ansi.get_key(valid_keys="XQ")
        if key == "Q": return
        if player.use_turns(2):
            curr = world.get_node_by_name(player.current_node)
            found = world.explore(curr.index if curr else 0, rng)
            ansi.result(f"Found: {found.name}" if found else "Nothing found.")
        else: ansi.result("Not enough turns.", ansi.R)
        ansi.draw_status(player, player.bbs_name)

def action_travel(player, world, cfg, rng):
    page, pg_sz = 0, 5
    while True:
        disc = world.discovered_nodes()
        pg_cnt = max(1, (len(disc) + pg_sz - 1) // pg_sz)
        shown = disc[page*pg_sz : (page+1)*pg_sz]
        ansi.screen_map(player, world, page, pg_sz)
        key = ansi.get_key().upper()
        if key == "Q": return
        if key.isdigit() and 0 < int(key) <= len(shown):
            node = shown[int(key)-1]; break
    if player.use_turns(1):
        player.current_node = node.name
        ansi.dial(ansi.RES_TOP + 1, 3, node.name)
        ansi.draw_status(player); time.sleep(1.0)

def hq_loop(player, world, cfg, rng):
    game_len = cfg_int(cfg, "gameplay", "game_length_days", 50)
    ansi.screen_hq(player)
    while not player.is_game_over(game_len):
        key = ansi.get_key(valid_keys="ETQ")
        if key == "E": action_explore(player, world, cfg, rng); ansi.screen_hq(player)
        elif key == "T": action_travel(player, world, cfg, rng); ansi.screen_hq(player)
        elif key == "Q": player.save(); world.save(player.handle); return False
        if player.turns_remaining <= 0:
            player.end_day(cfg_int(cfg, "gameplay", "action_points_per_day", 10))
            ansi.screen_hq(player)
    return True

def title_loop(door_info, cfg):
    while True:
        ansi.screen_title()
        key = ansi.get_key(valid_keys="NCQ")
        if key == "Q": return None, None
        elif key == "N": 
            # Simplified New Game
            p = playermod.Player(); p.handle = door_info.handle
            p.apply_config(cfg); w = worldmod.World()
            w.generate(p.handle, door_info.bbs_name, cfg)
            return p, w
        elif key == "C":
            p = playermod.Player(); p.handle = door_info.handle
            if p.load():
                w = worldmod.World()
                if w.load(p.handle): return p, w
            time.sleep(1.0)

def main():
    cfg = load_config()
    s_h = socketio.parse_socket_handle()
    socketio.init(s_h)
    d_i = door.load()
    rng = random.Random(); rng.seed(hash(d_i.handle))
    
    player, world = title_loop(d_i, cfg)
    if player: hq_loop(player, world, cfg, rng)
    
    ansi.show_cursor(); ansi.clear_screen(); time.sleep(1.0)

if __name__ == "__main__": main()