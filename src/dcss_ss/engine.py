from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from random import Random
from typing import Dict, List

BASE_ENERGY = 3
TURN_DRAW = 5
MAX_HAND = 10


@dataclass
class StatusEffects:
    poison: int = 0
    vulnerable: int = 0
    weak: int = 0
    burn: int = 0

    def copy(self) -> "StatusEffects":
        return StatusEffects(
            poison=self.poison,
            vulnerable=self.vulnerable,
            weak=self.weak,
            burn=self.burn,
        )


@dataclass
class ActorState:
    name: str
    hp: int
    max_hp: int
    block: int = 0
    statuses: StatusEffects = field(default_factory=StatusEffects)
    resistances: Dict[str, float] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class CombatState:
    player: ActorState
    enemy: ActorState
    turn: int = 1
    energy: int = BASE_ENERGY
    draw_pile: List[str] = field(default_factory=list)
    hand: List[str] = field(default_factory=list)
    discard: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


class CombatEngine:
    """Single-enemy prototype aligned with docs/core-loop.md."""

    def __init__(self, rng_seed: int = 42):
        self.rng = Random(rng_seed)

    @staticmethod
    def calculate_attack_damage(
        base_damage: int,
        attacker_mod: float,
        defender_mod: float,
        defender_block: int,
    ) -> int:
        raw = floor(base_damage * attacker_mod * defender_mod)
        return max(raw - defender_block, 0)

    @staticmethod
    def apply_resistance(damage: int, resistance_rate: float) -> int:
        resistance_rate = min(max(resistance_rate, 0.0), 0.95)
        return floor(damage * (1 - resistance_rate))

    def start_turn(self, state: CombatState) -> None:
        state.logs.append(f"--- TURN {state.turn} START ---")
        state.energy = BASE_ENERGY
        state.logs.append(f"Energy refilled to {state.energy}")

        # Draw cards and overflow to discard
        for _ in range(TURN_DRAW):
            self.draw_one(state)

        self.apply_poison_tick(state.player, state)

    def apply_poison_tick(self, actor: ActorState, state: CombatState) -> None:
        if actor.statuses.poison > 0:
            poison_damage = actor.statuses.poison
            actor.hp = max(actor.hp - poison_damage, 0)
            actor.statuses.poison -= 1
            state.logs.append(
                f"{actor.name} takes {poison_damage} poison damage (poison->{actor.statuses.poison})"
            )

    def draw_one(self, state: CombatState) -> None:
        if not state.draw_pile and state.discard:
            state.draw_pile = state.discard[:]
            state.discard = []
            self.rng.shuffle(state.draw_pile)
            state.logs.append("Draw pile exhausted: shuffled discard into draw pile")

        if not state.draw_pile:
            return

        card = state.draw_pile.pop(0)
        if len(state.hand) >= MAX_HAND:
            state.discard.append(card)
            state.logs.append(f"Hand overflow: discarded {card}")
        else:
            state.hand.append(card)
            state.logs.append(f"Drew card: {card}")

    def play_strike(self, state: CombatState, base_damage: int = 6, element: str | None = None) -> bool:
        if state.energy < 1:
            state.logs.append("Not enough energy to play Strike")
            return False

        state.energy -= 1
        attacker_mod = 0.75 if state.player.statuses.weak > 0 else 1.0
        defender_mod = 1.5 if state.enemy.statuses.vulnerable > 0 else 1.0
        damage = self.calculate_attack_damage(
            base_damage=base_damage,
            attacker_mod=attacker_mod,
            defender_mod=defender_mod,
            defender_block=state.enemy.block,
        )

        if element:
            resist = state.enemy.resistances.get(element, 0.0)
            damage = self.apply_resistance(damage, resist)

        state.enemy.hp = max(state.enemy.hp - damage, 0)
        state.logs.append(
            f"Player used Strike for {damage} damage (enemy hp {state.enemy.hp}, energy {state.energy})"
        )
        return True

    def end_player_turn(self, state: CombatState) -> None:
        burn_damage = state.player.statuses.burn * len(state.hand) * 2
        if burn_damage > 0:
            state.player.hp = max(state.player.hp - burn_damage, 0)
            state.logs.append(
                f"Burn triggers for {burn_damage} damage ({len(state.hand)} cards in hand)"
            )

        if state.player.statuses.vulnerable > 0:
            state.player.statuses.vulnerable -= 1
        if state.player.statuses.weak > 0:
            state.player.statuses.weak -= 1

        if state.hand:
            state.logs.append(f"Discarding hand: {', '.join(state.hand)}")
        state.discard.extend(state.hand)
        state.hand = []

    def enemy_turn(self, state: CombatState, base_damage: int = 8, element: str | None = None) -> None:
        if not state.enemy.is_alive():
            return

        attacker_mod = 0.75 if state.enemy.statuses.weak > 0 else 1.0
        defender_mod = 1.5 if state.player.statuses.vulnerable > 0 else 1.0
        damage = self.calculate_attack_damage(
            base_damage=base_damage,
            attacker_mod=attacker_mod,
            defender_mod=defender_mod,
            defender_block=state.player.block,
        )
        if element:
            resist = state.player.resistances.get(element, 0.0)
            damage = self.apply_resistance(damage, resist)

        state.player.hp = max(state.player.hp - damage, 0)
        state.logs.append(f"Enemy attacks for {damage} damage (player hp {state.player.hp})")

        if state.enemy.statuses.vulnerable > 0:
            state.enemy.statuses.vulnerable -= 1
        if state.enemy.statuses.weak > 0:
            state.enemy.statuses.weak -= 1

    def end_round(self, state: CombatState) -> None:
        state.player.block = 0
        state.enemy.block = 0
        state.turn += 1


DEFAULT_DECK = [
    "Strike",
    "Strike",
    "Strike",
    "Strike",
    "Defend",
    "Defend",
    "Defend",
    "Burn",
]


def run_sample_battle(seed: int = 7) -> CombatState:
    engine = CombatEngine(rng_seed=seed)
    draw = DEFAULT_DECK[:]
    engine.rng.shuffle(draw)

    state = CombatState(
        player=ActorState(name="Player", hp=80, max_hp=80, resistances={"fire": 0.2}),
        enemy=ActorState(name="Goblin", hp=35, max_hp=35, resistances={"poison": 0.3}),
        draw_pile=draw,
    )

    # Example statuses for the loop demonstration
    state.player.statuses.burn = 1
    state.enemy.statuses.vulnerable = 1

    while state.player.is_alive() and state.enemy.is_alive() and state.turn <= 6:
        engine.start_turn(state)
        while state.energy > 0 and state.enemy.is_alive():
            engine.play_strike(state, element="fire")
        engine.end_player_turn(state)
        if state.enemy.is_alive() and state.player.is_alive():
            engine.enemy_turn(state)
        engine.end_round(state)

    winner = "player" if state.player.is_alive() and not state.enemy.is_alive() else "enemy/timeout"
    state.logs.append(f"Battle finished. Winner: {winner}")
    return state
