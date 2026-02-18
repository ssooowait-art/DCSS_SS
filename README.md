# DCSS_SS
던전크롤과 슬레이더스파이어 합친 게임 만들어볼게

## 현재 상태
이 저장소는 우선 기획 문서(`docs/core-loop.md`)를 기준으로,
MVP 전투 루프를 검증하기 위한 **CLI 시뮬레이터**를 포함한다.
현재는 드로우/버림/소멸 더미, 적 Intent 예고, Burn 카드 기반 턴 종료 피해,
그리고 전투→보상→노드 이동을 잇는 간단한 `act` 모드까지 반영했다.

## 빠른 실행
```bash
python3 simulator.py --mode battle --seed 42 --max-turns 20
python3 simulator.py --mode act --seed 42 --floors 6
```

## 테스트
```bash
python3 -m pytest -q
```

## 다음 계획
- 상세 단계는 `docs/next-plan.md`에 정리했다.
- 우선순위: **전투 규칙 정확도 보강 → 카드/덱 시스템 실제화 → 맵 루프 연결**
