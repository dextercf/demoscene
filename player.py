"""
player.py — Player state, save and load
Demoscene: The Exploration of Art
A Cellfish Production

Handles everything to do with the player — their resources, reputation,
crew name, current location, progress through the game, and persistence
between sessions via a flat save file.

Save files are stored in the /saves folder, one file per player handle.
Format is plain INI-style text — human readable and SysOp editable.
"""

import os
import configparser
import time

SAVES_DIR = "saves"

# Default starting resources — overridden by config.ini values at new game
DEFAULTS = {
    "handle"          : "UNKNOWN",
    "crew_name"       : "New Crew",
    "bbs_name"        : "Unknown BBS",
    "day"             : 1,
    "turns_remaining" : 10,
    "phone_credits"   : 200,
    "floppy_disks"    : 100,
    "source_code"     : 80,
    "artwork"         : 50,
    "mod_music"       : 30,
    "reputation"      : 10,
    "beer"            : 0,
    "hardware"        : 0,
    "tools"           : 0,
    "current_node"    : "home",
    "home_node"       : "home",
    "defense"         : 10,
    "demos_produced"  : 0,
    "raids_won"       : 0,
    "raids_lost"      : 0,
    "parties_attended": 0,
    "raves_attended"  : 0,
    "5k_runs"         : 0,
    "beers_drunk"     : 0,
    "total_score"     : 0,
    "game_over"       : False,
    "last_played"     : "",
}

# Resources that can be traded or spent
RESOURCE_KEYS = [
    "phone_credits",
    "floppy_disks",
    "source_code",
    "artwork",
    "mod_music",
    "beer",
    "hardware",
    "tools",
]

# Display names for resources — used in UI screens
RESOURCE_NAMES = {
    "phone_credits" : "Phone Credits",
    "floppy_disks"  : "Floppy Disks",
    "source_code"   : "Source Code",
    "artwork"       : "Artwork",
    "mod_music"     : "MOD Music",
    "beer"          : "Beer",
    "hardware"      : "Hardware",
    "tools"         : "Tools",
}


class Player:
    """Represents a single player and their game state."""

    def __init__(self):
        # Copy all defaults onto self
        for key, val in DEFAULTS.items():
            setattr(self, key, val)
        self._dirty = False  # track unsaved changes
        # Resource caps — loaded from config, defaults are generous
        self._caps = {
            "phone_credits": 9999,
            "floppy_disks" : 2000,
            "source_code"  : 1000,
            "artwork"      : 1000,
            "mod_music"    : 1000,
            "beer"         : 48,
            "hardware"     : 500,
            "tools"        : 500,
        }

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def save_path(self):
        """Path to this player's save file."""
        safe = _safe_filename(self.handle)
        return os.path.join(SAVES_DIR, f"{safe}.sav")

    @property
    def is_new_game(self):
        return self.day == 1 and self.turns_remaining == 10

    # ------------------------------------------------------------------
    # Resource helpers
    # ------------------------------------------------------------------

    def get_resource(self, key):
        return getattr(self, key, 0)

    def set_resource(self, key, value):
        cap = self._caps.get(key, 999999)
        setattr(self, key, max(0, min(int(value), cap)))
        self._dirty = True

    def adjust_resource(self, key, delta):
        """Add or subtract from a resource. Clamps to 0 minimum."""
        current = self.get_resource(key)
        self.set_resource(key, current + delta)

    def can_afford(self, costs):
        """
        Check if the player can afford a dict of resource costs.
        costs = {"source_code": 200, "artwork": 80}
        Returns True if player has enough of every resource listed.
        """
        for key, amount in costs.items():
            if self.get_resource(key) < amount:
                return False
        return True

    def spend(self, costs):
        """
        Deduct a dict of resource costs from the player.
        Returns True if successful, False if they couldn't afford it.
        """
        if not self.can_afford(costs):
            return False
        for key, amount in costs.items():
            self.adjust_resource(key, -amount)
        return True

    def earn(self, rewards):
        """Add a dict of resource rewards to the player."""
        for key, amount in rewards.items():
            self.adjust_resource(key, amount)

    # ------------------------------------------------------------------
    # Turn / day management
    # ------------------------------------------------------------------

    def use_turns(self, count=1):
        """
        Spend action points. Returns True if successful,
        False if the player doesn't have enough turns left.
        """
        if self.turns_remaining < count:
            return False
        self.turns_remaining -= count
        self._dirty = True
        return True

    def end_day(self, action_points_per_day=10):
        """
        Advance to the next day and restore action points.
        Called when the player chooses to sleep / end their day.
        """
        self.day += 1
        self.turns_remaining = action_points_per_day
        self.last_played = _timestamp()
        self._dirty = True

    def is_game_over(self, game_length_days=50):
        """True if the player has reached the end of the game."""
        return self.day > game_length_days or self.game_over

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def calculate_score(self):
        """
        Final score calculation.
        Reputation is the primary driver, with bonuses for activity.
        """
        score = self.reputation * 10
        score += self.demos_produced * 50
        score += self.raids_won * 30
        score -= self.raids_lost * 10
        score += self.parties_attended * 100
        score += self.raves_attended * 25
        score += self.get_resource("5k_runs") * 40
        score = max(0, score)
        self.total_score = score
        self._dirty = True
        return score

    # ------------------------------------------------------------------
    # Save / load
    # ------------------------------------------------------------------

    def save(self):
        """Write player state to their save file."""
        _ensure_saves_dir()
        cfg = configparser.ConfigParser()
        cfg["player"] = {}
        cfg["stats"]  = {}
        cfg["resources"] = {}

        # Core identity
        cfg["player"]["handle"]           = str(self.handle)
        cfg["player"]["crew_name"]        = str(self.crew_name)
        cfg["player"]["bbs_name"]         = str(self.bbs_name)
        cfg["player"]["last_played"]      = str(self.last_played)

        # Game progress
        cfg["stats"]["day"]               = str(self.day)
        cfg["stats"]["turns_remaining"]   = str(self.turns_remaining)
        cfg["stats"]["current_node"]      = str(self.current_node)
        cfg["stats"]["home_node"]         = str(self.home_node)
        cfg["stats"]["defense"]           = str(self.defense)
        cfg["stats"]["reputation"]        = str(self.reputation)
        cfg["stats"]["demos_produced"]    = str(self.demos_produced)
        cfg["stats"]["raids_won"]         = str(self.raids_won)
        cfg["stats"]["raids_lost"]        = str(self.raids_lost)
        cfg["stats"]["parties_attended"]  = str(self.parties_attended)
        cfg["stats"]["raves_attended"]    = str(self.raves_attended)
        cfg["stats"]["5k_runs"]           = str(getattr(self, "5k_runs", 0))
        cfg["stats"]["beers_drunk"]       = str(self.beers_drunk)
        cfg["stats"]["total_score"]       = str(self.total_score)
        cfg["stats"]["game_over"]         = str(self.game_over)

        # Resources
        for key in RESOURCE_KEYS:
            cfg["resources"][key] = str(self.get_resource(key))

        with open(self.save_path, "w", encoding="cp437") as f:
            cfg.write(f)

        self._dirty = False

    def load(self):
        """
        Load player state from their save file.
        Returns True if successful, False if no save file exists.
        """
        if not os.path.isfile(self.save_path):
            return False

        cfg = configparser.ConfigParser()
        cfg.read(self.save_path, encoding="cp437")

        def _get(section, key, default):
            try:
                return cfg[section][key]
            except KeyError:
                return str(default)

        def _int(section, key, default=0):
            try:
                return int(_get(section, key, default))
            except ValueError:
                return default

        def _bool(section, key, default=False):
            val = _get(section, key, str(default)).lower()
            return val in ("true", "1", "yes")

        # Core identity
        self.handle           = _get("player", "handle",      self.handle)
        self.crew_name        = _get("player", "crew_name",   self.crew_name)
        self.bbs_name         = _get("player", "bbs_name",    self.bbs_name)
        self.last_played      = _get("player", "last_played", "")

        # Game progress
        self.day              = _int("stats", "day",              1)
        self.turns_remaining  = _int("stats", "turns_remaining",  10)
        self.current_node     = _get("stats", "current_node",     "home")
        self.home_node        = _get("stats", "home_node",        "home")
        self.defense          = _int("stats", "defense",          10)
        self.reputation       = _int("stats", "reputation",       10)
        self.demos_produced   = _int("stats", "demos_produced",   0)
        self.raids_won        = _int("stats", "raids_won",        0)
        self.raids_lost       = _int("stats", "raids_lost",       0)
        self.parties_attended = _int("stats", "parties_attended", 0)
        self.raves_attended   = _int("stats", "raves_attended",   0)
        setattr(self, "5k_runs", _int("stats", "5k_runs",         0))
        self.beers_drunk      = _int("stats", "beers_drunk",      0)
        self.total_score      = _int("stats", "total_score",      0)
        self.game_over        = _bool("stats", "game_over",       False)

        # Resources
        for key in RESOURCE_KEYS:
            default = DEFAULTS.get(key, 0)
            setattr(self, key, _int("resources", key, default))

        self._dirty = False
        return True

    def apply_config(self, cfg):
        """
        Apply starting values from config.ini to a fresh player.
        Only called when starting a new game — does not affect loaded saves.
        cfg is a configparser.ConfigParser instance already read from disk.
        """
        def _int(key, default):
            try:
                return int(cfg["gameplay"].get(key, default))
            except (KeyError, ValueError):
                return default

        self.phone_credits   = _int("starting_phone_credits", 200)
        self.floppy_disks    = _int("starting_floppy_disks",  100)
        self.source_code     = _int("starting_source_code",   80)
        self.artwork         = _int("starting_artwork",        50)
        self.mod_music       = _int("starting_mod_music",      30)
        self.reputation      = _int("starting_reputation",     10)
        self.beer            = _int("starting_beer",           0)
        self.turns_remaining = _int("action_points_per_day",   10)

        # Load resource caps from config so set_resource enforces them
        self._caps = {
            "phone_credits": _int("max_phone_credits", 9999),
            "floppy_disks" : _int("max_floppy_disks",  2000),
            "source_code"  : _int("max_source_code",   1000),
            "artwork"      : _int("max_artwork",        1000),
            "mod_music"    : _int("max_mod_music",      1000),
            "beer"         : _int("max_beer",           48),
            "hardware"     : _int("max_hardware",       500),
            "tools"        : _int("max_tools",          500),
        }
        self._dirty = True

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def summary(self):
        """Return a dict of display-ready player stats for UI screens."""
        return {
            "Handle"          : self.handle,
            "Crew"            : self.crew_name,
            "Day"             : self.day,
            "Turns"           : self.turns_remaining,
            "Reputation"      : self.reputation,
            "Phone Credits"   : self.phone_credits,
            "Floppy Disks"    : self.floppy_disks,
            "Source Code"     : self.source_code,
            "Artwork"         : self.artwork,
            "MOD Music"       : self.mod_music,
            "Beer"            : self.beer,
            "Hardware"        : self.hardware,
            "Tools"           : self.tools,
            "Current Node"    : self.current_node,
            "Defense"         : self.defense,
            "Demos Produced"  : self.demos_produced,
            "Raids Won"       : self.raids_won,
            "Raids Lost"      : self.raids_lost,
            "Parties Attended": self.parties_attended,
            "Score"           : self.total_score,
        }


# ------------------------------------------------------------------
# Leaderboard — shared across all players on the BBS
# ------------------------------------------------------------------

LEADERBOARD_PATH = os.path.join(SAVES_DIR, "leaderboard.txt")
LEADERBOARD_MAX  = 20


def load_leaderboard():
    """
    Load the Hall of Fame from disk.
    Returns a list of dicts sorted by score descending.
    Each entry: {handle, crew, bbs, score, day, date}
    """
    entries = []
    if not os.path.isfile(LEADERBOARD_PATH):
        return entries
    try:
        with open(LEADERBOARD_PATH, "r", encoding="cp437") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    entries.append({
                        "handle": parts[0],
                        "crew"  : parts[1],
                        "bbs"   : parts[2],
                        "score" : _safe_int(parts[3]),
                        "day"   : _safe_int(parts[4]) if len(parts) > 4 else 0,
                        "date"  : parts[5] if len(parts) > 5 else "",
                    })
    except OSError:
        pass
    entries.sort(key=lambda e: e["score"], reverse=True)
    return entries


def save_leaderboard(entries):
    """Write the leaderboard to disk."""
    _ensure_saves_dir()
    entries = sorted(entries, key=lambda e: e["score"], reverse=True)
    entries = entries[:LEADERBOARD_MAX]
    try:
        with open(LEADERBOARD_PATH, "w", encoding="cp437") as f:
            f.write("; Demoscene: The Exploration of Art — Hall of Fame\n")
            f.write("; handle|crew|bbs|score|day|date\n")
            for e in entries:
                f.write(
                    f"{e['handle']}|{e['crew']}|{e['bbs']}|"
                    f"{e['score']}|{e['day']}|{e['date']}\n"
                )
    except OSError:
        pass


def submit_score(player):
    """
    Add a player's final score to the leaderboard.
    If they already have an entry, only update it if the new score is higher.
    """
    score = player.calculate_score()
    entries = load_leaderboard()

    # Check for existing entry by this handle
    existing = next(
        (e for e in entries if e["handle"].upper() == player.handle.upper()),
        None
    )

    if existing:
        if score <= existing["score"]:
            return  # no improvement — don't update
        entries.remove(existing)

    entries.append({
        "handle": player.handle,
        "crew"  : player.crew_name,
        "bbs"   : player.bbs_name,
        "score" : score,
        "day"   : player.day,
        "date"  : _timestamp(),
    })
    save_leaderboard(entries)


def get_player_rank(handle, entries=None):
    """Return the 1-based leaderboard rank for a handle, or None."""
    if entries is None:
        entries = load_leaderboard()
    for i, e in enumerate(entries):
        if e["handle"].upper() == handle.upper():
            return i + 1
    return None


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _ensure_saves_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)


def _safe_filename(handle):
    """Sanitise a handle for use as a filename."""
    safe = "".join(c for c in handle if c.isalnum() or c in "-_")
    return safe.upper()[:20] or "UNKNOWN"


def _safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _timestamp():
    return time.strftime("%Y-%m-%d")


# ------------------------------------------------------------------
# Self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import configparser

    print("=== player.py self-test ===\n")

    # Create a fresh player
    p = Player()
    p.handle    = "AXON"
    p.crew_name = "The Fish Tank"
    p.bbs_name  = "The Aquarium BBS"

    # Simulate some gameplay
    p.adjust_resource("reputation",    +200)
    p.adjust_resource("phone_credits", -50)
    p.adjust_resource("source_code",   +100)
    p.demos_produced = 3
    p.raids_won      = 2
    p.use_turns(3)
    p.end_day()

    print("Player summary:")
    for k, v in p.summary().items():
        print(f"  {k:<20} {v}")

    # Save
    p.save()
    print(f"\nSaved to: {p.save_path}")

    # Load into a new object
    p2 = Player()
    p2.handle = "AXON"
    ok = p2.load()
    print(f"Load successful: {ok}")
    print(f"Day after load : {p2.day}")
    print(f"Reputation     : {p2.reputation}")

    # Score and leaderboard
    score = p.calculate_score()
    print(f"\nFinal score: {score}")
    submit_score(p)
    board = load_leaderboard()
    print(f"Leaderboard entries: {len(board)}")
    for e in board:
        print(f"  {e['handle']:<15} {e['crew']:<20} {e['score']}")

    rank = get_player_rank("AXON")
    print(f"\nAXON's rank: #{rank}")
