"""
test_core.py — Unit tests for Demoscene core modules
Run with: python test_core.py
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(__file__))

import combat
import world
import courier
import player as playermod


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def check(self, name, actual, expected):
        if actual == expected:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            msg = f"  [FAIL] {name}: expected {expected}, got {actual}"
            self.errors.append(msg)
            print(msg)

    def check_float(self, name, actual, expected, tolerance=0.01):
        if abs(actual - expected) < tolerance:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            msg = f"  [FAIL] {name}: expected ~{expected}, got {actual}"
            self.errors.append(msg)
            print(msg)

    def check_true(self, name, actual):
        if actual:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            msg = f"  [FAIL] {name}: expected truthy, got {actual}"
            self.errors.append(msg)
            print(msg)


def test_combat_basic(tr):
    print("\n## Combat: Basic resolve_raid")

    rng = random.Random(42)

    p = playermod.Player()
    p.tools = 50
    p.defense = 20
    p.hardware = 10

    w = world.World()
    w.generate("TESTPLAYER", "Test BBS", None)

    nc = w.npc_crews[0]

    result = combat.resolve_raid(p, nc, "S", rng)

    tr.check_true("Victory when player_power > enemy_power", result.victory)
    tr.check_true("Rep change is positive on win", result.rep_change > 0)
    tr.check("Loot includes phone_credits", "phone_credits" in result.loot, True)


def test_combat_tactics(tr):
    print("\n## Combat: Tactic multipliers")

    rng = random.Random(123)

    p = playermod.Player()
    p.tools = 30
    p.defense = 10
    p.hardware = 5

    w = world.World()
    w.generate("TACTIC_TEST", "Test BBS", None)

    nc = w.npc_crews[0]

    for tactic in ["A", "S", "H"]:
        result = combat.resolve_raid(p, nc, tactic, rng)
        tr.check_true(f"Tactic {tactic} produces result", result.tactic == tactic.upper())


def test_combat_defense(tr):
    print("\n## Combat: Defense decay")

    p = playermod.Player()
    p.defense = 50

    orig = p.defense
    combat.apply_defense_decay(p)
    tr.check_true("Defense decays", p.defense < orig)


def test_world_generation(tr):
    print("\n## World: Generation")

    rng = random.Random(777)

    w = world.World()
    w.generate("TESTPLAYER", "Test BBS", None)

    tr.check_true("Nodes generated", len(w.nodes) > 0)
    tr.check_true("Home node exists", w.home_node is not None)
    tr.check_true("NPC crews placed", len(w.npc_crews) > 0)


def test_world_node_types(tr):
    print("\n## World: Node types")

    rng = random.Random(999)

    w = world.World()
    w.generate("PLAYER2", "My BBS", None)

    types_seen = set()
    for node in w.nodes:
        if node.node_type != "home":
            types_seen.add(node.node_type)

    tr.check_true("Multiple node types generated", len(types_seen) > 3)


def test_courier_mission(tr):
    print("\n## Courier: Mission generation")

    rng = random.Random(555)

    w = world.World()
    w.generate("COURIERTEST", "Test BBS", None)

    p = playermod.Player()
    p.handle = "couriertest"
    p.day = 1
    p.current_node = p.bbs_name

    w.nodes[1].discovered = True
    w.nodes[2].discovered = True

    mission = courier.get_daily_mission(p, w, rng)

    tr.check_true("Mission generated", mission is not None)
    tr.check_true("Mission has label", bool(mission.label))
    tr.check_true("Mission has origin", bool(mission.origin))
    tr.check_true("Mission has dest", bool(mission.dest))


def test_courier_delivery(tr):
    print("\n## Courier: Mission delivery")

    w = world.World()
    w.generate("DELIVERYTEST", "Test BBS", None)
    w.nodes[1].discovered = True
    w.nodes[2].discovered = True

    p = playermod.Player()
    p.handle = "deliverytest"
    p.day = 1
    p.current_node = p.bbs_name

    p.floppy_disks = 200

    mission = courier.get_daily_mission(p, w, random.Random(666))
    if not mission:
        print("  [SKIP] No mission available")
        return

    courier.accept_mission(p, mission)

    p.current_node = mission.dest

    result = courier.deliver_mission(p, mission)
    tr.check_true("Mission delivered", result)


def test_player_resources(tr):
    print("\n## Player: Resource management")

    p = playermod.Player()

    p.set_resource("floppy_disks", 100)
    tr.check("Floppy disks set", p.floppy_disks, 100)

    p.adjust_resource("floppy_disks", 50)
    tr.check("Floppy disks adjusted", p.floppy_disks, 150)

    p.set_resource("floppy_disks", 500)
    tr.check("Floppy disks capped at max", p.floppy_disks <= p._caps.get("floppy_disks", 999999), True)


def test_player_score(tr):
    print("\n## Player: Score calculation")

    p = playermod.Player()
    p.demos_produced = 10
    p.raids_won = 5
    p.reputation = 100

    score = p.calculate_score()

    tr.check_true("Score is positive", score > 0)
    tr.check_true("Score includes reputation", score >= p.reputation)


def main():
    print("=" * 50)
    print("Demoscene Core Unit Tests")
    print("=" * 50)

    tr = TestResults()

    test_combat_basic(tr)
    test_combat_tactics(tr)
    test_combat_defense(tr)
    test_world_generation(tr)
    test_world_node_types(tr)
    test_courier_mission(tr)
    test_courier_delivery(tr)
    test_player_resources(tr)
    test_player_score(tr)

    print("\n" + "=" * 50)
    print(f"Results: {tr.passed} passed, {tr.failed} failed")
    print("=" * 50)

    if tr.failed:
        print("\nFailed tests:")
        for e in tr.errors:
            print(e)
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()