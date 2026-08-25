import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { renderActivityMockup } from "./render-activity-mockup.mjs";

const outputDir = await mkdtemp(join(tmpdir(), "activity-mockup-test-"));
const outputPath = join(outputDir, "agent-mockup.html");

const config = {
  description: "가상 교육 대상자 선정 팀 에이전트 실행 목업",
  pageTitle: "교육 대상자 선정 · 실행 확인 화면",
  eyebrow: "스킬 통합 코치 · 비식별 실습",
  heading: "여러 스킬을 묶어 팀 에이전트 또는 스킬팩을 만듭니다.",
  lead: "팀원이 만든 업무 지침을 연결하고 중복을 정리해 팀 에이전트나 스킬팩으로 구성합니다.",
  levels: ["Lv4 역량개발", "Lv5 교육 대상자 선정", "Lv6 작업 스킬 3"],
  appMark: "ED",
  appName: "Education Operations Lab",
  appMeta: "가상 신청 4건 · 외부 연결 없음 · 최종 판단은 사람 책임",
  verdict: "팀 에이전트 · 작업 3개",
  inputSummary: "신청 4건 · 정상 2건 · 사람 검토 2건",
  inputMeta: "data/input/fixture.json · 실제 메일 또는 HR 시스템 호출 없음",
  trace: {
    package: {
      name: "Education Operations Lab",
      type: "team agent",
      independent_tasks: 3,
      human_holds: 1,
      review_branches: 1,
      external_actions: 0
    },
    steps: [
      {
        id: "normalize",
        label: "신청 자료 정규화",
        kind: "system",
        owner: "education-operator",
        summary: "입력 4건을 보존했습니다.",
        metrics: [["4", "보존 행"]]
      },
      {
        id: "review",
        label: "대상자 검토",
        kind: "review",
        owner: "education-operator",
        summary: "정상 2건과 사람 검토 2건으로 나눴습니다.",
        metrics: [["2", "정상"], ["2", "사람 검토"]]
      },
      {
        id: "confirmation-hold",
        label: "담당자 최종 확인",
        kind: "human",
        owner: "education-owner",
        hold: "final",
        summary: "여기서 멈춥니다. 명단 배포는 수행하지 않았습니다."
      }
    ]
  }
};

await renderActivityMockup(config, outputPath);
const html = await readFile(outputPath, "utf8");

assert.match(html, /class="rail-scroll"/, "실행 레일을 보존해야 한다");
assert.match(html, /class="control-dock"/, "고정 재생 제어를 보존해야 한다");
assert.match(html, /id="trace-data"/, "동일 기록을 내장해야 한다");
assert.match(html, /사람 확인 대기/, "사람 정지 UI를 보존해야 한다");
assert.match(html, /Education Operations Lab/, "업무별 설정을 반영해야 한다");
assert.match(html, /신청 자료 정규화/, "업무별 실행 단계를 반영해야 한다");
assert.match(html, /스킬 통합 코치/, "코치 이름을 첫 화면에 표시해야 한다");
assert.match(html, /스킬팩.*여러 스킬을 묶어 필요한 것을 골라 쓰는 구성/s, "스킬팩을 쉬운 말로 설명해야 한다");
assert.match(html, /팀 에이전트.*여러 스킬을 순서와 갈림길로 연결해 함께 실행하는 구성/s, "팀 에이전트를 쉬운 말로 설명해야 한다");
assert.doesNotMatch(html, />SYSTEM<|>REVIEW BRANCH<|>HUMAN HOLD</, "사람이 보는 단계 이름에 영문 개발 용어를 노출하면 안 된다");
assert.doesNotMatch(html, /<button id="run">가상 실행<\/button>/, "단순 3카드 목업으로 축소하면 안 된다");

await assert.rejects(
  () => renderActivityMockup({ ...config, trace: { ...config.trace, steps: [] } }, outputPath),
  /trace\.steps/,
  "실행 단계가 없는 목업은 만들지 않아야 한다"
);

console.log("Activity 목업 계약 테스트 통과: 12개");
