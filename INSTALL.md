# 설치 안내 (사내망 · 인터넷 없이)

**인터넷·git·pip 모두 필요 없습니다.** 파일 복사만 합니다.

## 필요한 것

| | |
|---|---|
| Python | 3.8 이상 (`python3 -V`로 확인). **외부 패키지 없음** — 표준 라이브러리만 씁니다 |
| Claude Code | 스킬을 부르려면 필요. 스크립트만 쓸 거면 없어도 됩니다 |
| 인터넷 | **필요 없음** |

## 1. 폴더 받기

담당자에게 받은 **`Activity-Coach-SKI` 폴더(또는 zip)** 를 원하는 자리에 풉니다.
바탕화면이든 사내 공유 드라이브에서 복사해 온 것이든 상관없습니다.

## 2. 설치

**macOS · Linux · WSL**

```bash
cd Activity-Coach-SKI
bash install.sh
```

**Windows (PowerShell)**

```powershell
cd Activity-Coach-SKI
powershell -ExecutionPolicy Bypass -File install.ps1
```

`~/.claude/skills/` 에 스킬 2개가 들어갑니다. 이 컴퓨터의 **모든 프로젝트**에서 쓸 수 있습니다.

특정 폴더에서만 쓰려면 `--project`(PowerShell은 `-Project`)를 붙입니다.

설치 스크립트는 마지막에 **재무 샘플 팩을 실제로 점검해 보고** 통과해야 완료로 알립니다.
여기서 실패하면 복사가 덜 된 것이니 폴더를 다시 받으십시오.

## 3. 확인

Claude Code를 **새로 열고** 입력해 봅니다.

```
/activity-coach
/slide-pack
```

두 개가 목록에 뜨면 설치된 것입니다.

## 4. 첫 실습 — 재무 팩 돌려보기

```bash
cd ~/.claude/skills/activity-coach/examples/sample/quarterly-close-agent
python3 run.py
```

이렇게 나오면 정상입니다.

```
[계정검증대사] [1회차] 대사 5계정 · 차이 1건 · 확인서미수신 1건 (차이로 세지 않음)
◆ 차이 발견? → Yes · 차이분석조정으로 분기
[차이분석조정] ⛔ 사람고유 — 차이 1건의 목록과 근거만 만듦 (조정 금액을 정하지 않음)
[차이분석조정] ↩ 계정검증대사로 되돌아감 (탈출 조건: 차이 0)
[계정검증대사] [2회차] 대사 5계정 · 차이 0건
◆ 차이 발견? → No · 결산마감으로 진행 (2회차에 탈출)
[결산마감] ⛔ 사람고유 — 점검표 4건만 만들고 멈춤

루프백 1회 (차이대사 L4) · 최종 2회차에 차이 0
사람 확인 없이 마감된 것: 없음
```

`out/` 폴더에 마크다운 표 5개가 생깁니다. 열어 보십시오.

### 값을 바꿔 보기

입력은 `data/결산데이터.md` **한 파일**입니다. 메모장으로 열립니다.

| 고칠 것 | 일어나는 일 |
|---|---|
| 외부확인서 표에서 거래처B 확인잔액을 `5220000000`으로 | 차이가 0이 되어 **루프백 없이 1회차에 마감** |
| 조정사유사전 표에 `\| 2210 \| 미지급비용 증가 — 분기 귀속분 반영 \|` 한 줄 추가 | 마감 점검표가 **4건 → 3건** |

값을 고치고 `python3 run.py`를 다시 돌리면 흐름이 어디로 갈라지는지 바로 보입니다.

## 5. 점검기 직접 돌려보기

```bash
cd ~/.claude/skills/activity-coach
python3 check/run_check.py examples/sample/quarterly-close-agent   # 판정
python3 check/readchk.py  examples/sample/quarterly-close-agent    # 미결 갈래
```

## 자주 나오는 문제

**`python3: command not found`**
Windows에서는 `python`입니다. `python -V`로 3.8 이상인지 확인하십시오.

**`/activity-coach`가 목록에 안 뜬다**
Claude Code를 완전히 껐다 켜십시오. 그래도 없으면 `ls ~/.claude/skills/`로
`activity-coach/SKILL.md`가 실제로 있는지 확인합니다.

**한글이 깨진다 (Windows)**
PowerShell에서 `chcp 65001`을 한 번 실행한 뒤 다시 돌리십시오.

**`mdtable.py를 찾지 못했습니다`**
팩 폴더만 따로 복사한 경우입니다. `check/` 폴더가 함께 있어야 합니다 —
설치본 안(`~/.claude/skills/activity-coach/`)에서 실행하십시오.

## 지우기

```bash
rm -rf ~/.claude/skills/activity-coach ~/.claude/skills/slide-pack
```

```powershell
Remove-Item -Recurse -Force "$HOME\.claude\skills\activity-coach","$HOME\.claude\skills\slide-pack"
```

## 배포하는 분께

이 폴더를 그대로 zip으로 묶어 나눠주면 됩니다. `.git` 폴더는 빼도 됩니다.

```bash
cd .. && zip -r Activity-Coach-SKI.zip Activity-Coach-SKI -x '*/.git/*' '*/out/*' '*/__pycache__/*'
```
