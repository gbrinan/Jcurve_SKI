#!/usr/bin/env python3
"""실행 기록 — run.py가 무슨 일을 했는지 남긴다. 목업 화면은 이것만 읽는다.

왜 필요한가: 목업 HTML의 숫자를 사람이 실행 로그에서 베껴 적으면, 데이터를 고쳤을 때
실행 결과는 바뀌는데 화면은 그대로다. 조용히 어긋난다. 실측으로 확인된 문제다.

사용:
    from trace import Trace
    t = Trace("의료비 판독 AI", "Talent AX실 · HR AI", lv5="의료비 청구 건 판독·지급 판정")
    t.input("청구접수대장", 11, "2026년 7~8월 접수분")
    t.step("증빙서류판독", "자동", "11건 판독 · 판독불가 1건")
    t.fork("지급기준대조", "증강", [("기준 충족", "자동지급상신", 6), ...], note="...")
    t.loop("차이분석조정", "계정검증대사", exit_cond="차이가 0이 되면")
    t.table("지급대장.md", rows, cols)          # 화면에 표로 뜬다
    t.halt("지급승인", "사람고유", "팀장이 승인할 때까지 멈춤", actions=["6건 승인", ...])
    t.save(OUT)                                  # out/trace.json
"""
import json
from pathlib import Path

SCHEMA = 1


class Trace:
    def __init__(self, title, source="", lv4="", lv5=""):
        # mode: "run" = run.py가 실제로 돌린 기록 (숫자가 진짜)
        #       "contract" = orchestrate.py가 계약을 걸어 본 기록 (숫자 없음)
        self.d = {"schema": SCHEMA, "mode": "run", "title": title, "source": source,
                  "lv4": lv4, "lv5": lv5, "inputs": [], "steps": [],
                  "loops": [], "summary": ""}
        self._cycle = None

    # ── 입력 ──
    def input(self, name, count=None, note=""):
        self.d["inputs"].append({"name": name, "count": count, "note": note})
        return self

    # ── 회차 (루프 안에서 부르면 이후 step에 회차가 붙는다) ──
    def cycle(self, n):
        self._cycle = n
        return self

    def _mk(self, kind, skill, human, note):
        s = {"kind": kind, "skill": skill, "human": human, "note": note,
             "files": [], "tables": []}
        if self._cycle is not None:
            s["cycle"] = self._cycle
        self.d["steps"].append(s)
        return s

    # ── 보통 단계 ──
    def step(self, skill, human, note):
        self._cur = self._mk("step", skill, human, note)
        return self

    # ── 갈림길: [(조건, 다음 태스크, 건수), ...] ──
    def fork(self, skill, human, branches, note="", taken=None):
        s = self._mk("fork", skill, human, note)
        s["branches"] = [{"cond": c, "to": t, "count": n} for c, t, n in branches]
        if taken is not None:
            s["taken"] = taken
        self._cur = s
        return self

    # ── 멈추는 자리 ──
    def halt(self, skill, human, note, actions=None, checklist=None):
        s = self._mk("halt", skill, human, note)
        s["actions"] = actions or []
        s["checklist"] = checklist or []
        self._cur = s
        return self

    # ── 루프백 ──
    def loop(self, frm, to, exit_cond="", cycles=None):
        self.d["loops"].append({"from": frm, "to": to,
                                "exit": exit_cond, "cycles": cycles})
        self.d["steps"].append({"kind": "loopback", "from": frm, "to": to,
                                "exit": exit_cond})
        return self

    # ── 직전 단계에 붙는 것들 ──
    def file(self, path, count=None):
        self._cur["files"].append({"path": path, "count": count})
        return self

    def table(self, name, rows, cols, mark=None):
        """mark(row) -> "diff" | "na" | None : 행 강조. 화면에서 색으로 구분된다."""
        self._cur["tables"].append({
            "name": name, "cols": list(cols),
            "rows": [{"cells": [str(r.get(c, "")) for c in cols],
                      "mark": (mark(r) if mark else None)} for r in rows]})
        return self

    def warn(self, text):
        self._cur.setdefault("warns", []).append(text)
        return self

    def done(self, summary):
        self.d["summary"] = summary
        return self

    def save(self, out_dir):
        out = Path(out_dir)
        out.mkdir(exist_ok=True)
        p = out / "trace.json"
        p.write_text(json.dumps(self.d, ensure_ascii=False, indent=1), encoding="utf-8")
        return p


def load(pack_dir):
    p = Path(pack_dir) / "out" / "trace.json"
    if not p.is_file():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("schema") != SCHEMA:
        raise ValueError(f"{p}: trace 형식 버전이 {d.get('schema')}입니다 "
                         f"(이 도구는 {SCHEMA}). run.py를 다시 돌리십시오.")
    return d
