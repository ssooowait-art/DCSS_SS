# DCSS_SS
던전크롤과 슬레이더스파이어 합친 게임 만들어볼게

## 현재 상태 (Prototype)
문서화된 코어 루프를 기반으로, 전투 엔진의 최소 프로토타입을 Python으로 추가했습니다.

포함된 항목:
- 턴 시작/행동/종료/적 턴 진행
- 에너지(3), 드로우(5), 최대 손패(10), 드로우 고갈 시 셔플
- 피해 공식 + 방어도 + 속성 저항
- 상태이상 4종 타이밍 반영(독/취약/약화/화상)
- 전투 로그 출력

## 실행 방법
```bash
PYTHONPATH=src python -m dcss_ss.cli
```

## 테스트
```bash
PYTHONPATH=src python -m unittest discover -s tests
```
