# Activity Coach_SKI — 오프라인 설치 (Windows PowerShell)
#
#   powershell -ExecutionPolicy Bypass -File install.ps1
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Project
#
# 인터넷·git·pip 모두 필요 없습니다. 파일 복사만 합니다.

param([switch]$Project)

$ErrorActionPreference = "Stop"
$Here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Skills = @("activity-coach", "slide-pack")

if ($Project) {
    $Dest  = Join-Path $PWD ".claude\skills"; $Scope = "이 폴더"
} else {
    $Dest  = Join-Path $HOME ".claude\skills"; $Scope = "모든 프로젝트"
}

Write-Host "Activity Coach_SKI 설치"
Write-Host "  대상: $Dest  ($Scope 에서 사용)"
Write-Host ""

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "[X] python 이 없습니다. Python 3.8 이상을 먼저 설치하십시오." -ForegroundColor Red
    Write-Host "    (외부 패키지는 필요 없습니다 - 표준 라이브러리만 씁니다)"
    exit 1
}
Write-Host "[OK] $(& $py.Source -V)"

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
foreach ($s in $Skills) {
    $src = Join-Path $Here ".claude\skills\$s"
    $dst = Join-Path $Dest $s
    if (-not (Test-Path $src)) { Write-Host "[X] 원본 없음: $src" -ForegroundColor Red; exit 1 }
    if (Test-Path $dst) { Write-Host "  기존 $s 제거"; Remove-Item -Recurse -Force $dst }
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item (Join-Path $src "SKILL.md") $dst
    Write-Host "  - $s"
}

# 스킬이 실제로 실행할 것들을 함께 넣는다 - 스킬 폴더 하나로 자기완결이 되게.
$ac = Join-Path $Dest "activity-coach"
$sp = Join-Path $Dest "slide-pack"
Copy-Item (Join-Path $Here "check")   $ac -Recurse -Force
Copy-Item (Join-Path $Here "assets")  $ac -Recurse -Force
Copy-Item (Join-Path $Here "assets")  $sp -Recurse -Force
Copy-Item (Join-Path $Here "DESIGN.md") $sp -Force
New-Item -ItemType Directory -Force -Path (Join-Path $ac "examples") | Out-Null
Copy-Item (Join-Path $Here "examples\sample") (Join-Path $ac "examples") -Recurse -Force

Write-Host ""
Write-Host "동작 확인"
$check  = Join-Path $ac "check\run_check.py"
$sample = Join-Path $ac "examples\sample\quarterly-close-agent"
& $py.Source $check $sample *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] 통합 점검기 정상 (재무 샘플 팩 통과)" -ForegroundColor Green
} else {
    Write-Host "  [X] 통합 점검기가 샘플 팩을 통과시키지 못했습니다. 복사가 덜 된 것 같습니다." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "설치 완료."
Write-Host ""
Write-Host "Claude Code를 새로 열고 이렇게 부르십시오:"
Write-Host "  /activity-coach              팀 스킬들을 하나의 에이전트로 묶기"
Write-Host "  /slide-pack agent-plan.md    문서를 발표용 슬라이드로"
Write-Host ""
Write-Host "바로 해볼 것 (샘플 팩 실행):"
Write-Host "  cd $sample"
Write-Host "  python run.py"
Write-Host ""
Write-Host "지우려면: Remove-Item -Recurse -Force '$ac','$sp'"
