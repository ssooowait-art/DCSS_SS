# DCSS_SS
던전크롤과 슬레이더스파이어 합친 게임 만들어볼게

## 현재 상태
`simulator.py`로 **Act 1(15층 + 보스)** 를 끝까지 진행하는 텍스트 기반 게임 루프를 실행할 수 있다.

포함된 요소:
- 전투: 에너지/드로우/버림/소멸/손패, 상태이상(독/취약/약화/Burn 카드), 저항(화염/냉기/전기/독), 적 Intent
- 런 루프: 노드 진행(일반/엘리트/휴식/상점/이벤트/보스), 전투 보상(골드/카드/유물), 휴식/상점/이벤트 처리
- 종족 2종: `human`, `draconian`

## 실행
```bash
# 전체 런 실행 (기본)
python3 simulator.py --mode run --seed 42 --species human

# 단일 전투 실행
python3 simulator.py --mode battle --seed 42 --species draconian
```

## 테스트
```bash
python3 -m pytest -q
```
