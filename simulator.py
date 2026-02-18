#!/usr/bin/env python3
"""DCSS_SS MVP 텍스트 게임 시뮬레이터 (전투 + 1개 Act 런)."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from math import floor
from typing import Dict, List, Optional, Tuple

ELEMENTS = ("fire", "cold", "electric", "poison")
NODE_TYPES = ("normal", "event", "rest", "shop", "elite")


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


@dataclass
class RunResult:
    cleared: bool
    floor_reached: int
    gold: int
    deck_size: int
    species: str
    relics: List[str]
    log: List[str]


@dataclass
class SpeciesConfig:
    name: str
    start_hp: int
    resist: Dict[str, float]
    start_relic: str


SPECIES: Dict[str, SpeciesConfig] = {
    "human": SpeciesConfig("human", 80, {"fire": 0.1, "cold": 0.1, "electric": 0.1, "poison": 0.1}, "Adventurer's Charm"),
    "draconian": SpeciesConfig("draconian", 88, {"fire": 0.3, "cold": 0.0, "electric": 0.1, "poison": 0.05}, "Scale Carapace"),
}


def create_starting_deck(species: str) -> List[Card]:
    base = [
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
    if species == "draconian":
        base.append(Card("Scale Bash", 1, "attack_plus"))
    else:
        base.append(Card("Focus", 1, "skill_plus"))
    return base


def reward_card_pool() -> List[Card]:
    return [
        Card("Strike+", 1, "attack_plus"),
        Card("Shield", 1, "skill_plus"),
        Card("Spark", 1, "attack_electric"),
        Card("Frost Bite", 1, "attack_cold"),
        Card("Venom Fang", 1, "attack_poison_plus"),
    ]


def calc_damage(attacker: Combatant, defender: Combatant, base_damage: int, element: str = "physical") -> int:
    attack_mult = 0.75 if attacker.status.weak > 0 else 1.0
    defense_mult = 1.5 if defender.status.vulnerable > 0 else 1.0
    adjusted = floor(base_damage * attack_mult * defense_mult)
    if element in ELEMENTS:
        adjusted = floor(adjusted * (1.0 - defender.resist.get(element, 0.0)))
    final = max(0, adjusted - defender.block)
    defender.block = max(0, defender.block - adjusted)
    return final


def apply_poison(target: Combatant, log: List[str]) -> None:
    if target.status.poison > 0 and target.is_alive():
        damage = target.status.poison
        target.hp -= damage
        log.append(f"- {target.name} 독 피해 {damage} (HP {target.hp}/{target.max_hp})")
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
    return EnemyIntent("debuff_vulnerable" if rng.random() < 0.5 else "debuff_weak", 1)


def describe_enemy_intent(intent: EnemyIntent) -> str:
    mapping = {
        "attack": f"공격 {intent.value}",
        "buff": f"방어도 +{intent.value}",
        "debuff_vulnerable": "취약 1 부여",
        "debuff_weak": "약화 1 부여",
    }
    return mapping[intent.action]


def resolve_card(card: Card, player: Combatant, enemy: Combatant, state: PlayerState, log: List[str]) -> None:
    if card.kind == "attack":
        dmg = calc_damage(player, enemy, 6)
        enemy.hp -= dmg
        log.append(f"- Strike {dmg} (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "skill":
        player.block += 5
        log.append(f"- Guard 방어 +5 (현재 {player.block})")
    elif card.kind == "attack_fire":
        dmg = calc_damage(player, enemy, 7, "fire")
        enemy.hp -= dmg
        log.append(f"- Ember {dmg} (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "attack_poison":
        dmg = calc_damage(player, enemy, 3, "poison")
        enemy.hp -= dmg
        enemy.status.poison += 2
        log.append(f"- Poison Dart {dmg} + 독2 (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "attack_plus":
        dmg = calc_damage(player, enemy, 9)
        enemy.hp -= dmg
        log.append(f"- Strike+ {dmg} (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "skill_plus":
        player.block += 8
        log.append(f"- Shield 방어 +8 (현재 {player.block})")
    elif card.kind == "attack_electric":
        dmg = calc_damage(player, enemy, 6, "electric")
        enemy.hp -= dmg
        enemy.status.vulnerable += 1
        log.append(f"- Spark {dmg} + 취약1 (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "attack_cold":
        dmg = calc_damage(player, enemy, 5, "cold")
        enemy.hp -= dmg
        enemy.status.weak += 1
        log.append(f"- Frost Bite {dmg} + 약화1 (적 HP {enemy.hp}/{enemy.max_hp})")
    elif card.kind == "attack_poison_plus":
        dmg = calc_damage(player, enemy, 5, "poison")
        enemy.hp -= dmg
        enemy.status.poison += 3
        log.append(f"- Venom Fang {dmg} + 독3 (적 HP {enemy.hp}/{enemy.max_hp})")
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
        playable_idx = next((i for i, c in enumerate(state.hand) if c.cost <= state.energy and c.kind != "status_burn"), None)
        if playable_idx is None:
            break
        card = state.hand.pop(playable_idx)
        state.energy -= card.cost
        resolve_card(card, player, enemy, state, log)

    burn_count = sum(1 for c in state.hand if c.kind == "status_burn")
    if burn_count > 0:
        burn_damage = burn_count * 2
        player.hp -= burn_damage
        log.append(f"- 화상(Burn) {burn_count}장 피해 {burn_damage} (HP {player.hp}/{player.max_hp})")

    state.discard_pile.extend(state.hand)
    state.hand.clear()
    if player.status.vulnerable > 0:
        player.status.vulnerable -= 1
    if player.status.weak > 0:
        player.status.weak -= 1
    player.block = 0


def enemy_turn(enemy: Combatant, player: Combatant, intent: EnemyIntent, log: List[str]) -> None:
    if intent.action == "attack":
        dmg = calc_damage(enemy, player, intent.value)
        player.hp -= dmg
        log.append(f"- {enemy.name} 공격 {dmg} (플레이어 HP {player.hp}/{player.max_hp})")
    elif intent.action == "buff":
        enemy.block += intent.value
        log.append(f"- {enemy.name} 방어도 +{intent.value}")
    elif intent.action == "debuff_vulnerable":
        player.status.vulnerable += intent.value
        log.append(f"- {enemy.name} 취약 부여")
    else:
        player.status.weak += intent.value
        log.append(f"- {enemy.name} 약화 부여")

    if enemy.status.vulnerable > 0:
        enemy.status.vulnerable -= 1
    if enemy.status.weak > 0:
        enemy.status.weak -= 1
    enemy.block = 0


def collect_current_deck(state: PlayerState) -> List[Card]:
    # exhaust_pile은 런 중 덱에서 제외
    return list(state.draw_pile) + list(state.discard_pile) + list(state.hand)


def build_enemy(node_type: str, floor: int) -> Combatant:
    scale = max(0, floor - 1)
    if node_type == "elite":
        return Combatant("엘리트 슬라임", 58 + scale * 3, 58 + scale * 3, 9 + scale // 3, resist={"poison": 0.2})
    if node_type == "boss":
        return Combatant("Act1 보스 슬라임 군주", 95, 95, 12, resist={"poison": 0.25, "fire": 0.15})
    return Combatant("슬라임", 36 + scale * 2, 36 + scale * 2, 7 + scale // 4, resist={"poison": 0.1})


def run_battle(seed: int, deck: List[Card], player_hp: int, max_hp: int, resist: Dict[str, float], node_type: str, floor: int, max_turns: int = 25) -> Tuple[BattleResult, List[Card], int]:
    rng = random.Random(seed)
    log: List[str] = []
    player = Combatant("플레이어", player_hp, max_hp, 6, resist=resist.copy())
    enemy = build_enemy(node_type, floor)
    draw = list(deck)
    rng.shuffle(draw)
    state = PlayerState(draw_pile=draw)
    intent = choose_enemy_intent(rng, enemy)

    for turn in range(1, max_turns + 1):
        log.append(f"\n[턴 {turn}] 적 의도: {describe_enemy_intent(intent)}")
        player_turn(player, enemy, state, rng, log)
        if not enemy.is_alive():
            log.append("- 전투 승리")
            return BattleResult("player", turn, log), collect_current_deck(state), max(0, player.hp)

        apply_poison(enemy, log)
        if enemy.is_alive():
            enemy_turn(enemy, player, intent, log)
            intent = choose_enemy_intent(rng, enemy)
        if not player.is_alive():
            log.append("- 플레이어 사망")
            return BattleResult("enemy", turn, log), collect_current_deck(state), 0

    winner = "player" if player.hp > enemy.hp else "enemy" if enemy.hp > player.hp else "draw"
    return BattleResult(winner, max_turns, log), collect_current_deck(state), max(0, player.hp)


def generate_act1_path(seed: int) -> List[str]:
    rng = random.Random(seed)
    path: List[str] = []
    last_rest = False
    last_shop = -10
    for floor in range(1, 16):
        if floor <= 3:
            node = rng.choice(["normal", "event", "rest", "shop"])
        elif floor == 15:
            node = rng.choice(["rest", "event"])
        else:
            pool = ["normal"] * 5 + ["event"] * 2 + ["rest"] * 2 + ["shop"] + ["elite"]
            node = rng.choice(pool)

        if node == "rest" and last_rest:
            node = "normal"
        if node == "shop" and floor - last_shop < 4:
            node = "event"

        if node == "rest":
            last_rest = True
        else:
            last_rest = False
        if node == "shop":
            last_shop = floor
        path.append(node)
    path.append("boss")
    return path


def pick_reward_card(deck: List[Card], rng: random.Random) -> Card:
    choices = rng.sample(reward_card_pool(), k=3)
    attack_kinds = {"attack_plus", "attack_fire", "attack_electric", "attack_cold", "attack_poison_plus", "attack_poison", "attack"}
    attacks = sum(1 for c in deck if c.kind in attack_kinds)
    skills = len(deck) - attacks
    if attacks < skills:
        preferred = next((c for c in choices if "attack" in c.kind), choices[0])
    else:
        preferred = next((c for c in choices if "skill" in c.kind), choices[0])
    return preferred


def run_game(seed: int = 42, species: str = "human") -> RunResult:
    if species not in SPECIES:
        raise ValueError(f"unknown species: {species}")

    cfg = SPECIES[species]
    rng = random.Random(seed)
    path = generate_act1_path(seed)
    log: List[str] = [f"종족: {species}, 시작 유물: {cfg.start_relic}"]

    deck = create_starting_deck(species)
    hp = cfg.start_hp
    max_hp = cfg.start_hp
    gold = 99
    relics = [cfg.start_relic]

    for floor, node in enumerate(path, start=1):
        log.append(f"\n=== 층 {floor}: {node} ===")
        if node in {"normal", "elite", "boss"}:
            battle_seed = rng.randint(0, 1_000_000)
            battle, deck, hp = run_battle(battle_seed, deck, hp, max_hp, cfg.resist, node, floor)
            log.extend(battle.log)
            if battle.winner != "player":
                return RunResult(False, floor, gold, len(deck), species, relics, log)

            gain = 18 if node == "normal" else 35 if node == "elite" else 80
            gold += gain
            hp = min(max_hp, hp + 6)
            log.append(f"- 전투 보상 골드 +{gain} (총 {gold}), 전투 후 회복 +6 (HP {hp}/{max_hp})")

            if node != "boss":
                reward = pick_reward_card(deck, rng)
                deck.append(reward)
                log.append(f"- 카드 보상 획득: {reward.name} (덱 {len(deck)}장)")

                if rng.random() < (0.2 if node == "elite" else 0.08):
                    relic = "Minor Relic" if node == "normal" else "Elite Relic"
                    relics.append(relic)
                    log.append(f"- 유물 획득: {relic}")

        elif node == "rest":
            if hp < max_hp * 0.7:
                heal = min(24, max_hp - hp)
                hp += heal
                log.append(f"- 휴식: HP +{heal} (현재 {hp}/{max_hp})")
            else:
                idx = next((i for i, c in enumerate(deck) if c.kind in {"attack", "skill"}), None)
                if idx is not None:
                    upgraded = Card(deck[idx].name + "+", deck[idx].cost, "attack_plus" if deck[idx].kind == "attack" else "skill_plus")
                    deck[idx] = upgraded
                    log.append(f"- 휴식: 카드 강화 {upgraded.name}")
                else:
                    log.append("- 휴식: 강화할 카드 없음")

        elif node == "shop":
            log.append(f"- 상점 입장 (골드 {gold})")
            if gold >= 75:
                card = rng.choice(reward_card_pool())
                deck.append(card)
                gold -= 75
                log.append(f"- 카드 구매: {card.name} (잔액 {gold})")
            elif gold >= 50:
                hp = min(max_hp, hp + 12)
                gold -= 50
                log.append(f"- 회복 구매: HP +12 (현재 {hp}/{max_hp}, 잔액 {gold})")
            else:
                log.append("- 구매 스킵")

        else:  # event
            if rng.random() < 0.5:
                hp_loss = min(8, max(1, hp - 1))
                hp -= hp_loss
                gold += 45
                log.append(f"- 이벤트: 위험 선택 HP -{hp_loss}, 골드 +45 (총 {gold})")
            else:
                card = Card("Event Boon", 1, "skill_plus")
                deck.append(card)
                log.append(f"- 이벤트: 카드 획득 {card.name}")

    return RunResult(True, len(path), gold, len(deck), species, relics, log)


def main() -> None:
    parser = argparse.ArgumentParser(description="DCSS_SS Act1 텍스트 시뮬레이터")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--species", choices=sorted(SPECIES.keys()), default="human")
    parser.add_argument("--mode", choices=["run", "battle"], default="run")
    args = parser.parse_args()

    if args.mode == "run":
        run = run_game(seed=args.seed, species=args.species)
        print("=== 런 로그 ===")
        for line in run.log:
            print(line)
        print("\n=== 결과 ===")
        print(f"클리어: {run.cleared}")
        print(f"도달 층: {run.floor_reached}")
        print(f"골드: {run.gold}")
        print(f"덱 크기: {run.deck_size}")
        print(f"유물: {', '.join(run.relics)}")
    else:
        deck = create_starting_deck(args.species)
        cfg = SPECIES[args.species]
        result, _, hp = run_battle(args.seed, deck, cfg.start_hp, cfg.start_hp, cfg.resist, "normal", 1)
        print("=== 전투 로그 ===")
        for line in result.log:
            print(line)
        print(f"\n승자: {result.winner}, 남은 HP: {hp}")


if __name__ == "__main__":
    main()
