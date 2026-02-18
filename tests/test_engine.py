import unittest

from dcss_ss.engine import (
    ActorState,
    CombatEngine,
    CombatState,
    StatusEffects,
    run_sample_battle,
)


class CombatEngineTests(unittest.TestCase):
    def test_damage_formula_applies_floor_and_block(self):
        damage = CombatEngine.calculate_attack_damage(
            base_damage=7,
            attacker_mod=0.75,
            defender_mod=1.5,
            defender_block=3,
        )
        self.assertEqual(damage, 4)

    def test_resistance_is_applied(self):
        self.assertEqual(CombatEngine.apply_resistance(10, 0.3), 7)

    def test_poison_ticks_and_decrements(self):
        engine = CombatEngine()
        state = CombatState(
            player=ActorState(name="Player", hp=20, max_hp=20, statuses=StatusEffects(poison=3)),
            enemy=ActorState(name="Enemy", hp=10, max_hp=10),
        )
        engine.apply_poison_tick(state.player, state)
        self.assertEqual(state.player.hp, 17)
        self.assertEqual(state.player.statuses.poison, 2)

    def test_run_sample_battle_completes(self):
        state = run_sample_battle(seed=1)
        self.assertGreater(len(state.logs), 0)
        self.assertTrue(any("Battle finished" in line for line in state.logs))


if __name__ == "__main__":
    unittest.main()
