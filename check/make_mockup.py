#!/usr/bin/env python3
"""에이전트 실행 화면 목업 생성기 — 손으로 쓰던 것을 실행 결과에서 만든다.

사용: python3 check/make_mockup.py <팩 경로>   → <팩>/agent-mockup.html

읽는 것:
  · <팩>/out/trace.json   — run.py가 남긴 실행 기록. 화면의 **모든 숫자가 여기서 온다.**
  · <팩>/skills/*/*/SKILL.md — 진행 레일에 쓸 순서·Human 여부·루프백
  · DESIGN.md             — 색 토큰. 목업이 팔레트를 따로 갖지 않게 한다 (SSOT)

trace.json이 없으면 만들지 않는다. 실행하지 않은 화면은 지어낸 화면이다.
"""
import html
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
    kind = []
    if any(len(re.split(r"[|,]", m.get("next", ""))) > 1 for m in sk.values()
           if m.get("next") and m.get("next") != "null"):
        kind.append("갈림길")
    if tr.get("loops"):
        kind.append("루프백")
    verdict = f"팀 에이전트 · {'+'.join(kind)}" if kind else "팀 스킬팩"

    ins = " · ".join(f"{e(i['name'])} <b>{i['count']}건</b>" for i in tr["inputs"])
    input_card = (
        f'<div class="card"><header><b>입력</b>'
        f'<span class="tag">{e(tr["inputs"][0].get("note", "")) if tr["inputs"] else ""}</span>'
        f'</header><div class="body"><p>{ins}</p></div></div>') if tr["inputs"] else ""

    steps = "\n\n  ".join(step_html(s, sk, i) for i, s in enumerate(tr["steps"]))
    loops = " · ".join(f"{e(l['from'])} ↩ {e(l['to'])}"
                       + (f" ({l['cycles']}회차)" if l.get("cycles") else "")
                       for l in tr.get("loops", []))

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
<div class="app">

<div class="top">
  <div class="mark">{e(tr['title'][:1])}</div>
  <div>
    <h1>{e(tr['title'])}</h1>
    <div class="sub">{e(tr['source'])}{' · Lv5 「' + e(tr['lv5']) + '」' if tr.get('lv5') else ''}</div>
  </div>
  <span class="pill">{e(verdict)}</span>
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
  이 화면은 <code>python3 run.py</code>의 실제 실행 결과입니다 —
  숫자·표는 <code>out/trace.json</code>에서 그대로 가져왔습니다.
  데이터를 고치고 다시 돌리면 이 화면도 다시 만들어야 합니다:
  <code>python3 check/make_mockup.py {e(pack.name)}</code><br>
  {e(tr['source'])} · 데이터는 실습용 가상 값입니다.
</div>
</main>
</div>

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
