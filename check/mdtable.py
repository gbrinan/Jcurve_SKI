#!/usr/bin/env python3
"""마크다운 표를 읽는다 — 실습 데이터를 .md로 두기 위한 최소 도구.

사용:
    from mdtable import read_tables, read_table
    tables = read_tables("data/원장.md")      # {표제목: [행dict, ...]}
    rows   = read_table("data/원장.md")       # 첫 표만

왜 CSV가 아니라 md인가:
  · 교육생이 파일을 열면 표가 표로 보인다. 엑셀 없이 메모장으로 고칠 수 있다.
  · 표 위에 왜 이 값인지 문장을 적을 수 있다 — CSV는 주석을 달 자리가 없다.
  · 한 파일에 여러 표를 담을 수 있어 data/ 폴더가 얕아진다.

규칙:
  · `## 제목` 아래 오는 첫 표가 그 제목의 표다.
  · 파이프 표만 읽는다. `|---|` 구분선은 건너뛴다.
  · 셀 앞뒤 공백과 **굵게** 표시는 벗겨낸다 — 사람이 강조한 것이 값을 바꾸면 안 된다.
  · 빈 셀은 "" 이다. 0으로 채우지 않는다.
"""
import re
from pathlib import Path

_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    out = []
    for c in s.split("|"):
        c = c.strip()
        c = re.sub(r"^\*\*(.*)\*\*$", r"\1", c)   # **굵게** 벗기기
        c = re.sub(r"^`(.*)`$", r"\1", c)          # `코드` 벗기기
        out.append(c.strip())
    return out


def read_tables(path):
    """{제목: [{칸: 값}, ...]} 를 돌려준다. 제목 없는 표는 '(제목없음)' 아래 모인다."""
    text = Path(path).read_text(encoding="utf-8")
    tables, title, header, rows = {}, "(제목없음)", None, []

    def flush():
        nonlocal header, rows
        if header and rows:
            tables.setdefault(title, []).extend(rows)
        header, rows = None, []

    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if m:
            flush()
            title = m.group(1).strip()
            continue
        if "|" not in line:
            if header:          # 표가 끝났다
                flush()
            continue
        if _SEP.match(line):
            continue            # |---| 구분선
        cs = _cells(line)
        if header is None:
            header = cs
        else:
            if len(cs) < len(header):
                cs += [""] * (len(header) - len(cs))
            rows.append(dict(zip(header, cs[:len(header)])))
    flush()
    return tables


def read_table(path, title=None):
    """표 하나만 — title을 주면 그 제목의 표, 없으면 첫 표."""
    tables = read_tables(path)
    if title is not None:
        for k, v in tables.items():
            if title in k:
                return v
        raise KeyError(f"{path}: 「{title}」 표가 없습니다. 있는 표: {list(tables)}")
    if not tables:
        raise ValueError(f"{path}: 표가 하나도 없습니다")
    return next(iter(tables.values()))


def num(s, default=0):
    """표의 숫자 칸을 정수로. 천 단위 콤마와 원 표시를 허용하고, 빈 칸은 기본값.

    이미 숫자인 값도 그대로 받는다 — 한 번 읽은 행을 다시 넘겨도 터지지 않게.
    """
    if isinstance(s, (int, float)):
        return int(s)
    s = (s or "").replace(",", "").replace("원", "").strip()
    if s in ("", "—", "-", "(미정)"):
        return default
    return int(float(s))


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    t = read_tables(sys.argv[1])
    for name, rows in t.items():
        print(f"\n## {name}  ({len(rows)}행)")
        print(json.dumps(rows[:3], ensure_ascii=False, indent=1))
