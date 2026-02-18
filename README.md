# DCSS_SS
던전크롤과 슬레이더스파이어 합친 게임 만들어볼게

## 빠르게 실행하기 (가장 쉬운 방법)
프로젝트 폴더에서 아래 한 줄만 실행하세요.

```bash
python run.py
```

## 옵션 넣어서 실행하기
시드와 최대 턴 수를 바꿔서 실험할 수 있습니다.

```bash
python run.py --seed 10 --turns 8
```

## 모듈 방식으로 실행하기 (고급)
```bash
PYTHONPATH=src python -m dcss_ss.cli --seed 7 --turns 6
```

## 테스트
```bash
PYTHONPATH=src python -m unittest discover -s tests
```
