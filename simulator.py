#!/usr/bin/env python3
"""DCSS_SS MVP 전투 루프 CLI 시뮬레이터."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from math import floor
from typing import Dict, List, Optional


ELEMENTS = ("fire", "cold", "electric", "poison")


@dataclass
class Status:
    poison: int = 0
    vulnerable: int = 0
    weak: int = 0


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


@dataclass(frozen=True)
class Card:
    name: str
    cost: int
    kind: str


@dataclass
class EnemyIntent:
    action: str
    value: int


@dataclass
class PlayerState:
    energy: int = 3
    max_hand_size: int = 10
    draw_pile: List[Card] = field(default_factory=list)
    discard_pile: List[Card] = field(default_factory=list)
    exhaust_pile: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)


@dataclass
class BattleResult:
    winner: str
    turns: int
    log: List[str]


def create_starting_deck() -> List[Card]:
    deck = [
        Card("Strike", 1, "attack"),
        Card("Strike", 1, "attack"),
        Card("Strike", 1, "attack"),
        Card("Strike", 1, "attack"),
        Card("Guard", 1, "skill"),
        Card("Guard", 1, "skill"),
        Card("Guard", 1, "skill"),
        Card("Ember", 1, "attack_fire"),
        Card("Poison Dart", 1, "attack_poison"),
        Card("Burn", 0, "status_burn"),
    ]
    return deck


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


def apply_poison(target: Combatant, log: List[str]) -> None:
    if target.status.poison > 0 and target.is_alive():
        poison_damage = target.status.poison
        target.hp -= poison_damage
        log.append(f"- {target.name} 독 피해 {poison_damage} (HP {target.hp}/{target.max_hp})")
        target.status.poison -= 1


def shuffle_discard_into_draw(state: PlayerState, rng: random.Random, log: List[str]) -> None:
    if not state.draw_pile and state.discard_pile:
        state.draw_pile = list(state.discard_pile)
        state.discard_pile.clear()
        rng.shuffle(state.draw_pile)
        log.append("- 드로우 더미 소진 → 버림 더미 셔플")


def draw_cards(state: PlayerState, count: int, rng: random.Random, log: List[str]) -> None:
    for _ in range(count):
        if len(state.hand) >= state.max_hand_size:
            log.append("- 최대 손패 도달: 추가 드로우 무시")
            break
        shuffle_discard_into_draw(state, rng, log)
        if not state.draw_pile:
            break
        state.hand.append(state.draw_pile.pop())


def choose_enemy_intent(rng: random.Random, enemy: Combatant) -> EnemyIntent:
    roll = rng.choice(["attack", "attack", "buff", "debuff"])
    if roll == "attack":
        return EnemyIntent("attack", enemy.base_attack)
    if roll == "buff":
        return EnemyIntent("buff", 5)
    if rng.random() < 0.5:
        return EnemyIntent("debuff_vulnerable", 1)
    return EnemyIntent("debuff_weak", 1)


def describe_enemy_intent(intent: EnemyIntent) -> str:
    if intent.action == "attack":
        return f"공격 {intent.value}"
    if intent.action == "buff":
        return f"방어도 +{intent.value}"
    if intent.action == "debuff_vulnerable":
        return "취약 1 부여"
    return "약화 1 부여"


def resolve_card(card: Card, player: Combatant, enemy: Combatant, state: PlayerState, log: List[str]) -> None:
    if card.kind == "attack":
        damage = calc_damage(player, enemy, 6)
        enemy.hp -= damage
        log.append(f"- 플레이어 Strike {damage} (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "skill":
        player.block += 5
        log.append(f"- 플레이어 Guard 방어도 +5 (현재 {player.block})")
    elif card.kind == "attack_fire":
        damage = calc_damage(player, enemy, 7, element="fire")
        enemy.hp -= damage
        log.append(f"- 플레이어 Ember(화염) {damage} (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "attack_poison":
        damage = calc_damage(player, enemy, 3, element="poison")
        enemy.hp -= damage
        enemy.status.poison += 2
        log.append(f"- 플레이어 Poison Dart {damage} + 독2 (적 HP {enemy.hp}/{enemy.max_hp}, 독 {enemy.status.poison})")
    else:
        log.append("- Burn 카드: 사용 불가")

    if card.kind == "status_burn":
        state.exhaust_pile.append(card)
    else:
        state.discard_pile.append(card)


def player_turn(player: Combatant, enemy: Combatant, state: PlayerState, rng: random.Random, log: List[str]) -> None:
    state.energy = 3
    draw_cards(state, 5, rng, log)
    apply_poison(player, log)
    if not player.is_alive():
        return

    while state.energy > 0 and enemy.is_alive():
        playable_idx: Optional[int] = None
        for i, card in enumerate(state.hand):
            if card.cost <= state.energy and card.kind != "status_burn":
                playable_idx = i
                break
        if playable_idx is None:
            break

        card = state.hand.pop(playable_idx)
        state.energy -= card.cost
        resolve_card(card, player, enemy, state, log)

    burn_count = sum(1 for c in state.hand if c.kind == "status_burn")
    if burn_count > 0:
        burn_damage = burn_count * 2
        player.hp -= burn_damage
        log.append(f"- 플레이어 화상(Burn) {burn_count}장 피해 {burn_damage} (HP {player.hp}/{player.max_hp})")

    state.discard_pile.extend(state.hand)
    state.hand.clear()

    if player.status.vulnerable > 0:
        player.status.vulnerable -= 1
    if player.status.weak > 0:
        player.status.weak -= 1
    player.block = 0


def enemy_turn(enemy: Combatant, player: Combatant, intent: EnemyIntent, log: List[str]) -> None:
    if not enemy.is_alive():
        return

    if intent.action == "attack":
        damage = calc_damage(enemy, player, intent.value)
        player.hp -= damage
        log.append(f"- {enemy.name} 공격 {damage} (플레이어 HP {player.hp}/{player.max_hp})")
    elif intent.action == "buff":
        enemy.block += intent.value
        log.append(f"- {enemy.name} 방어도 +{intent.value}")
    elif intent.action == "debuff_vulnerable":
        player.status.vulnerable += intent.value
        log.append(f"- {enemy.name} 취약 부여 (플레이어 취약 {player.status.vulnerable})")
    else:
        player.status.weak += intent.value
        log.append(f"- {enemy.name} 약화 부여 (플레이어 약화 {player.status.weak})")

    if enemy.status.vulnerable > 0:
        enemy.status.vulnerable -= 1
    if enemy.status.weak > 0:
        enemy.status.weak -= 1
    enemy.block = 0


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

    deck = create_starting_deck()
    rng.shuffle(deck)
    state = PlayerState(draw_pile=deck)

    next_enemy_intent = choose_enemy_intent(rng, enemy)

    for turn in range(1, max_turns + 1):
        if not player.is_alive() or not enemy.is_alive():
            break

        log.append(f"\n[턴 {turn}] 시작")
        log.append(f"- 적 의도(Intent): {describe_enemy_intent(next_enemy_intent)}")
        player_turn(player, enemy, state, rng, log)

        if not enemy.is_alive():
            log.append("- 적 전멸! 전투 승리")
            return BattleResult(winner="player", turns=turn, log=log)

        apply_poison(enemy, log)
        if enemy.is_alive():
            enemy_turn(enemy, player, next_enemy_intent, log)
            next_enemy_intent = choose_enemy_intent(rng, enemy)

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
