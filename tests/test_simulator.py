import simulator


def test_battle_runs_and_returns_winner():
    result = simulator.run_battle(seed=42, max_turns=20)
    assert result.winner in {"player", "enemy", "draw"}
    assert result.turns >= 1
    assert any("턴" in line for line in result.log)


def test_seed_reproducible():
    result1 = simulator.run_battle(seed=7, max_turns=12)
    result2 = simulator.run_battle(seed=7, max_turns=12)
    assert result1.winner == result2.winner
    assert result1.turns == result2.turns
    assert result1.log == result2.log
