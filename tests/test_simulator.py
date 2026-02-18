import random

import simulator


def test_battle_runs_and_returns_winner():
    result, _, _ = simulator.run_battle(seed=42, max_turns=20)
    assert result.winner in {"player", "enemy", "draw"}
    assert result.turns >= 1
    assert any("의도(Intent)" in line for line in result.log)


def test_seed_reproducible():
    result1, deck1, hp1 = simulator.run_battle(seed=7, max_turns=12)
    result2, deck2, hp2 = simulator.run_battle(seed=7, max_turns=12)
    assert result1.winner == result2.winner
    assert result1.turns == result2.turns
    assert result1.log == result2.log
    assert deck1 == deck2
    assert hp1 == hp2


def test_draw_from_discard_when_draw_empty():
    rng = random.Random(3)
    state = simulator.PlayerState(draw_pile=[], discard_pile=[simulator.Card("Strike", 1, "attack")])
    log = []
    simulator.draw_cards(state, count=1, rng=rng, log=log)
    assert len(state.hand) == 1
    assert state.hand[0].name == "Strike"
    assert any("셔플" in line for line in log)


def test_burn_damage_uses_cards_remaining_in_hand():
    player = simulator.Combatant(name="P", hp=30, max_hp=30, base_attack=6)
    enemy = simulator.Combatant(name="E", hp=30, max_hp=30, base_attack=6)
    state = simulator.PlayerState(
        draw_pile=[],
        hand=[simulator.Card("Burn", 0, "status_burn"), simulator.Card("Burn", 0, "status_burn")],
    )
    log = []

    simulator.player_turn(player, enemy, state, random.Random(1), log)

    assert player.hp == 26
    assert any("화상(Burn)" in line for line in log)


def test_act_mode_reproducible():
    run1 = simulator.run_act(seed=21, floors=6)
    run2 = simulator.run_act(seed=21, floors=6)
    assert run1.cleared == run2.cleared
    assert run1.floor_reached == run2.floor_reached
    assert run1.gold == run2.gold
    assert run1.deck_size == run2.deck_size
    assert run1.log == run2.log
