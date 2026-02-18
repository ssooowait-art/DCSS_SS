# Implementation Plan (MVP 착수)

`docs/core-loop.md` 기준으로 실제 구현 순서를 고정합니다.

## 1. 완료됨 (이번 커밋)
- 전투 엔진 최소 골격 (`src/dcss_ss/engine.py`)
- 로그 출력 가능한 샘플 전투 (`run_sample_battle`)
- CLI 실행 엔트리 (`src/dcss_ss/cli.py`)
- 핵심 계산/효과 유닛 테스트 (`tests/test_engine.py`)

## 2. 다음 작업 (우선순위)
1. 카드 타입 확장 (Strike/Defend/Burn 외 카드 효과 분리)
2. 적 Intent 시스템 (의도 표시 + 순환 행동)
3. 맵 생성기 (15층 + 보스, 분포/제한/시드 재현)
4. 종족 2종 시작 세팅 (HP/시작덱/패시브)
5. 보상 선택 루프 연결 (골드/카드 선택/유물 확률)

## 3. Done 체크 기준
- 단일 런 시작~보스까지 끊김 없이 진행
- 로그 기반으로 수치 검증 가능
- 같은 시드에서 맵 재현 가능
