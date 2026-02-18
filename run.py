"""초보자용 실행 스크립트: `python run.py`로 샘플 전투 로그를 실행합니다."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dcss_ss.cli import main


if __name__ == "__main__":
    main()
