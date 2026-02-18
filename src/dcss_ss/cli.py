from __future__ import annotations

import argparse

from .engine import run_sample_battle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DCSS_SS 전투 프로토타입을 실행하고 로그를 출력합니다."
    )
    parser.add_argument("--seed", type=int, default=7, help="랜덤 시드 (기본값: 7)")
    parser.add_argument("--turns", type=int, default=6, help="최대 턴 수 (기본값: 6)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    state = run_sample_battle(seed=args.seed, max_turns=args.turns)
    print("\n".join(state.logs))


if __name__ == "__main__":
    main()
