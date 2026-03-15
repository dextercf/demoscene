"""
world.py — Network map, BBS nodes, NPC crews, demoparties
Demoscene: The Exploration of Art
A Cellfish Production

Generates and manages the game world — the network of BBS nodes the player
explores, the NPC rival crews that inhabit them, and the demoparty schedule.

The world is procedurally generated from a seed at the start of each new game
so every playthrough has a different map. The seed is saved with the world
so the same map is restored when the player continues a saved game.

World state is saved to saves/<HANDLE>.world as plain INI-style text.
"""

import os
import random
import configparser

SAVES_DIR = "saves"

# ---------------------------------------------------------------------------
# Node type definitions
# Each type has a speciality resource, a flavour description, and a rarity
# weight (higher = more common).
# ---------------------------------------------------------------------------

NODE_TYPES = {
    "home"     : {"label": "Home Board",     "speciality": None,            "rarity": 0,  "desc": "Your home BBS."},
    "music"    : {"label": "Music Board",    "speciality": "mod_music",     "rarity": 15, "desc": "A board dedicated to tracked music and MODs."},
    "art"      : {"label": "Art Board",      "speciality": "artwork",       "rarity": 12, "desc": "ANSI and pixel artists gather here."},
    "coding"   : {"label": "Coding Board",   "speciality": "source_code",   "rarity": 12, "desc": "Coders swap source and discuss algorithms."},
    "warez"    : {"label": "Warez Board",    "speciality": "tools",         "rarity": 14, "desc": "Shady. Anything goes. Watch your back."},
    "hardware" : {"label": "Hardware Bazaar","speciality": "hardware",      "rarity": 10, "desc": "Modems, gear, overclocked machines."},
    "trading"  : {"label": "Trade Post",     "speciality": "floppy_disks",  "rarity": 13, "desc": "Disk traders and couriers meet here."},
    "social"   : {"label": "Social Board",   "speciality": "reputation",    "rarity": 10, "desc": "The place to be seen. Reputation flows freely."},
    "elite"    : {"label": "Elite Board",    "speciality": None,            "rarity": 5,  "desc": "Invite only. The best crews in the scene."},
    "legendary": {"label": "Legendary Board","speciality": None,            "rarity": 2,  "desc": "Rumoured to exist. Few have found it."},
}

# ---------------------------------------------------------------------------
# BBS node name pools — drawn from when generating the world
# ---------------------------------------------------------------------------

# Common nodes — appear early, low hop count
COMMON_NODE_NAMES = [
    "The Humble Origins", "Null Pointer", "Stack Overflow",
    "The Swap Shop", "Carrier Signal", "The Render Farm",
    "Baud Brothel", "The Phreaks Nest", "Iron Gate",
    "The Blitter", "SID Station", "The Copper Mine",
    "Raster Interrupt", "The Copper List", "Neon Abyss",
    "The Byte Bucket", "Digital Darkness", "The Dungeon",
    "Dragon Citadel", "The Attack Zone", "POPNet",
]

# Mid-tier nodes — appear at medium distances
MID_NODE_NAMES = [
    "The Pixel Forge", "The Tracker Den", "The Art Gallery",
    "The Demo Hub", "The Hardware Bazaar", "The Underground",
    "The Mailbox", "Cloud Nine Elite", "Road to Nowhere",
    "State of Devolution", "Violent Playground", "Death Valley",
    "Suburban Decay", "The Warez Pit", "Speed of Light",
    "Metal ANet", "Apocalypse Now", "The Void",
]

# Rare / legendary nodes — appear only deep in the network
RARE_NODE_NAMES = [
    "Gates of Asgard", "Point of No Return", "Mirage",
    "The Elite Board", "The Legend", "Helter Skelter",
    "XTC Systems", "PCP Systems", "Southern Comfort",
    "Mortal Wish", "The House of God",
]

# ---------------------------------------------------------------------------
# NPC crew definitions
# Real and fictional demoscene / warez crews
# ---------------------------------------------------------------------------

NPC_CREWS = [
    {"name": "Future Crew",  "style": "demo",    "aggression": 1, "rep": 900},
    {"name": "ACiD",         "style": "art",     "aggression": 2, "rep": 820},
    {"name": "iCE",          "style": "art",     "aggression": 2, "rep": 780},
    {"name": "Razor 1911",   "style": "warez",   "aggression": 3, "rep": 850},
    {"name": "Skid Row",     "style": "warez",   "aggression": 3, "rep": 800},
    {"name": "Fairlight",    "style": "warez",   "aggression": 2, "rep": 760},
    {"name": "Phenomena",    "style": "demo",    "aggression": 1, "rep": 720},
    {"name": "The Silents",  "style": "demo",    "aggression": 1, "rep": 700},
    {"name": "Byterapers",   "style": "demo",    "aggression": 2, "rep": 650},
    {"name": "THG",          "style": "warez",   "aggression": 3, "rep": 680},
    {"name": "Paranoimia",   "style": "demo",    "aggression": 1, "rep": 600},
    {"name": "Triton",       "style": "coding",  "aggression": 1, "rep": 580},
]

# ---------------------------------------------------------------------------
# Demoparty definitions
# ---------------------------------------------------------------------------

PARTIES = [
    {
        "name"       : "Revision",
        "location"   : "Saarbrücken, Germany",
        "flavour"    : "The premier European demoparty. Serious competition.",
        "size"       : "large",
        "compos"     : ["demo", "64k", "4k", "music", "ansi", "wild"],
        "special"    : ["5k_run"],
        "rave_chance": 80,
    },
    {
        "name"       : "The Party",
        "location"   : "Denmark",
        "flavour"    : "The classic Danish gathering. Old school vibes.",
        "size"       : "large",
        "compos"     : ["demo", "64k", "4k", "music", "ansi"],
        "special"    : [],
        "rave_chance": 70,
    },
    {
        "name"       : "Assembly",
        "location"   : "Helsinki, Finland",
        "flavour"    : "Finnish mega-party. Music and graphics dominate.",
        "size"       : "large",
        "compos"     : ["demo", "music", "ansi", "wild"],
        "special"    : [],
        "rave_chance": 60,
    },
    {
        "name"       : "Gubbdata",
        "location"   : "Sweden",
        "flavour"    : "Retro heaven. C64 and Amiga rule here.",
        "size"       : "medium",
        "compos"     : ["demo", "4k", "music", "ansi"],
        "special"    : ["retro_bonus"],
        "rave_chance": 75,
    },
    {
        "name"       : "Evoke",
        "location"   : "Cologne, Germany",
        "flavour"    : "Underground and experimental. Expect the unexpected.",
        "size"       : "medium",
        "compos"     : ["demo", "wild", "music"],
        "special"    : [],
        "rave_chance": 85,
    },
    {
        "name"       : "Kindergarten",
        "location"   : "Unknown",
        "flavour"    : "Small friendly party. Good place to start.",
        "size"       : "small",
        "compos"     : ["4k", "music", "ansi"],
        "special"    : [],
        "rave_chance": 40,
    },
    {
        "name"       : "LAN in a Van",
        "location"   : "Unknown",
        "flavour"    : "Nobody knows where it is. Strange things happen here.",
        "size"       : "tiny",
        "compos"     : ["wild"],
        "special"    : ["chaos"],
        "rave_chance": 100,
    },
]

# Possible rave DJs
RAVE_DJS = [
    {"handle": "h0ffman",  "bonus": "mod_music",   "rep_bonus": 40,
     "flavour": "A set from h0ffman himself. The tracked music gods smile on you."},
    {"handle": "Dubmood",  "bonus": "source_code",  "rep_bonus": 35,
     "flavour": "Dubmood drops an 80s electro set. Cracktros write themselves."},
    {"handle": "Random",   "bonus": None,           "rep_bonus": 20,
     "flavour": "Nobody knows who this DJ is. Absolute chaos on the dancefloor."},
]

# Compo definitions — resource requirements and reputation rewards
COMPO_DEFS = {
    "demo"  : {"label": "Demo Compo",       "costs": {"source_code": 400, "artwork": 200, "mod_music": 150}, "rep_1st": 600, "rep_2nd": 350, "rep_3rd": 150},
    "64k"   : {"label": "64K Intro",        "costs": {"source_code": 200, "artwork": 80},                    "rep_1st": 280, "rep_2nd": 160, "rep_3rd": 80},
    "4k"    : {"label": "4K Intro",         "costs": {"source_code": 120, "artwork": 40},                    "rep_1st": 120, "rep_2nd": 70,  "rep_3rd": 30},
    "music" : {"label": "Tracked Music",    "costs": {"mod_music": 300},                                     "rep_1st": 200, "rep_2nd": 110, "rep_3rd": 50},
    "ansi"  : {"label": "ANSI/ASCII Art",   "costs": {"artwork": 250},                                       "rep_1st": 180, "rep_2nd": 100, "rep_3rd": 45},
    "wild"  : {"label": "Wild Compo",       "costs": {"floppy_disks": 100},                                  "rep_1st": 150, "rep_2nd": 80,  "rep_3rd": 35},
}


# ---------------------------------------------------------------------------
# Node class
# ---------------------------------------------------------------------------

class Node:
    def __init__(self, name, node_type, hops, index):
        self.name      = name
        self.node_type = node_type   # key into NODE_TYPES
        self.hops      = hops        # distance from home in hops
        self.index     = index       # unique index in world.nodes list
        self.discovered= hops == 0   # home is always discovered
        self.crew      = None        # name of NPC crew present, or None
        self.prices    = {}          # buy prices for resources at this node
        self._generate_prices()

    @property
    def label(self):
        return NODE_TYPES[self.node_type]["label"]

    @property
    def speciality(self):
        return NODE_TYPES[self.node_type]["speciality"]

    @property
    def description(self):
        return NODE_TYPES[self.node_type]["desc"]

    @property
    def is_legendary(self):
        return self.node_type == "legendary"

    def _generate_prices(self):
        """Generate buy/sell prices for all tradeable resources at this node."""
        base = {
            "phone_credits": 1,
            "floppy_disks" : 80,
            "source_code"  : 200,
            "artwork"      : 180,
            "mod_music"    : 160,
            "beer"         : 50,
            "hardware"     : 380,
            "tools"        : 300,
        }
        spec = self.speciality
        for key, price in base.items():
            # Speciality resource is cheaper to buy here
            modifier = 0.7 if key == spec else 1.0
            # Small random variance per node
            variance = random.uniform(0.85, 1.15)
            self.prices[key] = max(1, int(price * modifier * variance))

    def sell_price(self, resource):
        """Sell price is always 60% of buy price."""
        return max(1, int(self.prices.get(resource, 100) * 0.6))

    def to_dict(self):
        return {
            "name"      : self.name,
            "node_type" : self.node_type,
            "hops"      : self.hops,
            "index"     : self.index,
            "discovered": self.discovered,
            "crew"      : self.crew or "",
            "prices"    : "|".join(f"{k}:{v}" for k, v in self.prices.items()),
        }

    @classmethod
    def from_dict(cls, d):
        node = cls(d["name"], d["node_type"], int(d["hops"]), int(d["index"]))
        node.discovered = d["discovered"].lower() in ("true", "1", "yes") \
            if isinstance(d["discovered"], str) else bool(d["discovered"])
        node.crew = d["crew"] or None
        if d["prices"]:
            for pair in d["prices"].split("|"):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    try:
                        node.prices[k] = int(v)
                    except ValueError:
                        pass
        return node


# ---------------------------------------------------------------------------
# NPC Crew class
# ---------------------------------------------------------------------------

class NpcCrew:
    def __init__(self, name, style, aggression, rep):
        self.name        = name
        self.style       = style       # demo / art / warez / coding
        self.aggression  = aggression  # 1-3
        self.rep         = rep         # starting reputation
        self.home_node   = None        # index of their home node
        self.resources   = {
            "phone_credits": random.randint(100, 400),
            "floppy_disks" : random.randint(50,  300),
            "source_code"  : random.randint(50,  250),
            "artwork"      : random.randint(30,  200),
            "mod_music"    : random.randint(20,  150),
            "tools"        : random.randint(10,  100),
            "hardware"     : random.randint(10,  80),
        }
        self.strength    = random.randint(30, 80)
        self.defense     = random.randint(20, 70)

    def to_dict(self):
        res = "|".join(f"{k}:{v}" for k, v in self.resources.items())
        return {
            "name"      : self.name,
            "style"     : self.style,
            "aggression": self.aggression,
            "rep"       : self.rep,
            "home_node" : self.home_node if self.home_node is not None else "",
            "strength"  : self.strength,
            "defense"   : self.defense,
            "resources" : res,
        }

    @classmethod
    def from_dict(cls, d):
        crew = cls(d["name"], d["style"], int(d["aggression"]), int(d["rep"]))
        crew.home_node = int(d["home_node"]) if d.get("home_node") else None
        crew.strength  = int(d.get("strength", 50))
        crew.defense   = int(d.get("defense",  40))
        if d.get("resources"):
            for pair in d["resources"].split("|"):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    try:
                        crew.resources[k] = int(v)
                    except ValueError:
                        pass
        return crew


# ---------------------------------------------------------------------------
# Party schedule entry
# ---------------------------------------------------------------------------

class PartyEvent:
    def __init__(self, party_def, day, attended=False, results=None):
        self.name       = party_def["name"]
        self.location   = party_def["location"]
        self.flavour    = party_def["flavour"]
        self.size       = party_def["size"]
        self.compos     = party_def["compos"]
        self.special    = party_def["special"]
        self.rave_chance= party_def["rave_chance"]
        self.day        = day          # day the party starts
        self.attended   = attended
        self.results    = results or {}

    def to_dict(self):
        import json
        return {
            "name"    : self.name,
            "day"     : self.day,
            "attended": self.attended,
            "results" : str(self.results),
        }

    @classmethod
    def from_dict(cls, d, party_defs):
        defn = next((p for p in party_defs if p["name"] == d["name"]),
                    party_defs[0])
        pe = cls(defn, int(d["day"]), d["attended"] in ("True", "true", "1"))
        return pe


# ---------------------------------------------------------------------------
# World class
# ---------------------------------------------------------------------------

class World:
    """
    The full game world — nodes, NPC crews, party schedule.
    Generated once per new game from a random seed, then saved and restored.
    """

    def __init__(self):
        self.seed        = 0
        self.nodes       = []     # list of Node
        self.npc_crews   = []     # list of NpcCrew
        self.parties     = []     # list of PartyEvent
        self.home_node   = None   # reference to the player's home Node
        self._rng        = random.Random()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(self, handle, bbs_name, cfg=None):
        """
        Generate a fresh world for a new game.
        handle   — player handle, used to seed the RNG for reproducibility
        bbs_name — player's home BBS name
        cfg      — configparser instance from config.ini (optional)
        """
        # Seed from handle + current time for uniqueness
        self.seed = hash(handle + str(random.randint(0, 999999))) & 0xFFFFFFFF
        self._rng.seed(self.seed)
        rng = self._rng

        node_count        = 20
        npc_count         = 6
        party_frequency   = 12
        game_length       = 50

        if cfg:
            try:
                node_count      = int(cfg["gameplay"].get("node_count", 20))
                npc_count       = int(cfg["gameplay"].get("npc_crew_count", 6))
                party_frequency = int(cfg["parties"].get("party_frequency_days", 12))
                game_length     = int(cfg["gameplay"].get("game_length_days", 50))
            except (KeyError, ValueError):
                pass

        # -- Nodes --------------------------------------------------------
        self.nodes = []

        # Home node always index 0, hops 0
        home = Node(bbs_name, "home", 0, 0)
        home.discovered = True
        self.nodes.append(home)
        self.home_node = home

        # Build pools for each hop distance
        common_pool    = list(COMMON_NODE_NAMES)
        mid_pool       = list(MID_NODE_NAMES)
        rare_pool      = list(RARE_NODE_NAMES)
        rng.shuffle(common_pool)
        rng.shuffle(mid_pool)
        rng.shuffle(rare_pool)

        # Build weighted type pool (excluding home and legendary for now)
        type_pool = []
        for t, info in NODE_TYPES.items():
            if t in ("home", "legendary"):
                continue
            type_pool.extend([t] * info["rarity"])

        for i in range(1, node_count):
            # Determine hop distance — increases with index
            if i <= node_count * 0.3:
                hops = rng.randint(1, 3)
                name = common_pool.pop() if common_pool else f"Node {i}"
                ntype = rng.choice([t for t in type_pool
                                    if t not in ("elite", "legendary")])
            elif i <= node_count * 0.7:
                hops = rng.randint(3, 6)
                name = mid_pool.pop() if mid_pool else f"Node {i}"
                ntype = rng.choice(type_pool)
            else:
                hops = rng.randint(6, 10)
                # Last few nodes — chance of legendary
                if rare_pool and rng.random() < 0.4:
                    name  = rare_pool.pop()
                    ntype = rng.choice(["elite", "legendary"])
                else:
                    name  = mid_pool.pop() if mid_pool else rare_pool.pop() \
                        if rare_pool else f"Deep Node {i}"
                    ntype = rng.choice(type_pool)

            node = Node(name, ntype, hops, i)
            self.nodes.append(node)

        # -- NPC Crews ----------------------------------------------------
        self.npc_crews = []
        crew_pool = list(NPC_CREWS)
        rng.shuffle(crew_pool)
        selected = crew_pool[:min(npc_count, len(crew_pool))]

        non_home = [n for n in self.nodes if n.node_type != "home"]
        rng.shuffle(non_home)

        for i, cdef in enumerate(selected):
            crew = NpcCrew(cdef["name"], cdef["style"],
                           cdef["aggression"], cdef["rep"])
            # Assign a home node
            if i < len(non_home):
                crew.home_node = non_home[i].index
                non_home[i].crew = crew.name
            self.npc_crews.append(crew)

        # -- Party schedule -----------------------------------------------
        self.parties = []
        party_pool = list(PARTIES)
        rng.shuffle(party_pool)
        day = party_frequency
        pi  = 0
        while day <= game_length:
            pdef = party_pool[pi % len(party_pool)]
            self.parties.append(PartyEvent(pdef, day))
            day += rng.randint(
                max(5, party_frequency - 3),
                party_frequency + 4
            )
            pi += 1

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_node(self, index):
        for n in self.nodes:
            if n.index == index:
                return n
        return None

    def get_node_by_name(self, name):
        for n in self.nodes:
            if n.name.lower() == name.lower():
                return n
        return None

    def discovered_nodes(self):
        return [n for n in self.nodes if n.discovered]

    def undiscovered_count(self):
        return sum(1 for n in self.nodes if not n.discovered)

    def nodes_at_hops(self, max_hops):
        return [n for n in self.nodes if n.hops <= max_hops]

    def get_crew(self, name):
        for c in self.npc_crews:
            if c.name.lower() == name.lower():
                return c
        return None

    def upcoming_parties(self, current_day, lookahead=15):
        return [p for p in self.parties
                if current_day <= p.day <= current_day + lookahead]

    def party_on_day(self, day):
        for p in self.parties:
            if p.day == day:
                return p
        return None

    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------

    def explore(self, current_node_index, rng=None):
        """
        Discover a new node adjacent to the player's current position.
        Returns the newly discovered Node, or None if nothing new nearby.
        """
        if rng is None:
            rng = random.Random()

        current = self.get_node(current_node_index)
        if current is None:
            return None

        # Find undiscovered nodes within current_hops + 2
        candidates = [
            n for n in self.nodes
            if not n.discovered
            and abs(n.hops - current.hops) <= 2
        ]
        if not candidates:
            # Try anywhere undiscovered
            candidates = [n for n in self.nodes if not n.discovered]
        if not candidates:
            return None

        # Weight towards closer nodes
        weights = [max(1, 10 - n.hops) for n in candidates]
        found = rng.choices(candidates, weights=weights, k=1)[0]
        found.discovered = True
        return found

    # ------------------------------------------------------------------
    # Save / load
    # ------------------------------------------------------------------

    def save(self, handle):
        _ensure_saves_dir()
        path = _world_path(handle)
        cfg  = configparser.ConfigParser()

        cfg["world"] = {"seed": str(self.seed)}

        for i, node in enumerate(self.nodes):
            section = f"node_{i}"
            cfg[section] = node.to_dict()
            # configparser requires string values
            for k, v in cfg[section].items():
                cfg[section][k] = str(v)

        for i, crew in enumerate(self.npc_crews):
            section = f"crew_{i}"
            cfg[section] = crew.to_dict()
            for k, v in cfg[section].items():
                cfg[section][k] = str(v)

        for i, party in enumerate(self.parties):
            section = f"party_{i}"
            cfg[section] = party.to_dict()
            for k, v in cfg[section].items():
                cfg[section][k] = str(v)

        with open(path, "w", encoding="cp437") as f:
            cfg.write(f)

    def load(self, handle):
        path = _world_path(handle)
        if not os.path.isfile(path):
            return False

        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="cp437")

        try:
            self.seed = int(cfg["world"]["seed"])
        except (KeyError, ValueError):
            self.seed = 0

        self.nodes = []
        i = 0
        while True:
            section = f"node_{i}"
            if section not in cfg:
                break
            self.nodes.append(Node.from_dict(dict(cfg[section])))
            i += 1

        if self.nodes:
            self.home_node = self.nodes[0]

        self.npc_crews = []
        i = 0
        while True:
            section = f"crew_{i}"
            if section not in cfg:
                break
            self.npc_crews.append(NpcCrew.from_dict(dict(cfg[section])))
            i += 1

        self.parties = []
        i = 0
        while True:
            section = f"party_{i}"
            if section not in cfg:
                break
            self.parties.append(
                PartyEvent.from_dict(dict(cfg[section]), PARTIES)
            )
            i += 1

        return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_saves_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)


def _world_path(handle):
    safe = "".join(c for c in handle if c.isalnum() or c in "-_")
    return os.path.join(SAVES_DIR, f"{safe.upper()[:20]}.world")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== world.py self-test ===\n")

    w = World()
    w.generate("AXON", "The Fish Tank BBS")

    print(f"Seed        : {w.seed}")
    print(f"Nodes       : {len(w.nodes)}")
    print(f"NPC crews   : {len(w.npc_crews)}")
    print(f"Parties     : {len(w.parties)}")
    print(f"Home node   : {w.home_node.name}\n")

    print("[ First 5 nodes ]")
    for n in w.nodes[:5]:
        crew = f" — {n.crew}" if n.crew else ""
        print(f"  {n.index:>2}. {n.name:<30} {n.label:<18} {n.hops} hops{crew}")

    print("\n[ NPC Crews ]")
    for c in w.npc_crews:
        hn = w.get_node(c.home_node)
        home = hn.name if hn else "?"
        print(f"  {c.name:<15} style={c.style:<8} agg={c.aggression} "
              f"rep={c.rep} home={home}")

    print("\n[ Party Schedule ]")
    for p in w.parties:
        print(f"  Day {p.day:>3} — {p.name} ({p.location})")
        print(f"           Compos: {', '.join(p.compos)}")

    # Test exploration
    print("\n[ Exploration test ]")
    rng = random.Random(42)
    for _ in range(3):
        found = w.explore(0, rng)
        if found:
            print(f"  Discovered: {found.name} ({found.label}, {found.hops} hops)")

    # Save and reload
    w.save("AXON")
    print("\nWorld saved.")

    w2 = World()
    ok = w2.load("AXON")
    print(f"World loaded: {ok}")
    print(f"Nodes after load: {len(w2.nodes)}")
    print(f"Parties after load: {len(w2.parties)}")
