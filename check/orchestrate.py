#!/usr/bin/env python3
"""계약 오케스트레이터 — CONTRACT.md의 흐름을 그대로 걸어 실행 기록을 만든다.

사용:
    python3 check/orchestrate.py <팩 경로>                     모든 갈래를 다 걸어 본다
    python3 check/orchestrate.py <팩> --take 계정검증대사=차이분석조정   갈래를 지정
    python3 check/orchestrate.py <팩> --loops 2                루프를 몇 바퀴 돌 것인가

무엇을 하는가:
    CONTRACT.md의 `chain`·`halt_at`과 각 SKILL.md의 `next`/`when`/`loop_to`/`loop_exit`을
    읽어 흐름을 걷고, `out/trace.json`을 남긴다. 그러면 `make_mockup.py`가 목업을 만든다.
    팩마다 run.py를 손으로 쓰지 않아도 된다.

무엇을 하지 않는가 — **이것이 이 도구의 경계다**:
    판단기준은 한국어 문장이다. 「차이가 1건이라도 있으면」이 참인지 이 도구는 모른다.
    그래서 **계산하지 않는다.** 데이터를 읽지 않고, 숫자를 만들지 않는다.
    갈림길에서는 어느 쪽인지 고르지 않고 **양쪽을 다 걸어** 보여준다.

    그 결과 나오는 기록은 "무엇을 했는가"가 아니라 **"무엇을 하기로 되어 있는가"** 다.
    trace.json에 `mode: contract`로 표시되고, 목업 화면 맨 위에 그 사실이 뜬다.
    실제 숫자가 필요하면 팩에 run.py를 만들어 `mode: run` 기록을 남겨야 한다.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_contract import parse_contract          # noqa: E402
from trace import Trace                            # noqa: E402


def parse_skill(p):
    text = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, ""
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def load_skills(pack):
    out = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        meta, body = parse_skill(p)
        if meta and "name" in meta:
            out[meta["name"]] = (meta, body)
    return out


def rule_of(body):
    """스킬 본문의 판단기준 첫 줄 — 이 단계가 무엇을 하기로 되어 있는지."""
    m = re.search(r"^## 판단기준.*?\n(.*?)(?=\n##|\Z)", body, re.S | re.M)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        s = line.strip().lstrip("-").strip()
        if s and not s.startswith("("):
            return s
    return ""


def nexts_of(meta):
    v = meta.get("next", "")
    if not v or v == "null":
        return []
    return [x.strip() for x in re.split(r"[|,]", v) if x.strip() and x.strip() != "null"]


def main(pack_dir, takes=None, max_loops=1):
    pack = Path(pack_dir)
    takes = takes or {}
    sk = load_skills(pack)
    if not sk:
        print(f"❌ {pack}: 스킬을 찾지 못했습니다")
        return 2

    cf = pack / "CONTRACT.md"
    contract = parse_contract(cf) if cf.is_file() else None
    if contract is None:
        print(f"❌ {pack}/CONTRACT.md 의 ```contract 블록이 없습니다 — 걸을 흐름이 없습니다.")
        print("   python3 check/check_contract.py <팩> 이 채울 서식을 알려줍니다.")
        return 2

    halt_at = {x.strip() for x in re.split(r"[,;]", contract.get("halt_at") or "")
               if x.strip() and not x.strip().startswith("(")}
    # 계약의 chain에 나오는 이름과 스킬 이름이 어긋나면 여기서 멈춘다 — 조용히 넘어가지 않는다.
    named = {n for path in contract["chain"] for n in path}
    unknown = sorted(named - set(sk))
    if unknown:
        print(f"❌ 계약의 chain이 없는 스킬을 가리킵니다: {unknown}")
        return 2

    tgt = {t for m, _ in sk.values() for t in nexts_of(m)}
    starts = [n for n in sk if n not in tgt]
    if len(starts) != 1:
        print(f"❌ 시작 스킬이 {len(starts)}개입니다 {starts} — 하나여야 걸을 수 있습니다.")
        return 2

    plan = pack / "agent-plan.md"
    ptxt = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    g = lambda pat: (re.search(pat, ptxt, re.M) or [None, ""])[1].strip()
    # 기획서 제목에서 문서 꼬리표를 떼어 에이전트 이름만 남긴다.
    # "연간 성과평가 운영 팀 기획서 (워크플로우 변환 초안)" → "연간 성과평가 운영"
    title = (re.search(r"^#\s+(.+)$", ptxt, re.M) or [None, ""])[1].strip()
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title)
    title = re.sub(r"\s*팀?\s*기획서\s*$", "", title).strip()
    title = title or g(r"^- Lv5:\s*(.+)$") or pack.name

    src = (g(r"^> 출처:\s*\*\*(.+?)\*\*") or g(r"^> 출처:\s*(.+?)\s*·")
           or g(r"^> 상류:\s*(.+)$") or pack.name)
    TR = Trace(title, source=src,
               lv4=g(r"^- Lv4:\s*(.+)$"), lv5=g(r"^- Lv5:\s*(.+)$"))
    TR.d["mode"] = "contract"      # 실행이 아니라 계약을 걸은 기록이다

    tables = [t for t in contract["tables"] if not t.startswith("(")]
    for t in tables[:4]:
        TR.input(t, None, "계약이 선언한 표 — 값은 읽지 않았습니다")
    if not tables:
        TR.input("(표 미정)", None, "계약에 표 이름이 아직 없습니다")

    # ── 흐름 걷기 ────────────────────────────────────────────────────────
    seen_loops, n, visits = set(), 0, {}
    order = []

    def walk(name, depth=0):
        nonlocal n
        if depth > 40 or name not in sk:
            return
        visits[name] = visits.get(name, 0) + 1
        meta, body = sk[name]
        n += 1
        label = f"{n}. {name}"
        order.append(name)
        human = meta.get("human", "")
        rule = rule_of(body)
        note = rule or "(판단기준이 아직 (미정)입니다 — 와이어프레임에서 채웁니다)"
        nx = nexts_of(meta)
        loop_to = (meta.get("loop_to") or "").strip()

        stops = human == "사람고유" or name in halt_at
        if len(nx) > 1:
            when = (meta.get("when") or "").strip()
            TR.fork(label, human,
                    [(c, t, None) for c, t in branch_labels(when, nx)],
                    note=note,
                    taken=takes.get(name))
            if when:
                TR.warn(f"갈림길 조건: {when}")
            else:
                TR.warn("갈림길 조건(when)이 비어 있습니다 — 원본 흐름도의 ◆ 문장을 옮겨 적으십시오.")
        elif stops:
            TR.halt(label, human or "사람고유", note,
                    actions=["확인함", "반려"] if human == "사람고유" else None)
            TR.warn("여기서 멈춥니다. 사람이 확인해야 다음으로 갑니다.")
        else:
            TR.step(label, human or "(미정)", note)

        for w in meta.get("writes", "[]").strip("[]").split(","):
            if w.strip():
                TR.file(w.strip())

        if loop_to and loop_to in sk:
            key = (name, loop_to)
            if key not in seen_loops and visits.get(loop_to, 0) < max_loops + 1:
                seen_loops.add(key)
                TR.loop(name, loop_to, exit_cond=(meta.get("loop_exit") or "").strip())
                walk(loop_to, depth + 1)
            elif key in seen_loops:
                TR.warn(f"↩ {loop_to}로 되돌아갑니다 — 조건이 찰 때까지 반복합니다.")

        chosen = [takes[name]] if name in takes and takes[name] in nx else nx
        for t in chosen:
            if visits.get(t, 0) <= max_loops:
                walk(t, depth + 1)

    walk(starts[0])

    forks = sum(1 for m, _ in sk.values() if len(nexts_of(m)) > 1)
    loops = sum(1 for m, _ in sk.values() if (m.get("loop_to") or "").strip())
    TR.done(f"계약이 선언한 흐름을 걸었습니다 — 스킬 {len(sk)}개 · 갈림길 {forks}곳 · "
            f"루프백 {loops}곳 · 정지 {len(halt_at)}곳. "
            f"**숫자는 없습니다 — 데이터를 읽지 않았습니다.**")
    p = TR.save(pack / "out")

    print(f"계약 흐름 기록: {p}")
    print(f"  스킬 {len(sk)}개 · 걸은 단계 {n}개 · 갈림길 {forks}곳 · 루프백 {loops}곳 · "
          f"정지 {len(halt_at)}곳")
    if takes:
        print(f"  고른 갈래: {', '.join(f'{k}→{v}' for k, v in takes.items())}")
    else:
        print("  갈래를 고르지 않아 **모든 경로를 다 걸었습니다** "
              "(--take 스킬=대상 으로 하나만 고를 수 있습니다)")
    print("  ⚠️ 이것은 실행 기록이 아닙니다. 판단기준을 계산하지 않았고 데이터를 읽지 않았습니다.")
    print(f"  다음: python3 check/make_mockup.py {pack}")
    return 0


def branch_labels(when, nx):
    """when 문장에서 각 갈래의 조건을 뽑는다. 못 뽑으면 '→ 대상'만 쓴다."""
    out = []
    for t in nx:
        cond = ""
        for part in re.split(r"[;·]", when or ""):
            if t in part:
                cond = re.sub(r"\s*->.*$", "", part).strip()
                break
        out.append((cond or f"→ {t}", t))
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    pack, takes, loops = args[0], {}, 1
    i = 1
    while i < len(args):
        if args[i] == "--take" and i + 1 < len(args):
            k, _, v = args[i + 1].partition("=")
            takes[k.strip()] = v.strip()
            i += 2
        elif args[i] == "--loops" and i + 1 < len(args):
            loops = int(args[i + 1]); i += 2
        else:
            i += 1
    sys.exit(main(pack, takes, loops))
