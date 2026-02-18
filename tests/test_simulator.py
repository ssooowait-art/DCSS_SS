import simulator


def test_battle_runs_and_logs_intent():
    cfg = simulator.SPECIES["human"]
    result, deck_after, hp_after = simulator.run_battle(
        seed=42,
        deck=simulator.create_starting_deck("human"),
        player_hp=cfg.start_hp,
        max_hp=cfg.start_hp,
        resist=cfg.resist,
        node_type="normal",
        floor=1,
    )
    assert result.winner in {"player", "enemy", "draw"}
    assert any("의도" in line for line in result.log)
    assert hp_after >= 0
    assert len(deck_after) >= 1


def test_run_reproducible_same_seed():
    run1 = simulator.run_game(seed=21, species="human")
    run2 = simulator.run_game(seed=21, species="human")
    assert run1.cleared == run2.cleared
    assert run1.floor_reached == run2.floor_reached
    assert run1.gold == run2.gold
    assert run1.deck_size == run2.deck_size
    assert run1.log == run2.log


def test_generate_act1_path_properties():
    path = simulator.generate_act1_path(7)
    assert len(path) == 16
    assert path[-1] == "boss"
    assert all(node in set(simulator.NODE_TYPES) | {"boss"} for node in path)
    assert all(node != "elite" for node in path[:3])
    assert path[14] in {"rest", "event"}


def test_species_variation_changes_start_hp():
    human = simulator.run_game(seed=1, species="human")
    draco = simulator.run_game(seed=1, species="draconian")
    assert human.species == "human"
    assert draco.species == "draconian"
    assert human.log[0] != draco.log[0]
