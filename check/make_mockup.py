#!/usr/bin/env python3
"""에이전트 실행 화면 목업 생성기 — 손으로 쓰던 것을 실행 결과에서 만든다.

사용: python3 check/make_mockup.py <팩 경로>   → <팩>/agent-mockup.html

읽는 것:
  · <팩>/out/trace.json   — run.py가 남긴 실행 기록. 실행 구간의 **모든 숫자가 여기서 온다.**
  · <팩>/skills/*/*/SKILL.md — 계층·순서·Human 여부·갈림길·루프백
  · <팩>/agent-plan.md    — Lv4/Lv5 이름, 한 줄 소개, 하는 일/하지 않는 일
  · DESIGN.md             — 색 토큰. 목업이 팔레트를 따로 갖지 않게 한다 (SSOT)

만드는 것은 한 장이고 두 부분이다:
  앞 — 요약·설계도 (이름 / 한 줄 / Lv4›Lv5›Lv6 계층 / 실행 흐름 / 스킬 카드 / 폴더 트리)
  뒤 — 실행 (▶ 누르면 한 단계씩. 사람고유 지점에서 멈춘다)

trace.json이 없으면 만들지 않는다. 실행하지 않은 화면은 지어낸 화면이다.
페이지 끝에 `#agent-data` JSON을 심어 둔다 — 다시 만들거나 다른 도구가 읽을 때 쓰는 SSOT다.
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trace import load as load_trace   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# DESIGN.md에 없지만 목업에만 필요한 것 — 없으면 여기 기본값을 쓴다.
FALLBACK = {"loop": "#5B4FCF", "warn": "#B26A00"}
HUMAN_CLS = {"자동": "auto", "증강": "aug", "사람고유": "human"}


def e(s):
    return html.escape(str(s), quote=True)


def rich(s):
    """기록에 적힌 **굵게**·`코드`를 화면에서도 굵게·코드로. 그 밖의 태그는 막는다."""
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


# 식별자를 담는 칸. 여기 숫자는 수량이 아니므로 자릿수를 끊지 않는다.
ID_COL = re.compile(r"코드|번호|ID|no\.?$", re.I)


def money(s, col=""):
    """표의 정수 칸에 천 단위 쉼표. 화면에서만 — 원본 파일은 그대로 둔다.

    계정코드·분개번호처럼 **식별자인 칸은 건드리지 않는다.** 1010을 1,010으로 쓰면
    금액처럼 보인다 (브라우저에서 실제로 그렇게 나왔다).
    """
    if ID_COL.search(col or ""):
        return s
    if re.fullmatch(r"-?\d{4,}", s):
        return f"{int(s):,}"
    return s


def tokens():
    """DESIGN.md의 토큰 표에서 색을 읽는다 — 목업이 팔레트를 복제하지 않도록."""
    md = ROOT / "DESIGN.md"
    t = {}
    if md.is_file():
        for name, val in re.findall(r"`--([a-z-]+)`\s*\|\s*`(#[0-9A-Fa-f]{3,8})`",
                                    md.read_text(encoding="utf-8")):
            t[name] = val
    for k, v in FALLBACK.items():
        t.setdefault(k, v)
    return t


def plan_facts(pack):
    """agent-plan.md에서 이름·한 줄 소개·하는 일/안 하는 일을 읽는다. 없으면 빈 값."""
    f = pack / "agent-plan.md"
    txt = f.read_text(encoding="utf-8") if f.is_file() else ""
    g = lambda pat: (re.search(pat, txt, re.M) or [None, ""])[1].strip()
    one = g(r"^- 한 문장:\s*(.+)$")
    if one:                                   # 여러 줄로 이어진 한 문장을 잇는다
        m = re.search(r"^- 한 문장:\s*(.+(?:\n  +\S.*)*)$", txt, re.M)
        one = re.sub(r"\s*\n\s+", " ", m.group(1)).strip() if m else one
    return {"one": one,
            "does": g(r"^- 하는 일:\s*(.+)$"),
            "not": g(r"^- 하지 않는 일:\s*(.+)$"),
            "lv4": g(r"^- Lv4:\s*(.+)$"),
            "lv5": g(r"^- Lv5:\s*(.+)$")}


def order_of(sk):
    """위상 정렬된 스킬 이름 순서 — 구조도·흐름도·레일이 같은 순서를 쓴다."""
    nx = {n: [x.strip() for x in re.split(r"[|,]", m.get("next", "")) if x.strip()
              and x.strip() != "null"] for n, m in sk.items()}
    indeg = {n: 0 for n in sk}
    for v in nx.values():
        for x in v:
            if x in indeg:
                indeg[x] += 1
    q, out = [n for n in sk if indeg[n] == 0], []
    while q:
        n = q.pop(0); out.append(n)
        for m_ in nx.get(n, []):
            if m_ in indeg:
                indeg[m_] -= 1
                if indeg[m_] == 0:
                    q.append(m_)
    out += [n for n in sk if n not in out]
    return out, nx


def skills(pack):
    out = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        m = re.match(r"^---\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        if "name" in meta:
            out[meta["name"]] = meta
    return out


def rail(sk, tr):
    """상단 진행 레일 — 흐름 순서대로. 갈림길·사람고유·루프백을 색으로 구분."""
    nexts = {n: [x.strip() for x in re.split(r"[|,]", m.get("next", "")) if x.strip()
                 and x.strip() != "null"] for n, m in sk.items()}
    # 위상 정렬. 깊이 우선으로 걸으면 갈래가 만나는 지점이 형제 갈래보다 앞에 와서
    # 레일이 실제 순서와 어긋난다 (실측). 들어오는 화살표가 다 처리된 뒤에 놓는다.
    indeg = {n: 0 for n in sk}
    for v in nexts.values():
        for x in v:
            if x in indeg:
                indeg[x] += 1
    queue = [n for n in sk if indeg[n] == 0]
    order = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m_ in nexts.get(n, []):
            if m_ in indeg:
                indeg[m_] -= 1
                if indeg[m_] == 0:
                    queue.append(m_)
    for n in sk:          # 순환에 갇힌 것도 빠뜨리지 않는다
        if n not in order:
            order.append(n)

    cycles = {l["from"]: l.get("cycles") for l in tr.get("loops", [])}
    out = []
    for i, n in enumerate(order):
        cls, extra = "done", ""
        if len(nexts.get(n, [])) > 1:
            cls, extra = "fork", "◆ "
        if sk[n].get("loop_to"):
            cls, extra = "loop", "↩ "
        if sk[n].get("human") == "사람고유" and not sk[n].get("loop_to"):
            cls, extra = "halt", "⛔ "
        c = cycles.get(n)
        times = ""
        for l in tr.get("loops", []):
            if l["to"] == n and l.get("cycles"):
                times = f" ×{l['cycles']}"
        out.append(f'<span class="n {cls}" data-skill="{e(n)}">'
                   f'<i class="dot"></i>{extra}{e(n)}{times}</span>')
        if i < len(order) - 1:
            out.append('<span class="arrow">›</span>')
    # 원본 흐름도(디자인캠프)의 ● 시작 / ■ 종료 표기를 그대로 쓴다.
    return ('<span class="cap start" id="cap-start">● 시작</span>'
            '<span class="arrow">›</span>\n  ' + "\n  ".join(out)
            + '\n  <span class="arrow">›</span>'
              '<span class="cap end" id="cap-end">■ 종료</span>')


# Human 여부별 색 — 우리 팩이 실제로 가진 값이다. 환경 태그(MCP·조회 등)는 이 단계에
# 없으므로 그것으로 칠하지 않는다. 없는 정보로 칠하면 그림이 거짓말을 한다.
LANES = [("자동", "auto"), ("증강", "aug"), ("사람고유", "human")]
LANE_FILL = {"자동": ("#F1F8F3", "ok"), "증강": ("#FFF6F0", "brand-sub"),
             "사람고유": ("#FDF2F4", "brand")}


def hierarchy_svg(sk, facts, tk):
    """Lv4 › Lv5 › Lv6 계층. 이 도구가 무엇을 어느 층에서 묶는지가 한눈에 보여야 한다."""
    order, _ = order_of(sk)
    n = len(order)
    CW, GAP = 150, 12
    total = n * CW + (n - 1) * GAP
    # 카드가 많으면 폭을 늘린다. 고정 폭이면 마지막 카드가 잘린다 (화면에서 실제로 잘렸다).
    W = max(980, total + 28)
    x0 = max(14, (W - total) / 2)
    H = 300
    o = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"'
         f' aria-label="Lv4 Lv5 Lv6 계층 구조도">']
    # Lv4 밴드
    o.append(f'<rect x="14" y="10" width="{W-28}" height="46" rx="10" '
             f'fill="{tk["bg-soft"]}" stroke="{tk["line"]}"/>')
    o.append(f'<text x="30" y="30" font-size="10.5" font-weight="700" '
             f'fill="{tk["muted"]}">Lv4 · 핵심 업무</text>')
    o.append(f'<text x="30" y="47" font-size="14" font-weight="700" '
             f'fill="{tk["text"]}">{e(facts["lv4"] or "(미정)")}</text>')
    # Lv5 박스 — 이번에 만드는 것
    bw = min(560, W - 120)
    bx = (W - bw) / 2
    o.append(f'<rect x="{bx}" y="72" width="{bw}" height="62" rx="12" fill="{tk["text"]}"/>')
    o.append(f'<text x="{bx+16}" y="92" font-size="10.5" font-weight="700" '
             f'fill="{tk["brand-sub"]}">Lv5 · 워크플로우 — 이 에이전트가 묶는 단위</text>')
    o.append(f'<text x="{W/2}" y="118" text-anchor="middle" font-size="16" font-weight="800" '
             f'fill="#fff">{e(facts["lv5"] or "(미정)")}</text>')
    # 연결선
    for i, name in enumerate(order):
        cx = x0 + i * (CW + GAP) + CW / 2
        o.append(f'<path d="M{W/2} 134 L{W/2} 150 L{cx} 150 L{cx} 168" '
                 f'stroke="{tk["line"]}" stroke-width="1.6" fill="none"/>')
    # Lv6 카드
    for i, name in enumerate(order):
        m = sk[name]
        hv = m.get("human", "")
        fill, tok = LANE_FILL.get(hv, (tk["bg-soft"], "line"))
        stroke = tk.get(tok, tk["line"])
        x = x0 + i * (CW + GAP)
        o.append(f'<rect x="{x}" y="168" width="{CW}" height="104" rx="10" '
                 f'fill="{tk["bg"]}" stroke="{stroke}" stroke-width="1.8"/>')
        o.append(f'<path d="M{x} 178 a10 10 0 0 1 10 -10 h{CW-20} a10 10 0 0 1 10 10 v16 h-{CW} z" '
                 f'fill="{fill}"/>')
        o.append(f'<text x="{x+11}" y="188" font-size="10" font-weight="700" '
                 f'fill="{stroke}">Lv6 · {e(hv or "(미정)")}</text>')
        label = name if len(name) <= 9 else name[:9] + "…"
        o.append(f'<text x="{x+11}" y="217" font-size="12.5" font-weight="700" '
                 f'fill="{tk["text"]}">{e(label)}</text>')
        o.append(f'<text x="{x+11}" y="236" font-size="10.5" '
                 f'fill="{tk["muted"]}">Skill화 {e(m.get("skillability", "(미정)"))}</text>')
        own = m.get("owner", "")
        if own:
            o.append(f'<text x="{x+11}" y="254" font-size="10.5" font-weight="700" '
                     f'fill="{tk["muted"]}">👤 {e(own)}</text>')
        if m.get("loop_to"):
            o.append(f'<text x="{x+CW-13}" y="188" text-anchor="end" font-size="10" '
                     f'font-weight="700" fill="{tk["loop"]}">↩</text>')
        nxs = [z for z in re.split(r"[|,]", m.get("next", "")) if z.strip() and z.strip() != "null"]
        if len(nxs) > 1:
            o.append(f'<text x="{x+CW-13}" y="188" text-anchor="end" font-size="10" '
                     f'font-weight="700" fill="{tk["brand-sub"]}">◆</text>')
    o.append(f'<text x="{W/2}" y="290" text-anchor="middle" font-size="10.5" '
             f'fill="{tk["muted"]}">한 사람이 만든 Lv6 스킬 하나가 카드 하나 · '
             f'테두리 색 = Human 여부 · ◆ 갈림길 · ↩ 루프백</text>')
    o.append("</svg>")
    return "\n".join(o)


def flow_svg(sk, tr, tk):
    """실행 흐름 설계도 — Human 여부 레인. 갈림길과 루프백이 눈에 보여야 한다."""
    order, nx = order_of(sk)
    lanes = [l for l, _ in LANES if any(sk[n].get("human") == l for n in order)]
    LY, LH = 44, 76
    # 7~8노드가 한 화면에 들어가도록 조인다. 넘치면 .lane-scroll이 받아준다.
    CW, GAP = 118, 30
    x0 = 92
    W = max(1040, x0 + len(order) * (CW + GAP) + 70)
    H = LY + len(lanes) * LH + 54
    y_of = {l: LY + i * LH for i, l in enumerate(lanes)}
    pos = {}
    for i, n in enumerate(order):
        pos[n] = (x0 + i * (CW + GAP), y_of.get(sk[n].get("human"), LY) + 16)

    o = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"'
         f' aria-label="실행 흐름 설계도">']
    for l in lanes:
        fill, tok = LANE_FILL[l]
        y = y_of[l]
        o.append(f'<rect x="0" y="{y}" width="{W}" height="{LH-10}" rx="8" fill="{fill}"/>')
        o.append(f'<text x="12" y="{y+38}" font-size="11" font-weight="700" '
                 f'fill="{tk[tok]}">{e(l)}</text>')
    # 시작·종료
    fx, fy = pos[order[0]]
    o.append(f'<text x="{fx}" y="{fy-7}" font-size="10.5" font-weight="700" '
             f'fill="{tk["text"]}">● 시작</text>')
    ends = [n for n in order if not nx.get(n)]
    if ends:
        ex, ey = pos[ends[-1]]
        o.append(f'<text x="{ex+CW}" y="{ey-7}" text-anchor="end" font-size="10.5" '
                 f'font-weight="700" fill="{tk["text"]}">■ 종료</text>')
    # 화살표 정의
    o.append(f'<defs><marker id="a" markerWidth="7" markerHeight="7" refX="6" refY="3.5" '
             f'orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="{tk["line"]}"/></marker>'
             f'<marker id="al" markerWidth="7" markerHeight="7" refX="6" refY="3.5" '
             f'orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="{tk["loop"]}"/></marker></defs>')
    # 앞으로 가는 화살표
    for n in order:
        ax, ay = pos[n]
        for m_ in nx.get(n, []):
            if m_ not in pos:
                continue
            bx, by = pos[m_]
            mid = ax + CW + GAP / 2
            o.append(f'<path d="M{ax+CW} {ay+22} H{mid} V{by+22} H{bx}" fill="none" '
                     f'stroke="{tk["line"]}" stroke-width="1.6" marker-end="url(#a)"/>')
    # 루프백
    for n in order:
        dst = (sk[n].get("loop_to") or "").strip()
        if dst and dst in pos:
            ax, ay = pos[n]; bx, by = pos[dst]
            top = min(ay, by) - 20
            o.append(f'<path d="M{ax+CW/2} {ay} V{top} H{bx+CW/2} V{by}" fill="none" '
                     f'stroke="{tk["loop"]}" stroke-width="1.6" stroke-dasharray="5 4" '
                     f'marker-end="url(#al)"/>')
            lab = (sk[n].get("loop_exit") or "재작업")
            lab = lab if len(lab) <= 20 else lab[:20] + "…"
            lx = min(max((ax + bx) / 2 + CW / 2, 90), W - 90)
            o.append(f'<text x="{lx}" y="{top-6}" text-anchor="middle" '
                     f'font-size="10" font-weight="700" fill="{tk["loop"]}">↩ {e(lab)}</text>')
    # 노드
    for i, n in enumerate(order):
        x, y = pos[n]
        m = sk[n]
        _, tok = LANE_FILL.get(m.get("human"), (None, "line"))
        stroke = tk.get(tok, tk["line"])
        forked = len([z for z in re.split(r"[|,]", m.get("next", ""))
                      if z.strip() and z.strip() != "null"]) > 1
        o.append(f'<rect x="{x}" y="{y}" width="{CW}" height="44" rx="8" fill="{tk["bg"]}" '
                 f'stroke="{stroke}" stroke-width="{2.4 if m.get("human")=="사람고유" else 1.6}"/>')
        head = f'{i+1}. ' + (n if len(n) <= 7 else n[:7] + "…")
        o.append(f'<text x="{x+CW/2}" y="{y+20}" text-anchor="middle" font-size="11.5" '
                 f'font-weight="700" fill="{tk["text"]}">{e(head)}</text>')
        sub = "◆ 갈림길" if forked else ("⛔ 멈춤" if m.get("human") == "사람고유" else
                                       e(m.get("skillability", "")))
        o.append(f'<text x="{x+CW/2}" y="{y+35}" text-anchor="middle" font-size="10" '
                 f'fill="{tk["muted"]}">{sub}</text>')
    # 갈림길 조건
    for n in order:
        w = (sk[n].get("when") or "").strip()
        if w and len(nx.get(n, [])) > 1:
            x, y = pos[n]
            cx = min(max(x + CW / 2, 200), W - 200)
            o.append(f'<text x="{cx}" y="{H-28}" text-anchor="middle" font-size="10" '
                     f'fill="{tk["brand-sub"]}">◆ {e(w[:60])}</text>')
    o.append("</svg>")
    return "\n".join(o)


def table_html(t):
    head = "".join(f"<th>{e(c)}</th>" for c in t["cols"])
    body = []
    for r in t["rows"]:
        cls = f' class="{r["mark"]}"' if r.get("mark") else ""
        tds = "".join(
            (f'<td class="num">{e(money(c, col))}</td>' if re.fullmatch(r"-?[\d,]+", c)
             else f"<td>{e(c)}</td>")
            for c, col in zip(r["cells"], t["cols"]))
        body.append(f"<tr{cls}>{tds}</tr>")
    return (f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def step_html(s, sk, idx):
    if s["kind"] == "loopback":
        return (f'<div class="st loopback" data-i="{idx}" data-kind="loopback" '
                f'data-skill="{e(s["to"])}">↩ {e(s["to"])}로 되돌아감'
                f'{" &nbsp;·&nbsp; 탈출 조건: " + e(s["exit"]) if s.get("exit") else ""}</div>')

    hc = HUMAN_CLS.get(s.get("human"), "")
    tags = [f'<span class="tag {hc}">{e(s["human"])}</span>'] if s.get("human") else []
    if s["kind"] == "fork":
        tags.append('<span class="tag fork">◆ 갈림길</span>')
    if s["kind"] == "halt":
        tags.append('<span class="tag human">멈춤</span>')
    if s.get("cycle"):
        tags.insert(0, f'<span class="cycle">{s["cycle"]}회차</span>')

    body = [f"<p>{rich(s['note'])}</p>"] if s.get("note") else []
    for w in s.get("warns", []):
        body.append(f'<div class="warn">⚠️ {rich(w)}</div>')

    if s["kind"] == "fork":
        cards = []
        for b in s["branches"]:
            # 어느 갈래로 갔는지는 taken이 말한다 — 건수 0을 "안 갔다"로 읽지 않는다.
            taken = ' taken' if b.get("to") == s.get("taken") else ""
            cnt = (f'<div class="cnt">{b["count"]}<span>건</span></div>'
                   if b.get("count") is not None else '<div class="cnt none">—</div>')
            cards.append(f'<div class="br{taken}"><div class="cond">{e(b["cond"])}</div>'
                         f'<div class="to">→ {e(b["to"])}</div>{cnt}</div>')
        body.append(f'<div class="branches">{"".join(cards)}</div>')

    for t in s.get("tables", []):
        body.append(table_html(t))

    if s["kind"] == "halt":
        if s.get("checklist"):
            items = "".join(f"<li>☐ {rich(c)}</li>" for c in s["checklist"])
            body.append(f'<ul class="chk">{items}</ul>')
        if s.get("actions"):
            btns = "".join(
                "<button{}>{}</button>".format(' class="primary"' if i == 0 else "", e(a))
                for i, a in enumerate(s["actions"]))
            body.append(f'<div class="actions">{btns}</div>')
            body.append('<p class="disabled-note">※ 목업입니다. 이 팩에는 실행 코드가 없습니다 — '
                        '버튼은 동작하지 않습니다.</p>')

    for f in s.get("files", []):
        cnt = f' <b>{f["count"]}건</b>' if f.get("count") is not None else ""
        body.append(f'<div class="files"><span class="file">→ {e(f["path"])}{cnt}</span></div>')

    cls = {"fork": " fork-card", "halt": " halt"}.get(s["kind"], "")
    # 재생 중 이 단계가 사람을 기다린다는 것을 화면이 직접 말한다.
    if s["kind"] == "halt":
        body.append('<div class="waitbar">⏸ <b>사람 확인 대기</b> — '
                    '확인해야 다음으로 넘어갑니다.'
                    '<button class="go" type="button">확인하고 계속 ▶</button></div>')
    bare = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s.get("note", ""))).strip()
    return (f'<div class="st card{cls}" data-i="{idx}" data-kind="{s["kind"]}" '
            f'data-skill="{e(s["skill"])}" data-label="{e(bare[:60])}">'
            f'<header><b>{e(s["skill"])}</b>{"".join(tags)}'
            f'<span class="ms" data-ms=""></span></header>'
            f'<div class="run"><i class="spin"></i>처리 중…</div>'
            f'<div class="body">{"".join(body)}</div></div>')


def skill_cards(sk):
    order, nx = order_of(sk)
    out = []
    for i, n in enumerate(order):
        m = sk[n]
        hv = m.get("human", "(미정)")
        cls = HUMAN_CLS.get(hv, "")
        ins = m.get("inputs", "[]").strip("[]")
        outs = m.get("outputs", "[]").strip("[]")
        rule = (m.get("when") or m.get("loop_exit") or "").strip()
        rk = "갈림길" if m.get("when") else ("루프 탈출" if m.get("loop_exit") else "")
        reads = m.get("reads", "[]").strip("[]")
        writes = m.get("writes", "[]").strip("[]")
        own = m.get("owner", "")
        out.append(
            f'<div class="skill">'
            + (f'<span class="owner">👤 {e(own)}</span>' if own else "")
            + f'<span class="tag {cls}">Lv6 · {e(hv)}</span>'
            f'<div class="sname">{i+1}. {e(n)}</div>'
            f'<div class="io"><b>입력</b> {e(ins or "—")} → <b>출력</b> {e(outs or "—")}</div>'
            + (f'<div class="io"><b>읽기</b> {e(reads)}</div>' if reads else "")
            + (f'<div class="io"><b>쓰기</b> {e(writes)}</div>' if writes else "")
            + (f'<div class="rule"><span class="k">{rk}</span>{e(rule)}</div>' if rule else "")
            + '</div>')
    return "".join(out)


def folder_tree(pack, sk):
    order, _ = order_of(sk)
    lines = [f"{pack.name}/",
             "├─ README.md          처음 보는 사람을 위한 사용 안내",
             "├─ agent-plan.md      팀 목적과 실행 흐름의 원본 (SSOT)",
             "├─ AGENTS.md          역할 · 하는 일 · 하지 않는 일",
             "├─ CONTRACT.md        표·기록자·순서·정지 지점의 합의",
             "│", "├─ skills/depth/"]
    for i, n in enumerate(order):
        tip = "└─" if i == len(order) - 1 else "├─"
        hv = sk[n].get("human", "")
        lines.append(f"│   {tip} {n}/    SKILL.md · {hv}")
    lines += ["│", "├─ data/              사람이 넣는 원본",
              "└─ out/               에이전트가 만드는 결과 (run.py 실행 시)"]
    return e("\n".join(lines))


def css(tk):
    root = " ".join(f"--{k}:{v};" for k, v in tk.items())
    return f"""
  :root {{ {root} }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg-soft);color:var(--text);
       font:15px/1.6 -apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}}
  .app{{max-width:1120px;margin:0 auto;background:var(--bg);min-height:100vh;
       border-left:1px solid var(--line);border-right:1px solid var(--line)}}
  .top{{display:flex;align-items:center;gap:12px;padding:14px 22px;
       border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}}
  .mark{{width:30px;height:30px;border-radius:8px;background:var(--brand);color:#fff;
        display:grid;place-items:center;font-size:14px;font-weight:700;flex:none}}
  .top h1{{font-size:15px;letter-spacing:-.01em}}
  .top .sub{{font-size:12px;color:var(--muted)}}
  .pill{{margin-left:auto;font-size:11px;border:1px solid var(--line);border-radius:999px;
        padding:3px 10px;color:var(--muted)}}
  .rail{{display:flex;gap:6px;padding:12px 22px;overflow-x:auto;align-items:center;
        border-bottom:1px solid var(--line);background:var(--bg-soft);
        position:sticky;top:59px;z-index:4}}
  .rail .n{{flex:none;font-size:12px;padding:5px 11px;border-radius:999px;white-space:nowrap;
           border:1px solid var(--line);background:var(--bg);color:var(--muted)}}
  .rail .n.done{{border-color:var(--ok);color:var(--ok)}}
  .rail .n.fork{{border-color:var(--brand-sub);color:var(--brand-sub);font-weight:600}}
  .rail .n.halt{{border-color:var(--brand);color:var(--brand);font-weight:600}}
  .rail .n.loop{{border-color:var(--loop);color:var(--loop);font-weight:600}}
  .rail .arrow{{flex:none;color:var(--line);font-size:12px}}
  main{{padding:20px 22px 60px}}
  .log{{display:flex;flex-direction:column;gap:14px}}
  .card{{border:1px solid var(--line);border-radius:10px;overflow:hidden}}
  .card>header{{display:flex;align-items:center;gap:9px;padding:10px 14px;font-size:13px;
                background:var(--bg-soft);border-bottom:1px solid var(--line)}}
  .card.fork-card{{border-color:var(--brand-sub)}}
  .card.halt{{border-color:var(--brand)}}
  .card.halt>header{{background:#FDF2F4;border-color:var(--brand);color:var(--brand)}}
  .tag{{font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);
       color:var(--muted)}}
  .tag.auto{{border-color:var(--ok);color:var(--ok)}}
  .tag.aug{{border-color:var(--brand-sub);color:var(--brand-sub)}}
  .tag.human{{border-color:var(--brand);color:var(--brand)}}
  .tag.fork{{border-color:var(--brand-sub);color:var(--brand-sub)}}
  .cycle{{font-size:11px;border:1px solid var(--loop);color:var(--loop);border-radius:999px;
         padding:1px 8px;font-weight:600}}
  .body{{padding:13px 14px;font-size:14px}}
  .body p+p{{margin-top:6px}}
  .files{{margin-top:9px;display:flex;gap:6px;flex-wrap:wrap}}
  .file{{font-size:12px;border:1px solid var(--line);border-radius:6px;padding:3px 9px;
        color:var(--muted)}}
  .file b{{color:var(--text);font-weight:600}}
  .warn{{background:#FFF6F0;border:1px solid var(--brand-sub);border-radius:8px;
        padding:10px 12px;font-size:13px;margin-top:10px}}
  .branches{{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));
            gap:10px;margin-top:11px}}
  .br{{border:1px solid var(--line);border-radius:8px;padding:11px 12px}}
  .br.taken{{border-color:var(--brand-sub);background:#FFF9F5}}
  .br .cond{{font-size:11px;color:var(--brand-sub);font-weight:600;margin-bottom:3px}}
  .br .to{{font-size:13px;font-weight:600}}
  .br .cnt{{font-size:22px;font-weight:700;letter-spacing:-.02em;margin-top:5px}}
  .br .cnt.none{{color:var(--muted);font-weight:400}}
  .br .cnt span{{font-size:12px;font-weight:400;color:var(--muted);margin-left:3px}}
  .loopback{{text-align:center;font-size:12px;color:var(--loop);padding:7px;font-weight:600;
            border:1px dashed var(--loop);border-radius:8px;background:#F8F7FE}}
  .scroll{{overflow-x:auto;margin-top:10px}}
  table{{width:100%;border-collapse:collapse;font-size:13px;min-width:520px}}
  th{{text-align:left;font-size:11px;color:var(--muted);font-weight:600;padding:6px 9px;
     border-bottom:1px solid var(--line);white-space:nowrap}}
  td{{padding:6px 9px;border-bottom:1px solid var(--line);white-space:nowrap}}
  td.num{{text-align:right;font-variant-numeric:tabular-nums}}
  tr.diff td{{background:#FFF6F0}}
  tr.na td{{color:var(--muted)}}
  tbody tr:last-child td{{border-bottom:none}}
  .chk{{list-style:none;margin-top:10px;font-size:13px}}
  .chk li{{padding:5px 0;border-bottom:1px solid var(--line)}}
  .chk li:last-child{{border-bottom:none}}
  .actions{{display:flex;gap:8px;margin-top:13px;flex-wrap:wrap}}
  button{{font:inherit;font-size:13px;padding:8px 16px;border-radius:7px;cursor:not-allowed;
         border:1px solid var(--line);background:var(--bg);color:var(--muted)}}
  button.primary{{background:var(--brand);border-color:var(--brand);color:#fff}}
  .disabled-note{{font-size:12px;color:var(--muted);margin-top:7px}}
  /* 계약 흐름 기록임을 화면이 먼저 말한다 — 숫자가 없는 이유 */
  .modebar{{max-width:1120px;margin:0 auto;padding:12px 22px;font-size:13px;
           display:flex;gap:10px;align-items:flex-start;
           background:#F8F7FE;border-bottom:1px solid var(--loop);color:var(--loop)}}
  .modebar b{{color:var(--text)}}
  .modebar .ic{{font-size:15px;line-height:1.3}}

  /* ── 요약·설계도 (실행 앞단) ─────────────────────────────────────── */
  .hero{{background:var(--text);color:#fff;padding:44px 0 38px}}
  .hero .wrap{{max-width:1120px;margin:0 auto;padding:0 22px}}
  .hero .eyebrow{{font-size:11.5px;font-weight:700;letter-spacing:.12em;
                 color:rgba(255,255,255,.55);margin-bottom:14px}}
  .hero h1{{font-size:clamp(28px,5vw,44px);font-weight:800;letter-spacing:-.02em;
           line-height:1.15;margin-bottom:4px}}
  .hero h1 small{{font-size:.36em;font-weight:600;color:var(--brand-sub);margin-left:12px;
                 letter-spacing:0}}
  .hero .one{{font-size:clamp(14px,2vw,17px);color:rgba(255,255,255,.8);max-width:680px;
             margin-top:12px}}
  .hero .one b{{color:#fff}}
  .lvpath{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:20px;
          font-size:12px;color:rgba(255,255,255,.6)}}
  .lvpath .lv{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);
              border-radius:999px;padding:4px 12px}}
  .lvpath .lv b{{color:#fff}}
  .lvpath .lv.on{{background:var(--brand);border-color:var(--brand);color:#fff}}
  .stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:26px}}
  .stat{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
        border-radius:12px;padding:14px 16px}}
  .stat .n{{font-size:24px;font-weight:700;letter-spacing:-.01em;
           font-variant-numeric:tabular-nums}}
  .stat .n em{{font-style:normal;font-size:13px;color:rgba(255,255,255,.55);margin-left:2px}}
  .stat .l{{font-size:12px;color:rgba(255,255,255,.55);margin-top:2px}}
  @media(max-width:680px){{.stats{{grid-template-columns:repeat(2,1fr)}}}}

  .sec{{margin:0 0 30px}}
  .sec-head{{display:flex;align-items:baseline;gap:12px;margin-bottom:13px;flex-wrap:wrap}}
  .sec-head .no{{font-size:12px;font-weight:700;color:var(--brand);background:#FDF2F4;
                padding:3px 10px;border-radius:6px}}
  .sec-head h2{{font-size:18px;font-weight:800;letter-spacing:-.01em}}
  .sec-head .hint{{font-size:12.5px;color:var(--muted)}}
  .panel{{background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:20px}}
  .lane-scroll{{overflow-x:auto;padding-bottom:4px}}
  .legend{{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font-size:12px;
          color:var(--muted)}}
  .legend .item{{display:flex;align-items:center;gap:6px}}
  .legend .sw{{width:12px;height:12px;border-radius:3px;display:inline-block}}
  .skill-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
  @media(max-width:760px){{.skill-grid{{grid-template-columns:1fr}}}}
  .skill{{background:var(--bg);border:1px solid var(--line);border-radius:12px;
         padding:16px 18px;position:relative}}
  .skill .owner{{position:absolute;top:14px;right:16px;font-size:11.5px;font-weight:700;
                color:var(--muted);background:var(--bg-soft);padding:3px 9px;border-radius:999px}}
  .skill .sname{{font-size:14px;font-weight:700;margin:6px 0 6px}}
  .skill .io{{font-size:12.5px;color:var(--muted);margin-bottom:4px}}
  .skill .io b{{color:var(--text);font-weight:600}}
  .skill .rule{{font-size:12.5px;background:var(--bg-soft);border-left:3px solid var(--brand-sub);
               padding:7px 11px;border-radius:0 8px 8px 0;margin-top:8px}}
  .skill .rule .k{{font-weight:700;color:var(--brand-sub);margin-right:5px}}
  pre.tree{{font-family:ui-monospace,"SF Mono",Consolas,monospace;font-size:12px;
           background:#0F172A;color:#E2E8F0;padding:16px 18px;border-radius:10px;
           overflow-x:auto;line-height:1.75;margin:0}}
  .runhead{{border-top:2px solid var(--line);padding-top:26px;margin-top:6px}}

  .foot{{margin-top:26px;padding-top:16px;border-top:1px solid var(--line);
        font-size:12px;color:var(--muted);line-height:1.8}}
  .foot code{{background:var(--bg-soft);border:1px solid var(--line);border-radius:4px;
             padding:1px 5px}}

  /* ── 재생 ─────────────────────────────────────────────────────────── */
  body.play .st{{opacity:0;transform:translateY(6px);
                 transition:opacity .28s ease,transform .28s ease}}
  body.play .st.shown{{opacity:1;transform:none}}
  body.play .st:not(.shown){{pointer-events:none;height:0;margin:0;overflow:hidden;border:0}}
  .st.now{{box-shadow:0 0 0 3px color-mix(in srgb,var(--brand-sub) 28%,transparent)}}
  .rail .n{{opacity:.35;transition:opacity .2s ease}}
  body:not(.play) .rail .n,
  .rail .n.lit{{opacity:1}}
  .rail .n.now{{outline:2px solid var(--brand-sub);outline-offset:2px}}

  .waitbar{{display:none;align-items:center;gap:10px;flex-wrap:wrap;margin-top:11px;
           padding:10px 12px;border-radius:8px;font-size:13px;
           background:#FDF2F4;border:1px solid var(--brand);color:var(--brand)}}
  body.play .st.waiting .waitbar{{display:flex}}
  .waitbar .go{{margin-left:auto;cursor:pointer;background:var(--brand);color:#fff;
               border-color:var(--brand);font-size:12px;padding:6px 12px}}
  .st.waiting{{box-shadow:0 0 0 3px color-mix(in srgb,var(--brand) 22%,transparent)}}

  /* ── 하단 진행 바 ─────────────────────────────────────────────────── */
  .dock{{position:fixed;left:0;right:0;bottom:0;z-index:20;background:var(--bg);
        border-top:1px solid var(--line);box-shadow:0 -2px 12px rgba(0,0,0,.06)}}
  .dock .track{{height:4px;background:var(--bg-soft)}}
  .dock .fill{{height:100%;width:0;background:var(--brand);transition:width .3s ease}}
  .dock.waiting .fill{{background:var(--brand-sub)}}
  .dock.done .fill{{background:var(--ok)}}
  .dock .row{{max-width:1120px;margin:0 auto;display:flex;align-items:center;gap:10px;
             padding:9px 22px;flex-wrap:wrap}}
  .dock .pct{{font-size:16px;font-weight:700;letter-spacing:-.02em;
             font-variant-numeric:tabular-nums;min-width:52px}}
  .dock .what{{font-size:13px;color:var(--muted);flex:1;min-width:160px;
              overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .dock .what b{{color:var(--text)}}
  .dock button{{cursor:pointer;font-size:12px;padding:6px 12px}}
  .dock button:hover{{border-color:var(--brand);color:var(--brand)}}
  .dock button.primary:hover{{color:#fff;opacity:.9}}
  .dock .keys{{font-size:11px;color:var(--muted);width:100%}}
  main{{padding-bottom:120px}}
  /* 노드 상태 점 · 시작/종료 캡 */
  .rail .dot{{width:6px;height:6px;border-radius:50%;background:currentColor;opacity:.35;
             display:inline-block;margin-right:6px;vertical-align:1px}}
  .rail .n.lit .dot{{opacity:1}}
  .rail .n.now .dot{{animation:pulse 1s ease-in-out infinite}}
  @keyframes pulse{{50%{{opacity:.25}}}}
  .rail .cap{{flex:none;font-size:11px;color:var(--muted);opacity:.4;
             transition:opacity .2s ease,color .2s ease}}
  .rail .cap.on{{opacity:1;color:var(--text);font-weight:600}}
  body:not(.play) .rail .cap{{opacity:1}}
  body.play .rail .n{{cursor:pointer}}

  /* 처리 중 */
  .st .run{{display:none;align-items:center;gap:8px;padding:11px 14px;font-size:13px;
           color:var(--muted);border-bottom:1px solid var(--line);background:var(--bg-soft)}}
  .st.working .run{{display:flex}}
  .st.working .body{{display:none}}
  .spin{{width:12px;height:12px;border-radius:50%;border:2px solid var(--line);
        border-top-color:var(--brand-sub);animation:spin .7s linear infinite;flex:none}}
  @keyframes spin{{to{{transform:rotate(360deg)}}}}
  .st .ms{{margin-left:auto;font-size:11px;color:var(--muted);
          font-variant-numeric:tabular-nums;opacity:0;transition:opacity .2s ease}}
  .st .ms.on{{opacity:1}}
  .st.loopback.working{{opacity:.6}}

  .dock .clock{{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;
               border:1px solid var(--line);border-radius:6px;padding:5px 9px}}
  .dock .clock b{{color:var(--text)}}

  @media (prefers-reduced-motion:reduce){{
    body.play .st,.dock .fill{{transition:none}}
    .spin,.rail .n.now .dot{{animation:none}}
  }}
"""


def main(pack_dir):
    pack = Path(pack_dir)
    tr = load_trace(pack)
    if tr is None:
        print(f"❌ {pack}/out/trace.json 이 없습니다.")
        print("   먼저 run.py를 돌리십시오 — 실행하지 않은 화면은 지어낸 화면입니다.")
        return 2

    sk = skills(pack)
    facts = plan_facts(pack)
    tk = tokens()
    order, nxmap = order_of(sk)
    ai_n = sum(1 for n in order if sk[n].get("human") in ("자동", "증강"))
    hu_n = sum(1 for n in order if sk[n].get("human") == "사람고유")
    fork_n = sum(1 for n in order if len(nxmap.get(n, [])) > 1)
    kind = []
    if any(len(re.split(r"[|,]", m.get("next", ""))) > 1 for m in sk.values()
           if m.get("next") and m.get("next") != "null"):
        kind.append("갈림길")
    if tr.get("loops"):
        kind.append("루프백")
    verdict = f"팀 에이전트 · {'+'.join(kind)}" if kind else "팀 스킬팩"

    ins = " · ".join(
        (f"{e(i['name'])} <b>{i['count']}건</b>" if i.get("count") is not None
         else f"{e(i['name'])} <span style=\"color:var(--muted)\">(값 안 읽음)</span>")
        for i in tr["inputs"])
    input_card = (
        f'<div class="card"><header><b>입력</b>'
        f'<span class="tag">{e(tr["inputs"][0].get("note", "")) if tr["inputs"] else ""}</span>'
        f'</header><div class="body"><p>{ins}</p></div></div>') if tr["inputs"] else ""

    steps = "\n\n  ".join(step_html(s, sk, i) for i, s in enumerate(tr["steps"]))
    loops = " · ".join(f"{e(l['from'])} ↩ {e(l['to'])}"
                       + (f" ({l['cycles']}회차)" if l.get("cycles") else "")
                       for l in tr.get("loops", []))

    lv4, lv5 = facts["lv4"] or tr.get("lv4", ""), facts["lv5"] or tr.get("lv5", "")
    legend = "".join(
        f'<span class="item"><span class="sw" style="background:{LANE_FILL[l][0]};'
        f'border:1px solid {tk[LANE_FILL[l][1]]}"></span>{l}</span>'
        for l, _ in LANES if any(sk[n].get("human") == l for n in order))
    legend += (f'<span class="item"><span class="sw" style="border:1px dashed {tk["loop"]}">'
               f'</span>↩ 루프백</span>'
               f'<span class="item" style="color:{tk["brand-sub"]}">◆ 갈림길</span>')

    ssot = json.dumps({
        "schema": "agent-summary/v0.2",
        "source": tr.get("source", ""),
        "agent": {"name": tr["title"], "level": "Lv.5", "one_liner": facts["one"]},
        "levels": {"lv4": lv4, "lv5": lv5,
                   "lv6": [{"name": n, "human": sk[n].get("human", ""),
                            "owner": sk[n].get("owner", ""),
                            "skillability": sk[n].get("skillability", ""),
                            "next": nxmap.get(n, []),
                            "loop_to": sk[n].get("loop_to", "")} for n in order]},
        "stats": {"skills": len(order), "ai_tasks": ai_n, "human_points": hu_n,
                  "forks": fork_n, "loops": len(tr.get("loops", [])),
                  "steps": len([s for s in tr["steps"] if s["kind"] != "loopback"])},
        "verdict": verdict, "summary": tr.get("summary", ""),
    }, ensure_ascii=False, indent=1)

    contract_mode = tr.get("mode") == "contract"
    modebar = ("" if not contract_mode else
               '<div class="modebar"><span class="ic">🗺</span><div>'
               '<b>계약이 선언한 흐름을 걸어 본 화면입니다 — 실행 기록이 아닙니다.</b><br>'
               'CONTRACT.md와 SKILL.md에서 순서·갈림길·루프백·정지 지점만 읽었습니다. '
               '판단기준을 계산하지 않았고 데이터를 읽지 않았으므로 <b>건수·금액이 없습니다.</b> '
               '갈래는 고르지 않고 <b>양쪽을 다</b> 보여줍니다. '
               '실제 숫자가 필요하면 팩에 <code>run.py</code>를 만들어 다시 돌리십시오.'
               '</div></div>')

    summary = f'''{modebar}
<div class="hero">
  <div class="wrap">
    <div class="eyebrow">{e(tr.get("source", ""))}</div>
    <h1>{e(tr["title"])} <small>Lv.5 팀 에이전트</small></h1>
    <p class="one">{rich(facts["one"]) if facts["one"] else "(agent-plan.md §2에 한 문장이 아직 없습니다)"}</p>
    <div class="lvpath">
      <span class="lv">Lv4 핵심 업무 · <b>{e(lv4 or "(미정)")}</b></span> ›
      <span class="lv on">Lv5 워크플로우 · <b>{e(lv5 or "(미정)")}</b></span> ›
      <span class="lv">Lv6 태스크 <b>{len(order)}개</b> = 스킬 {len(order)}개</span>
    </div>
    <div class="stats">
      <div class="stat"><div class="n">{len(order)}<em>개</em></div>
        <div class="l">Lv6 스킬 · 1인 1스킬</div></div>
      <div class="stat"><div class="n">{ai_n}<em>개</em></div>
        <div class="l">AI 태스크 (자동+증강) · ATF③</div></div>
      <div class="stat"><div class="n">{hu_n}<em>곳</em></div>
        <div class="l">사람이 확인하는 자리</div></div>
      <div class="stat"><div class="n">{fork_n}<em>+</em>{len(tr.get("loops", []))}</div>
        <div class="l">갈림길 + 루프백 · ATF④</div></div>
    </div>
  </div>
</div>

<main class="wrap">

<section class="sec">
  <div class="sec-head"><span class="no">①</span>
    <h2>구조 — Lv4 › Lv5 › Lv6</h2>
    <span class="hint">이 Lv5 에이전트는 아래 Lv6 스킬들로 이루어집니다</span></div>
  <div class="panel"><div class="lane-scroll">{hierarchy_svg(sk, {"lv4": lv4, "lv5": lv5}, tk)}</div></div>
</section>

<section class="sec">
  <div class="sec-head"><span class="no">②</span>
    <h2>실행 흐름 설계도</h2>
    <span class="hint">아래 실행이 이 지도를 따라갑니다</span></div>
  <div class="panel">
    <div class="lane-scroll">{flow_svg(sk, tr, tk)}</div>
    <div class="legend">{legend}</div>
  </div>
</section>

<section class="sec">
  <div class="sec-head"><span class="no">③</span>
    <h2>Lv6 스킬 {len(order)}개 — 만든 사람과 판단 기준</h2></div>
  <div class="skill-grid">{skill_cards(sk)}</div>
</section>

<section class="sec">
  <div class="sec-head"><span class="no">④</span>
    <h2>폴더 트리</h2>
    <span class="hint">교육생이 받는 팩의 실제 모양</span></div>
  <div class="panel"><pre class="tree">{folder_tree(pack, sk)}</pre></div>
</section>

<section class="sec runhead">
  <div class="sec-head"><span class="no">⑤</span>
    <h2>실행 — 아래에서 직접 돌려 보십시오</h2>
    <span class="hint">▶ 실행 · 사람고유 지점에서 멈춥니다</span></div>
</section>
</main>
'''

    doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(tr['title'])} — 실행 화면</title>
<!-- 이 파일은 check/make_mockup.py 가 out/trace.json 에서 생성했습니다.
     손으로 고치지 마십시오 — run.py를 다시 돌리고 이 스크립트를 다시 실행하십시오.
     색 토큰의 SSOT는 DESIGN.md 입니다. -->
<style>{css(tokens())}</style>
</head>
<body>
{summary}

<div class="app">

<div class="top">
  <div class="mark">{e(tr['title'][:1])}</div>
  <div>
    <h1>{e(tr['title'])}</h1>
    <div class="sub">{e(tr['source'])}{' · Lv5 「' + e(tr['lv5']) + '」' if tr.get('lv5') else ''}</div>
  </div>
  <span class="pill">{e(verdict)}{" · 계약 흐름" if tr.get("mode") == "contract" else ""}</span>
</div>

<div class="rail">
  {rail(sk, tr)}
</div>

<main>
<div class="log">

  {input_card}

  {steps}

</div>

<div class="foot">
  {e(tr.get('summary', ''))}<br>
  {'루프백: ' + loops + '<br>' if loops else ''}
  {"이 화면은 <code>check/orchestrate.py</code>가 계약을 걸어 만든 것입니다 — 숫자는 없습니다."
    if tr.get("mode") == "contract" else
    "이 화면은 <code>python3 run.py</code>의 실제 실행 결과입니다 — 숫자·표는 <code>out/trace.json</code>에서 그대로 가져왔습니다."}
  데이터를 고치고 다시 돌리면 이 화면도 다시 만들어야 합니다:
  <code>python3 check/make_mockup.py {e(pack.name)}</code><br>
  {e(tr['source'])} · 데이터는 실습용 가상 값입니다.
</div>
</main>
</div>

<script type="application/json" id="agent-data">
{ssot}
</script>

<div class="dock" id="dock">
  <div class="track"><div class="fill" id="fill"></div></div>
  <div class="row">
    <span class="pct" id="pct">0%</span>
    <span class="clock" id="clock" title="시뮬레이션 시간입니다 — 실제 실행은 1초 미만입니다">
      ⏱ <b>0.0</b>s</span>
    <span class="what" id="what">▶ 실행을 누르면 한 단계씩 진행됩니다</span>
    <button class="primary" id="play" type="button">▶ 실행</button>
    <button id="next" type="button">다음 단계 ›</button>
    <button id="speed" type="button">1×</button>
    <button id="reset" type="button">처음으로</button>
    <span class="keys">스페이스 재생·일시정지 · → 다음 단계 · R 처음으로 ·
      레일의 단계를 클릭하면 거기까지 건너뜁니다 ·
      <b>시간은 시뮬레이션 값</b>입니다 (실제 실행은 1초 미만) ·
      끝까지 보려면 <b>전체 보기</b>를 누르십시오
      <button id="all" type="button" style="padding:2px 8px;margin-left:6px">전체 보기</button></span>
  </div>
</div>

<script>
// 재생 컨트롤러 — 데이터는 건드리지 않는다. 이미 그려진 단계를 순서대로 보여줄 뿐이다.
// 사람고유(halt) 단계에서는 **반드시 멈춘다.** 이 목업이 말하려는 것이 그것이다.
(function () {{
  const steps = [...document.querySelectorAll('.st')];
  const rail  = [...document.querySelectorAll('.rail .n')];
  const fill = document.getElementById('fill'), pct = document.getElementById('pct');
  const what = document.getElementById('what'), dock = document.getElementById('dock');
  const bPlay = document.getElementById('play'), bNext = document.getElementById('next');
  const bSpd = document.getElementById('speed'), bReset = document.getElementById('reset');
  const bAll = document.getElementById('all');
  const clock = document.getElementById('clock').querySelector('b');
  const capS = document.getElementById('cap-start'), capE = document.getElementById('cap-end');
  const SPEEDS = [1, 2, 4], DELAY = 1100, WORK = 420;
  let i = 0, timer = null, work = null, tick2 = null;
  let playing = false, spd = 0, waiting = false, held = null, t0 = 0, elapsed = 0;

  const bare = n => (n || '').replace(/^\s*\d+[.)]\s*/, '').trim();   // "5. 계정검증대사" → "계정검증대사"
  const railFor = n => rail.filter(r => bare(r.dataset.skill) === bare(n));

  function showClock() {{ clock.textContent = (elapsed / 1000).toFixed(1); }}
  function clockOn() {{ t0 = Date.now(); clearInterval(tick2);
    tick2 = setInterval(() => {{ elapsed += 100; showClock(); }}, 100); }}
  function clockOff() {{ clearInterval(tick2); tick2 = null; }}

  // 숫자를 0에서 세어 올린다 — 방금 계산된 것처럼 보이게.
  function countUp(el) {{
    const end = parseInt(el.dataset.n ?? el.textContent.replace(/[^0-9]/g, ''), 10);
    if (!Number.isFinite(end) || end === 0) return;
    el.dataset.n = end; let v = 0;
    const st = setInterval(() => {{
      v = Math.min(end, v + Math.max(1, Math.ceil(end / 12)));
      el.firstChild.nodeValue = v;
      if (v >= end) clearInterval(st);
    }}, 45);
  }}

  function paint() {{
    const p = Math.round(i / steps.length * 100);
    fill.style.width = p + '%'; pct.textContent = p + '%';
    dock.classList.toggle('done', i >= steps.length);
    dock.classList.toggle('waiting', waiting);
    bPlay.textContent = playing ? '⏸ 일시정지' : (i >= steps.length ? '↻ 다시' : '▶ 실행');
    if (i >= steps.length) {{ what.innerHTML = '<b>완료</b> — 모든 단계가 끝났습니다.'; return; }}
    const s = steps[i];
    what.innerHTML = waiting
      ? '⏸ <b>' + bare(held.dataset.skill) + '</b> — 사람 확인 대기. 확인해야 다음으로 갑니다.'
      : (i === 0 ? '▶ 실행을 누르면 한 단계씩 진행됩니다'
                 : '다음: <b>' + bare(s.dataset.skill) + '</b>');
  }}

  function reveal(done) {{
    if (i >= steps.length) {{ stop(); capE.classList.add('on'); paint(); return; }}
    const s = steps[i];
    steps.forEach(x => x.classList.remove('now'));
    rail.forEach(r => r.classList.remove('now'));
    capS.classList.add('on');
    s.classList.add('shown', 'now', 'working');       // 먼저 "처리 중"을 보여준다
    railFor(s.dataset.skill).forEach(r => r.classList.add('lit', 'now'));
    s.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    const dur = WORK / SPEEDS[spd];
    clearTimeout(work);
    work = setTimeout(() => {{                          // 그 다음 결과로 바뀐다
      s.classList.remove('working');
      const ms = s.querySelector('.ms');
      if (ms) {{ ms.textContent = (0.08 + Math.random() * 0.35).toFixed(2) + 's';
                ms.classList.add('on'); }}
      s.querySelectorAll('.br .cnt:not(.none)').forEach(countUp);
      i++;
      if (s.dataset.kind === 'halt' && i < steps.length) {{
        waiting = true; held = s; s.classList.add('waiting'); stop(); paint(); return;
      }}
      if (i >= steps.length) {{ capE.classList.add('on'); stop(); }}
      paint();
      if (done) done();
    }}, dur);
  }}

  function tick() {{ reveal(() => {{ if (playing && !waiting) schedule(); }}); }}
  function schedule() {{ clearTimeout(timer); timer = setTimeout(tick, DELAY / SPEEDS[spd]); }}
  function stop() {{ playing = false; clearTimeout(timer); clockOff(); }}

  function play() {{
    if (waiting) return;
    if (i >= steps.length) {{ reset(); setTimeout(play, 350); return; }}
    playing = true; clockOn(); paint(); tick();
  }}
  function reset() {{
    stop(); clearTimeout(work); waiting = false; held = null; i = 0; elapsed = 0; showClock();
    capS.classList.remove('on'); capE.classList.remove('on');
    steps.forEach(x => {{ x.classList.remove('shown', 'now', 'waiting', 'working');
      const m = x.querySelector('.ms'); if (m) {{ m.textContent = ''; m.classList.remove('on'); }}
      x.querySelectorAll('.br .cnt').forEach(c => {{
        if (c.dataset.n) c.firstChild.nodeValue = c.dataset.n; }}); }});
    rail.forEach(r => r.classList.remove('lit', 'now'));
    document.body.classList.add('play');
    window.scrollTo({{ top: 0, behavior: 'smooth' }}); paint();
  }}
  function showAll() {{
    stop(); clearTimeout(work); waiting = false; held = null; i = steps.length;
    steps.forEach(x => {{ x.classList.add('shown');
      x.classList.remove('now', 'waiting', 'working'); }});
    rail.forEach(r => r.classList.add('lit'));
    capS.classList.add('on'); capE.classList.add('on');
    paint();
  }}

  // 레일을 클릭하면 그 단계까지 건너뛴다 — 데모에서 보고 싶은 대목만 짚어 보여줄 때.
  function jumpTo(name) {{
    const at = steps.findIndex(s => bare(s.dataset.skill) === bare(name));
    if (at < 0) return;
    stop(); clearTimeout(work); waiting = false; held = null;
    steps.forEach((x, k) => {{
      x.classList.toggle('shown', k <= at);
      x.classList.remove('now', 'waiting', 'working');
      const m = x.querySelector('.ms');
      if (m && k <= at && !m.textContent) {{
        m.textContent = (0.08 + Math.random() * 0.35).toFixed(2) + 's'; m.classList.add('on'); }}
    }});
    // 건너뛴 지점까지의 레일도 함께 켠다 — 지나온 것이 꺼져 있으면 어디까지 왔는지 안 보인다.
    const passed = new Set(steps.slice(0, at + 1).map(s => bare(s.dataset.skill)));
    rail.forEach(r => {{ r.classList.remove('now');
                        r.classList.toggle('lit', passed.has(bare(r.dataset.skill))); }});
    railFor(name).forEach(r => r.classList.add('now'));
    steps[at].classList.add('now');
    i = at + 1; capS.classList.add('on');
    capE.classList.toggle('on', i >= steps.length);
    steps[at].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    paint();
  }}
  function proceed() {{     // 사람 확인 버튼
    if (!waiting) return;
    waiting = false; held = null;
    steps.forEach(x => x.classList.remove('waiting'));
    paint(); play();
  }}

  bPlay.onclick = () => (playing ? (stop(), paint()) : play());
  bNext.onclick = () => {{ if (waiting) return proceed(); stop(); reveal(); }};
  bReset.onclick = reset;
  bAll.onclick = showAll;
  bSpd.onclick = () => {{ spd = (spd + 1) % SPEEDS.length; bSpd.textContent = SPEEDS[spd] + '×';
                         if (playing) schedule(); }};
  document.querySelectorAll('.waitbar .go').forEach(b => b.onclick = proceed);
  rail.forEach(r => r.onclick = () => jumpTo(r.dataset.skill));
  addEventListener('keydown', ev => {{
    if (ev.target.tagName === 'INPUT') return;
    if (ev.code === 'Space') {{ ev.preventDefault(); waiting ? proceed() : bPlay.onclick(); }}
    if (ev.key === 'ArrowRight') {{ ev.preventDefault(); bNext.onclick(); }}
    if (ev.key === 'r' || ev.key === 'R') reset();
  }});

  reset();   // 자바스크립트가 살아 있을 때만 재생 모드로 — 꺼져 있으면 전부 그냥 보인다
}})();
</script>
</body>
</html>
"""
    out = pack / "agent-mockup.html"
    out.write_text(doc, encoding="utf-8")
    print(f"목업 생성: {out}")
    print(f"  단계 {len([s for s in tr['steps'] if s['kind'] != 'loopback'])}개 · "
          f"표 {sum(len(s.get('tables', [])) for s in tr['steps'])}개 · "
          f"루프백 {len(tr.get('loops', []))}곳 · 판정 {verdict}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
