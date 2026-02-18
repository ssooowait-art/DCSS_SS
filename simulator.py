#!/usr/bin/env python3
"""DCSS_SS MVP 전투 루프 CLI 시뮬레이터."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from math import floor
from typing import Dict, List


ELEMENTS = ("fire", "cold", "electric", "poison")


@dataclass
class Status:
    poison: int = 0
    vulnerable: int = 0
    weak: int = 0
    burn: int = 0


@dataclass
class Combatant:
    name: str
    hp: int
    max_hp: int
    base_attack: int
    block: int = 0
    status: Status = field(default_factory=Status)
    resist: Dict[str, float] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class PlayerState:
    energy: int = 3
    hand_size: int = 5
    max_hand_size: int = 10


@dataclass
class BattleResult:
    winner: str
    turns: int
    log: List[str]


def calc_damage(attacker: Combatant, defender: Combatant, base_damage: int, element: str = "physical") -> int:
    attack_mult = 0.75 if attacker.status.weak > 0 else 1.0
    defense_mult = 1.5 if defender.status.vulnerable > 0 else 1.0
    adjusted = floor(base_damage * attack_mult * defense_mult)

    if element in ELEMENTS:
        resist_rate = defender.resist.get(element, 0.0)
        adjusted = floor(adjusted * (1.0 - resist_rate))

    final = max(0, adjusted - defender.block)
    defender.block = max(0, defender.block - adjusted)
    return final


def start_of_turn_status(target: Combatant, log: List[str]) -> None:
    if target.status.poison > 0 and target.is_alive():
        poison_damage = target.status.poison
        target.hp -= poison_damage
        log.append(f"- {target.name} 독 피해 {poison_damage} (HP {target.hp}/{target.max_hp})")
        target.status.poison -= 1


def end_of_player_turn(player: Combatant, state: PlayerState, log: List[str]) -> None:
    if player.status.burn > 0:
        burn_damage = 2 * state.hand_size
        player.hp -= burn_damage
        log.append(f"- {player.name} 화상 피해 {burn_damage} (HP {player.hp}/{player.max_hp})")

    if player.status.vulnerable > 0:
        player.status.vulnerable -= 1
    if player.status.weak > 0:
        player.status.weak -= 1

    player.block = 0


def enemy_turn(enemy: Combatant, player: Combatant, log: List[str], rng: random.Random) -> None:
    if not enemy.is_alive():
        return

    action = rng.choice(["attack", "attack", "buff", "debuff"])
    if action == "attack":
        damage = calc_damage(enemy, player, enemy.base_attack)
        player.hp -= damage
        log.append(f"- {enemy.name} 공격 {damage} (플레이어 HP {player.hp}/{player.max_hp})")
    elif action == "buff":
        enemy.block += 5
        log.append(f"- {enemy.name} 방어도 +5")
    else:
        if rng.random() < 0.5:
            player.status.vulnerable += 1
            log.append(f"- {enemy.name} 취약 부여 (플레이어 취약 {player.status.vulnerable})")
        else:
            player.status.weak += 1
            log.append(f"- {enemy.name} 약화 부여 (플레이어 약화 {player.status.weak})")


def player_turn(player: Combatant, enemy: Combatant, state: PlayerState, log: List[str], rng: random.Random) -> None:
    state.energy = 3
    state.hand_size = min(5, state.max_hand_size)
    start_of_turn_status(player, log)
    if not player.is_alive():
        return

    while state.energy > 0 and enemy.is_alive():
        card = rng.choice(["strike", "strike", "guard", "ember", "poison_dart"])
        if card == "strike":
            damage = calc_damage(player, enemy, 6)
            enemy.hp -= damage
            log.append(f"- 플레이어 Strike {damage} (적 HP {enemy.hp}/{enemy.max_hp})")
            state.energy -= 1
        elif card == "guard":
            player.block += 5
            log.append(f"- 플레이어 Guard 방어도 +5 (현재 {player.block})")
            state.energy -= 1
        elif card == "ember":
            damage = calc_damage(player, enemy, 7, element="fire")
            enemy.hp -= damage
            log.append(f"- 플레이어 Ember(화염) {damage} (적 HP {enemy.hp}/{enemy.max_hp})")
            state.energy -= 1
        else:
            damage = calc_damage(player, enemy, 3, element="poison")
            enemy.hp -= damage
            enemy.status.poison += 2
            log.append(
                f"- 플레이어 Poison Dart {damage} + 독2 (적 HP {enemy.hp}/{enemy.max_hp}, 독 {enemy.status.poison})"
            )
            state.energy -= 1

    end_of_player_turn(player, state, log)


def run_battle(seed: int = 42, max_turns: int = 20) -> BattleResult:
    rng = random.Random(seed)
    log: List[str] = []

    player = Combatant(
        name="플레이어",
        hp=80,
        max_hp=80,
        base_attack=6,
        resist={"fire": 0.3, "cold": 0.1, "electric": 0.0, "poison": 0.25},
    )
    enemy = Combatant(name="슬라임 엘리트", hp=55, max_hp=55, base_attack=9, resist={"poison": 0.2})
    player_state = PlayerState()

    for turn in range(1, max_turns + 1):
        if not player.is_alive() or not enemy.is_alive():
            break

        log.append(f"\n[턴 {turn}] 시작")
        player_turn(player, enemy, player_state, log, rng)

        if not enemy.is_alive():
            log.append("- 적 전멸! 전투 승리")
            return BattleResult(winner="player", turns=turn, log=log)

        start_of_turn_status(enemy, log)
        if enemy.is_alive():
            enemy_turn(enemy, player, log, rng)

        if not player.is_alive():
            log.append("- 플레이어 사망. 런 종료")
            return BattleResult(winner="enemy", turns=turn, log=log)

    winner = "draw"
    if player.hp > enemy.hp:
        winner = "player"
    elif enemy.hp > player.hp:
        winner = "enemy"

    log.append(f"- 최대 턴({max_turns}) 도달. 판정 승자: {winner}")
    return BattleResult(winner=winner, turns=max_turns, log=log)


def main() -> None:
    parser = argparse.ArgumentParser(description="DCSS_SS 전투 루프 CLI 시뮬레이터")
    parser.add_argument("--seed", type=int, default=42, help="난수 시드")
    parser.add_argument("--max-turns", type=int, default=20, help="최대 턴 수")
    args = parser.parse_args()

    result = run_battle(seed=args.seed, max_turns=args.max_turns)
    print("=== 전투 로그 ===")
    for line in result.log:
        print(line)
    print("\n=== 결과 ===")
    print(f"승자: {result.winner}")
    print(f"턴 수: {result.turns}")


if __name__ == "__main__":
    main()
