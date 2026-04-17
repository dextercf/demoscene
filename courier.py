"""
courier.py — Courier mission system
Demoscene: The Exploration of Art
A Cellfish Production

Disk couriers were a real part of the demoscene — people who physically
(or digitally) transported new releases between BBSes. This module gives
the player optional side-missions: carry a package from one node to
another within a time limit (turns), earn phone credits and bonus resources.

Missions are generated fresh each day and expire at day end.
The player can hold one active mission at a time.

Usage (from game.py):
    import courier
    mission = courier.get_daily_mission(player, world, rng)
    if mission:
        courier.screen_mission_board(player, mission)
        ...
    courier.deliver_mission(player, mission, world)
"""

import random

# ---------------------------------------------------------------------------
# Mission definitions — templates for variety
# ---------------------------------------------------------------------------

_MISSION_TEMPLATES = [
    {
        "label"     : "Disk run",
        "desc"      : "Courier a box of floppies from {origin} to {dest}.",
        "cargo_key" : "floppy_disks",
        "cargo_amt" : 50,
        "turn_cost" : 2,    # turns to complete (travel + 1)
        "reward_crd": 120,
        "reward_res": {},
        "difficulty": 1,
    },
    {
        "label"     : "Source drop",
        "desc"      : "Move a source archive from {origin} to {dest}. No questions.",
        "cargo_key" : "source_code",
        "cargo_amt" : 80,
        "turn_cost" : 2,
        "reward_crd": 160,
        "reward_res": {"artwork": 20},
        "difficulty": 1,
    },
    {
        "label"     : "MOD transport",
        "desc"      : "Deliver a new MOD music pack to {dest} before the party.",
        "cargo_key" : "mod_music",
        "cargo_amt" : 60,
        "turn_cost" : 3,
        "reward_crd": 200,
        "reward_res": {"reputation": 20},
        "difficulty": 2,
    },
    {
        "label"     : "Hardware haul",
        "desc"      : "Lug a box of gear from {origin} to {dest}. Heavy stuff.",
        "cargo_key" : "hardware",
        "cargo_amt" : 30,
        "turn_cost" : 3,
        "reward_crd": 250,
        "reward_res": {"tools": 15},
        "difficulty": 2,
    },
    {
        "label"     : "Elite package",
        "desc"      : "Sealed package. Don't open it. {origin} to {dest}. Urgent.",
        "cargo_key" : "tools",
        "cargo_amt" : 40,
        "turn_cost" : 4,
        "reward_crd": 350,
        "reward_res": {"reputation": 40},
        "difficulty": 3,
    },
]


# ---------------------------------------------------------------------------
# Mission class
# ---------------------------------------------------------------------------

class Mission:
    def __init__(self, template, origin_node, dest_node, expires_day):
        self.label       = template["label"]
        self.desc        = template["desc"].format(
                               origin=origin_node.name,
                               dest=dest_node.name)
        self.cargo_key   = template["cargo_key"]
        self.cargo_amt   = template["cargo_amt"]
        self.turn_cost   = template["turn_cost"]
        self.reward_crd  = template["reward_crd"]
        self.reward_res  = dict(template["reward_res"])
        self.difficulty  = template["difficulty"]
        self.origin      = origin_node.name
        self.dest        = dest_node.name
        self.expires_day = expires_day
        self.accepted    = False
        self.delivered   = False

    def is_expired(self, current_day):
        return current_day > self.expires_day

    def reward_summary(self):
        parts = [f"{self.reward_crd} credits"]
        for key, amt in self.reward_res.items():
            parts.append(f"+{amt} {key.replace('_', ' ')}")
        return ", ".join(parts)


# ---------------------------------------------------------------------------
# Mission generation
# ---------------------------------------------------------------------------

def get_daily_mission(player, world, rng=None):
    """
    Generate one courier mission for the current day.
    Returns a Mission, or None if conditions aren't met.

    Uses a deterministic RNG seeded from handle+day so the same
    mission is offered each session on the same day (reload-proof).
    Difficulty scales with player day so early missions are easy.
    """
    disc = [n for n in world.discovered_nodes() if n.name != player.current_node]
    if len(disc) < 2:
        return None

    mission_rng = random.Random(hash(player.handle) ^ player.day)

    if player.day <= 10:
        max_diff = 1
    elif player.day <= 25:
        max_diff = 2
    else:
        max_diff = 3

    eligible = [t for t in _MISSION_TEMPLATES if t["difficulty"] <= max_diff]
    template = mission_rng.choice(eligible)

    mission_rng.shuffle(disc)
    origin = disc[0]
    dest   = disc[1] if len(disc) > 1 and disc[1] != origin else (disc[2] if len(disc) > 2 else None)

    if not dest or origin == dest:
        return None

    mission = Mission(template, origin, dest, player.day + 1)
    return mission


# ---------------------------------------------------------------------------
# Accept / deliver
# ---------------------------------------------------------------------------

def accept_mission(player, mission):
    """
    Player picks up the cargo at origin node.
    Deducts cargo from player inventory (they're carrying it).
    Returns True if player has enough resources, False otherwise.
    """
    if player.get_resource(mission.cargo_key) < mission.cargo_amt:
        return False
    player.adjust_resource(mission.cargo_key, -mission.cargo_amt)
    mission.accepted = True
    return True


def deliver_mission(player, mission):
    """
    Complete delivery at destination node.
    Rewards are applied here. Cargo is 'delivered' (not returned to player).
    Returns True on success.
    """
    if not mission.accepted or mission.delivered:
        return False
    player.adjust_resource("phone_credits", mission.reward_crd)
    for key, amt in mission.reward_res.items():
        player.adjust_resource(key, amt)
    mission.delivered = True
    return True


def fail_mission(player, mission):
    """
    Called when a mission expires or is abandoned.
    Returns cargo to player (they still have it, just failed to deliver).
    """
    if mission.accepted and not mission.delivered:
        player.adjust_resource(mission.cargo_key, mission.cargo_amt)
        player.adjust_resource("reputation", -10)
        mission.accepted = False


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import types, sys

    print("=== courier.py self-test ===\n")

    rng = random.Random(42)

    # Mock player
    p = types.SimpleNamespace(
        handle="AXON", day=8, current_node="Cellfish BBS",
        phone_credits=200, floppy_disks=200, source_code=200,
        mod_music=100, hardware=50, tools=40, reputation=50, artwork=30,
        _caps={},
    )
    def adj(k, v):
        current = getattr(p, k, 0)
        setattr(p, k, max(0, current + v))
    def get_res(k):
        return getattr(p, k, 0)
    p.adjust_resource = adj
    p.get_resource = get_res

    # Mock world with some nodes
    NodeMock = types.SimpleNamespace
    nodes = [
        NodeMock(name="Cellfish BBS",   discovered=True),
        NodeMock(name="Null Pointer",   discovered=True),
        NodeMock(name="The Blitter",    discovered=True),
        NodeMock(name="SID Station",    discovered=False),
    ]

    class MockWorld:
        def discovered_nodes(self):
            return [n for n in nodes if n.discovered]

    world = MockWorld()

    m = get_daily_mission(p, world, rng)
    if m:
        print(f"Mission     : {m.label}")
        print(f"Description : {m.desc}")
        print(f"Cargo       : {m.cargo_amt} {m.cargo_key}")
        print(f"Turn cost   : {m.turn_cost}")
        print(f"Reward      : {m.reward_summary()}")
        print(f"Expires day : {m.expires_day}")
        print()

        # Accept
        ok = accept_mission(p, m)
        print(f"Accept ok   : {ok}  (floppy_disks now: {p.floppy_disks})")

        # Deliver
        ok = deliver_mission(p, m)
        print(f"Deliver ok  : {ok}  (credits now: {p.phone_credits})")
    else:
        print("No mission generated (not enough nodes).")
