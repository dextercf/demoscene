"""
combat.py — Raid and combat resolution engine
Demoscene: The Exploration of Art
A Cellfish Production

Handles all combat between the player's crew and NPC rival crews.
Separated from game.py to keep combat logic clean and easy to balance.

Combat is turn-based within a raid — the player picks a tactic,
the engine resolves the outcome based on stats plus a luck factor,
and resources are transferred accordingly.

This module is imported by game.py — it does not run standalone
as a game component, but includes a self-test at the bottom.
"""

import random

# ---------------------------------------------------------------------------
# Combat constants — tweak these to balance the game
# ---------------------------------------------------------------------------

# Base power contributed by each resource point the player has
TOOLS_WEIGHT    = 2.0   # tools are the primary combat resource
DEFENSE_WEIGHT  = 0.5   # defense contributes a little to attack power
HARDWARE_WEIGHT = 0.3   # hardware gives a small combat edge

# Luck range — how much random variance affects each combat roll
LUCK_MIN = 0.75
LUCK_MAX = 1.25

# Loot percentage — how much of the enemy's resources the winner takes
LOOT_FRACTION = 0.33

# Reputation effects
REP_WIN  =  30   # reputation gained on a successful raid
REP_LOSS = -20   # reputation lost on a failed raid
REP_DEFEND_WIN = 15  # reputation gained when successfully defending

# Defense decay — each day undefended, home board loses this much defense
DEFENSE_DECAY = 2

# ---------------------------------------------------------------------------
# Tactic definitions
# ---------------------------------------------------------------------------

TACTICS = {
    "A": {
        "label"      : "All-out assault",
        "desc"       : "Go in hard. High risk, high reward.",
        "atk_mult"   : 1.30,
        "def_mult"   : 0.80,   # you leave yourself open
        "loot_mult"  : 1.20,   # bigger loot if you win
        "detect_mod" : 0.20,   # higher chance of being noticed by others
    },
    "S": {
        "label"      : "Sneak raid",
        "desc"       : "Quiet and careful. Balanced risk.",
        "atk_mult"   : 1.05,
        "def_mult"   : 1.05,
        "loot_mult"  : 0.90,
        "detect_mod" : -0.10,  # less likely to be noticed
    },
    "H": {
        "label"      : "Hit and run",
        "desc"       : "Strike fast, retreat before they can respond.",
        "atk_mult"   : 0.85,
        "def_mult"   : 1.20,   # you are harder to counter-raid after
        "loot_mult"  : 0.70,   # less loot — you leave quickly
        "detect_mod" : -0.05,
    },
}


# ---------------------------------------------------------------------------
# Combat result dataclass (plain class for Python 3 compatibility)
# ---------------------------------------------------------------------------

class CombatResult:
    def __init__(self):
        self.victory        = False
        self.tactic         = ""
        self.player_power   = 0
        self.enemy_power    = 0
        self.loot           = {}        # {resource: amount}
        self.losses         = {}        # {resource: amount} lost on defeat
        self.rep_change     = 0
        self.message        = ""
        self.counter_risk   = False     # enemy may counter-raid after this
        self.flavour        = ""        # narrative line for the message board

    def __repr__(self):
        return (f"CombatResult(victory={self.victory}, "
                f"tactic={self.tactic!r}, "
                f"player={self.player_power}, enemy={self.enemy_power}, "
                f"loot={self.loot}, rep={self.rep_change})")


# ---------------------------------------------------------------------------
# Core combat resolver
# ---------------------------------------------------------------------------

def resolve_raid(player, npc_crew, tactic_key, rng=None):
    """
    Resolve a raid attempt by the player against an NPC crew.

    player    — playermod.Player instance
    npc_crew  — worldmod.NpcCrew instance
    tactic    — "A", "S", or "H"
    rng       — random.Random instance (uses module-level random if None)

    Returns a CombatResult.
    """
    if rng is None:
        rng = random.Random()

    tactic = TACTICS.get(tactic_key.upper(), TACTICS["S"])
    result = CombatResult()
    result.tactic = tactic_key.upper()

    # --- Player combat power ---
    base_player = (
        player.tools    * TOOLS_WEIGHT  +
        player.defense  * DEFENSE_WEIGHT +
        player.hardware * HARDWARE_WEIGHT +
        20  # base floor so new players aren't helpless
    )
    player_luck   = rng.uniform(LUCK_MIN, LUCK_MAX)
    result.player_power = int(base_player * tactic["atk_mult"] * player_luck)

    # --- Enemy combat power — modified by behaviour ---
    base_enemy = npc_crew.strength + (npc_crew.defence * 0.5) \
        if hasattr(npc_crew, 'defence') else npc_crew.strength + (npc_crew.defense * 0.5)

    behaviour = getattr(npc_crew, 'behaviour', 'producer')
    if behaviour == 'raider':
        base_enemy *= 1.20    # raiders hit harder
    elif behaviour == 'trader':
        base_enemy *= 0.80    # traders are weak fighters
    elif behaviour == 'artist':
        base_enemy *= 0.75    # artists are even weaker fighters
    elif behaviour == 'party':
        base_enemy *= 0.85    # party crews are mediocre fighters
    # producer is baseline (1.0x)

    enemy_luck = rng.uniform(LUCK_MIN, LUCK_MAX)
    result.enemy_power = int(base_enemy * enemy_luck)

    # --- Resolution ---
    if result.player_power >= result.enemy_power:
        result.victory = True
        result.rep_change = REP_WIN

        # Calculate loot — producers protect source_code, artists protect artwork/music
        loot_keys = ["phone_credits", "floppy_disks", "source_code",
                     "artwork", "mod_music", "hardware", "tools"]
        for key in loot_keys:
            available = npc_crew.resources.get(key, 0)
            if available > 0:
                # Behaviour-specific loot protection
                protection = 1.0
                if behaviour == 'producer' and key == 'source_code':
                    protection = 0.5   # producers hide their source
                elif behaviour == 'artist' and key in ('artwork', 'mod_music'):
                    protection = 0.5   # artists hide their art
                elif behaviour == 'raider' and key == 'tools':
                    protection = 0.7   # raiders guard their tools
                taken = int(available * LOOT_FRACTION * tactic["loot_mult"] * protection)
                taken = max(0, min(taken, available))
                if taken > 0:
                    taken = int(taken * rng.uniform(0.7, 1.0))
                    result.loot[key] = taken

        # Remove looted resources from NPC
        for key, amount in result.loot.items():
            npc_crew.resources[key] = max(
                0, npc_crew.resources.get(key, 0) - amount
            )

        # Counter-raid risk — aggressive crews hit back; raiders always more likely
        counter_chance = 0.15 + (npc_crew.aggression * 0.10)
        counter_chance += tactic.get("detect_mod", 0)
        if behaviour == 'raider':
            counter_chance += 0.15   # raiders are vindictive
        elif behaviour == 'trader':
            counter_chance -= 0.10   # traders prefer to cut losses
        result.counter_risk = rng.random() < counter_chance

        result.message = _victory_message(npc_crew.name, result.loot, rng)
        result.flavour = (
            f"AXON's crew hit {npc_crew.name} hard. "
            f"{'They may be planning revenge.' if result.counter_risk else 'Clean getaway.'}"
        )

    else:
        result.victory    = False
        result.rep_change = REP_LOSS

        # Player loses some resources on defeat
        loss_credits = rng.randint(20, 80)
        loss_disks   = rng.randint(0,  40)
        actual_credits = min(loss_credits, player.phone_credits)
        actual_disks   = min(loss_disks,   player.floppy_disks)
        result.losses = {
            "phone_credits": actual_credits,
            "floppy_disks" : actual_disks,
        }

        # Enemy gets stronger from winning, but capped
        npc_crew.strength = min(90, npc_crew.strength + rng.randint(2, 6))

        result.message = _defeat_message(npc_crew.name, result.losses, rng)
        result.flavour = (
            f"{npc_crew.name} repelled the raid. "
            f"They're feeling bold now."
        )

    return result


def apply_raid_result(player, result):
    """
    Apply a CombatResult to the player — transfer resources and rep.
    Call this after resolve_raid once you've shown the result to the player.
    """
    if result.victory:
        for key, amount in result.loot.items():
            player.adjust_resource(key, amount)
        player.raids_won += 1
    else:
        for key, amount in result.losses.items():
            player.adjust_resource(key, -amount)
        player.raids_lost += 1

    player.adjust_resource("reputation", result.rep_change)


# ---------------------------------------------------------------------------
# Defence resolver — called when an NPC crew raids the player's home board
# ---------------------------------------------------------------------------

def resolve_defence(player, npc_crew, rng=None):
    """
    Resolve an NPC crew raiding the player's home board overnight.

    Returns a dict describing what happened:
    {
        "attacker": crew name,
        "success" : True if attacker succeeded,
        "losses"  : {resource: amount} lost by player,
        "rep_change": int,
        "message" : str,
    }
    """
    if rng is None:
        rng = random.Random()

    # Player defense power
    defense_power = (
        player.defense * 1.5 +
        player.hardware * 0.4 +
        rng.randint(10, 30)
    )

    # Attacker power
    attack_power = (
        npc_crew.strength +
        rng.randint(5, 25)
    )

    if defense_power >= attack_power:
        # Defender wins
        rep = REP_DEFEND_WIN
        msg = (f"{npc_crew.name} tried to raid your home board overnight "
               f"but your defenses held. +{rep} rep.")
        return {
            "attacker"  : npc_crew.name,
            "success"   : False,
            "losses"    : {},
            "rep_change": rep,
            "message"   : msg,
        }
    else:
        # Attacker wins
        loss_credits = min(rng.randint(20, 100), player.phone_credits)
        loss_disks   = min(rng.randint(10,  60), player.floppy_disks)
        rep          = -15

        player.adjust_resource("phone_credits", -loss_credits)
        player.adjust_resource("floppy_disks",  -loss_disks)
        player.adjust_resource("reputation",     rep)

        msg = (f"{npc_crew.name} raided your home board! "
               f"Lost {loss_credits} credits and {loss_disks} disks.")
        return {
            "attacker"  : npc_crew.name,
            "success"   : True,
            "losses"    : {"phone_credits": loss_credits,
                           "floppy_disks" : loss_disks},
            "rep_change": rep,
            "message"   : msg,
        }


# ---------------------------------------------------------------------------
# Daily defense decay
# ---------------------------------------------------------------------------

def apply_npc_daily_trickle(npc_crews, rng=None):
    """
    Slowly replenish NPC crew resources each day so they remain
    worth raiding throughout the game. Aggressive crews recover faster.
    Called by game.py end_day().
    """
    if rng is None:
        rng = random.Random()

    for crew in npc_crews:
        rate = 5 + (crew.aggression * 3)   # agg=1→8, agg=2→11, agg=3→14
        for key in ["phone_credits", "floppy_disks", "source_code",
                    "artwork", "mod_music", "hardware", "tools"]:
            current = crew.resources.get(key, 0)
            cap     = 300
            if current < cap:
                gain = rng.randint(0, rate)
                crew.resources[key] = min(cap, current + gain)


def apply_defense_decay(player):
    """
    Reduce home board defense slightly each day it goes unfortified.
    Called by game.py at the start of each new day.
    """
    player.defense = max(5, player.defense - DEFENSE_DECAY)


# ---------------------------------------------------------------------------
# Flavour message generators
# ---------------------------------------------------------------------------

_VICTORY_LINES = [
    "Your crew hit {crew} like a freight train. They never saw it coming.",
    "In and out. {crew} didn't know what happened until you were gone.",
    "Clean sweep. {crew} will think twice before crossing your path.",
    "{crew}'s board is looking a lot emptier than it was an hour ago.",
    "Textbook execution. {crew} got played hard.",
]

_DEFEAT_LINES = [
    "{crew} was ready for you. Every trick in the book.",
    "They had logging enabled. You walked right into it.",
    "Bad timing. {crew} was online and waiting.",
    "Your crew got humiliated. {crew} is going to brag about this.",
    "Abort, abort. {crew} hit back twice as hard.",
]


_RAID_EVENTS = {
    "A": [
        [
            "Your crew floods the phone lines. No mercy, no subtlety.",
            "Calling everyone in. Brute force is the plan.",
            "You blow through the login screen like it isn't there.",
        ],
        [
            "Their sysop gets an alert — too late to stop you.",
            "Two couriers bounce off the firewall. The rest push through.",
            "You hit three boards at once. Chaos everywhere.",
            "Their ICE kicks back hard — you lose two tools but keep going.",
            "Alarm bells. You silence them and keep moving.",
        ],
        [
            "You're inside their directory. Grab everything.",
            "It's a war of attrition now. Who blinks first?",
            "Your whole crew is in. Time to take what's ours.",
        ],
    ],
    "S": [
        [
            "Slow dialing. You mask your board ID.",
            "Quiet. Low-traffic hour. Fewer eyes on the boards.",
            "You forge a handle from their own memberlist.",
        ],
        [
            "You spot a back door from a trade session last week.",
            "Their logger misses you — you're mimicking legit traffic.",
            "An insider tip: they changed the password. You already have it.",
            "Their sysop posted the new access codes in a msg. Careless.",
        ],
        [
            "You're in. Nobody knows yet. Work fast.",
            "Files transfer in silence. No alarm bells.",
            "Clean in, clean out. Just the way you like it.",
        ],
    ],
    "H": [
        [
            "One fast hit. No lingering.",
            "You've already got the exit route mapped.",
            "In and out in 90 seconds — that's the plan.",
        ],
        [
            "You grab the first directory listing you can reach.",
            "Their sysop's away message is up. Perfect timing.",
            "You yank the archive and cut the line before they respond.",
            "You're in the file area. Take the top shelf and go.",
        ],
        [
            "The signal cuts. You're already gone.",
            "Drop the line before they trace it.",
            "Three hops, two hangups. You're clean.",
        ],
    ],
}


def generate_raid_events(tactic_key, rng):
    """Return 3 narrative event strings for a raid in progress."""
    pools = _RAID_EVENTS.get(tactic_key.upper(), _RAID_EVENTS["S"])
    return [rng.choice(phase) for phase in pools]


def _victory_message(crew_name, loot, rng):
    line = rng.choice(_VICTORY_LINES).format(crew=crew_name)
    if loot:
        items = [f"{v} {k.replace('_', ' ')}" for k, v in loot.items() if v > 0]
        if items:
            line += f" Looted: {', '.join(items[:3])}."
    return line


def _defeat_message(crew_name, losses, rng):
    line = rng.choice(_DEFEAT_LINES).format(crew=crew_name)
    if losses:
        items = [f"{v} {k.replace('_', ' ')}" for k, v in losses.items() if v > 0]
        if items:
            line += f" Lost: {', '.join(items)}."
    return line


# ---------------------------------------------------------------------------
# Combat summary renderer — called from ansi.py / game.py
# ---------------------------------------------------------------------------

def render_result(result, ansi_module):
    """
    Print a formatted combat result to the terminal.
    ansi_module — the imported ansi module (passed to avoid circular imports)
    """
    a = ansi_module
    if result.victory:
        a.writeln(f"\n  {a.G}*** RAID SUCCESSFUL ***{a.RST}")
        a.writeln(f"  {a.DG}{result.message}{a.RST}")
        if result.loot:
            a.writeln(f"\n  {a.Y}LOOT:{a.RST}")
            for key, amount in result.loot.items():
                name = key.replace("_", " ").title()
                a.writeln(f"    {a.W}+{amount:<6}{a.RST}  {a.DG}{name}{a.RST}")
        a.writeln(f"\n  {a.C}Reputation: +{result.rep_change}{a.RST}")
        if result.counter_risk:
            a.writeln(f"  {a.R}Warning: {_tactic_label(result.tactic)} left traces. "
                      f"Counter-raid possible.{a.RST}")
    else:
        a.writeln(f"\n  {a.R}*** RAID FAILED ***{a.RST}")
        a.writeln(f"  {a.DG}{result.message}{a.RST}")
        if result.losses:
            a.writeln(f"\n  {a.R}LOSSES:{a.RST}")
            for key, amount in result.losses.items():
                name = key.replace("_", " ").title()
                a.writeln(f"    {a.R}-{amount:<6}{a.RST}  {a.DG}{name}{a.RST}")
        a.writeln(f"\n  {a.R}Reputation: {result.rep_change}{a.RST}")

    a.writeln(f"\n  {a.DG}Power: yours {result.player_power} vs "
              f"theirs {result.enemy_power}{a.RST}")


def _tactic_label(key):
    return TACTICS.get(key, {}).get("label", key)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import types

    print("=== combat.py self-test ===\n")

    rng = random.Random(42)

    # Mock player
    p = types.SimpleNamespace(
        handle="AXON", tools=40, defense=50, hardware=20,
        phone_credits=450, floppy_disks=300, source_code=200,
        artwork=150, mod_music=100, reputation=200,
        raids_won=0, raids_lost=0,
        adjust_resource=lambda k, v: None,
    )

    # Proper adjust for test
    resources = {
        "phone_credits": 450, "floppy_disks": 300, "source_code": 200,
        "artwork": 150, "mod_music": 100, "reputation": 200,
        "tools": 40, "hardware": 20, "defense": 50,
    }
    def adj(k, v):
        resources[k] = max(0, resources.get(k, 0) + v)
    p.adjust_resource = adj
    def get_res(k):
        return resources.get(k, 0)
    p.get_resource = get_res

    from world import NpcCrew
    enemy = NpcCrew("iCE", "art", 2, 780)

    print("Testing all three tactics:\n")
    for tactic in ["A", "S", "H"]:
        r = resolve_raid(p, enemy, tactic, rng)
        print(f"  Tactic [{tactic}] {TACTICS[tactic]['label']}")
        print(f"    Victory : {r.victory}")
        print(f"    Power   : player={r.player_power}  enemy={r.enemy_power}")
        print(f"    Loot    : {r.loot}")
        print(f"    Losses  : {r.losses}")
        print(f"    Rep     : {r.rep_change}")
        print(f"    Counter : {r.counter_risk}")
        print(f"    Message : {r.message}")
        print()

    # Defence test
    print("Testing defence resolution:\n")
    from world import NpcCrew
    attacker = NpcCrew("Razor 1911", "warez", 3, 850)
    def_result = resolve_defence(p, attacker, rng)
    print(f"  Attacker : {def_result['attacker']}")
    print(f"  Success  : {def_result['success']}")
    print(f"  Losses   : {def_result['losses']}")
    print(f"  Message  : {def_result['message']}")
    print()

    # Decay test
    p.defense = 50
    apply_defense_decay(p)
    print(f"Defense after decay: {p.defense} (was 50, should be {50 - DEFENSE_DECAY})")
