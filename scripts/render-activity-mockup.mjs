import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const TEMPLATE_URL = new URL(
  "../skills/activity-packaging-coach/assets/activity-mockup-template.html",
  import.meta.url
);

class ActivityMockupConfigError extends Error {
  constructor(field, message) {
    super(`${field}: ${message}`);
    this.name = "ActivityMockupConfigError";
    this.field = field;
  }
}

function requireObject(value, field) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ActivityMockupConfigError(field, "객체가 필요합니다");
  }
  return value;
}

function requireString(value, field) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new ActivityMockupConfigError(field, "비어 있지 않은 문자열이 필요합니다");
  }
  return value;
}

function requireNumber(value, field) {
  if (!Number.isInteger(value) || value < 0) {
    throw new ActivityMockupConfigError(field, "0 이상의 정수가 필요합니다");
  }
  return value;
}

function parseConfig(input) {
  const value = requireObject(input, "config");
  const levels = Array.isArray(value.levels) ? value.levels.map((item, index) => requireString(item, `levels[${index}]`)) : [];
  if (levels.length !== 3) throw new ActivityMockupConfigError("levels", "Lv4·Lv5·Lv6 세 항목이 필요합니다");

  const trace = requireObject(value.trace, "trace");
  const pkg = requireObject(trace.package, "trace.package");
  const steps = Array.isArray(trace.steps) ? trace.steps : [];
  if (steps.length === 0) throw new ActivityMockupConfigError("trace.steps", "한 개 이상의 실행 단계가 필요합니다");
  const parsedSteps = steps.map((item, index) => {
    const step = requireObject(item, `trace.steps[${index}]`);
    const kind = requireString(step.kind, `trace.steps[${index}].kind`);
    if (!new Set(["system", "review", "human"]).has(kind)) {
      throw new ActivityMockupConfigError(`trace.steps[${index}].kind`, "system·review·human 중 하나여야 합니다");
    }
    if (step.hold !== undefined && !new Set(["intermediate", "final"]).has(step.hold)) {
      throw new ActivityMockupConfigError(`trace.steps[${index}].hold`, "intermediate·final 중 하나여야 합니다");
    }
    return {
      ...step,
      id: requireString(step.id, `trace.steps[${index}].id`),
      label: requireString(step.label, `trace.steps[${index}].label`),
      kind,
      owner: requireString(step.owner, `trace.steps[${index}].owner`),
      summary: requireString(step.summary, `trace.steps[${index}].summary`)
    };
  });

  return {
    description: requireString(value.description, "description"),
    pageTitle: requireString(value.pageTitle, "pageTitle"),
    eyebrow: requireString(value.eyebrow, "eyebrow"),
    heading: requireString(value.heading, "heading"),
    lead: requireString(value.lead, "lead"),
    levels,
    appMark: requireString(value.appMark, "appMark"),
    appName: requireString(value.appName, "appName"),
    appMeta: requireString(value.appMeta, "appMeta"),
    verdict: requireString(value.verdict, "verdict"),
    inputSummary: requireString(value.inputSummary, "inputSummary"),
    inputMeta: requireString(value.inputMeta, "inputMeta"),
    externalActions: Array.isArray(value.externalActions) && value.externalActions.length > 0
      ? value.externalActions.map((item, index) => requireString(item, `externalActions[${index}]`))
      : ["외부 시스템 반영"],
    trace: {
      package: {
        ...pkg,
        name: requireString(pkg.name, "trace.package.name"),
        type: requireString(pkg.type, "trace.package.type"),
        independent_tasks: requireNumber(pkg.independent_tasks, "trace.package.independent_tasks"),
        human_holds: requireNumber(pkg.human_holds, "trace.package.human_holds"),
        review_branches: requireNumber(pkg.review_branches, "trace.package.review_branches"),
        external_actions: requireNumber(pkg.external_actions, "trace.package.external_actions")
      },
      steps: parsedSteps
    }
  };
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[char]);
}

function replaceOnce(source, search, replacement, field) {
  const first = source.indexOf(search);
  if (first < 0 || source.indexOf(search, first + search.length) >= 0) {
    throw new ActivityMockupConfigError(field, "기준 목업의 교체 지점이 정확히 하나여야 합니다");
  }
  return `${source.slice(0, first)}${replacement}${source.slice(first + search.length)}`;
}

export async function renderActivityMockup(input, outputPath) {
  const config = parseConfig(input);
  const e = escapeHtml;
  let html = await readFile(TEMPLATE_URL, "utf8");
  const replacements = [
    ['content="여러 업무 스킬을 팀 에이전트 또는 스킬팩으로 묶어 확인하는 실행 화면"', `content="${e(config.description)}"`, "description"],
    ["<title>공급업체 견적 검토 · 실행 확인 화면</title>", `<title>${e(config.pageTitle)}</title>`, "pageTitle"],
    ["스킬 통합 코치 · 비식별 실습", e(config.eyebrow), "eyebrow"],
    ["팀원이 만든 업무 지침을 연결하고 중복을 정리해, 함께 순서대로 실행하는 팀 에이전트나 필요할 때 골라 쓰는 스킬팩으로 구성합니다.", e(config.lead), "lead"],
    ['<span class="level">Lv4 구매 전략</span><span aria-hidden="true">›</span><span class="level current">Lv5 공급업체 견적 검토</span><span aria-hidden="true">›</span><span class="level">Lv6 작업 스킬 3</span>', `<span class="level">${e(config.levels[0])}</span><span aria-hidden="true">›</span><span class="level current">${e(config.levels[1])}</span><span aria-hidden="true">›</span><span class="level">${e(config.levels[2])}</span>`, "levels"],
    ['<div class="app-mark" aria-hidden="true">견</div>', `<div class="app-mark" aria-hidden="true">${e(config.appMark)}</div>`, "appMark"],
    ["<h3>공급업체 견적 검토 실행 화면</h3>", `<h3>${e(config.appName)}</h3>`, "appName"],
    ["가상 견적 3건 · 외부 연결 없음 · 구매 판단은 사람 책임", e(config.appMeta), "appMeta"],
    ["팀 에이전트 · 작업 3개", e(config.verdict), "verdict"],
    ["<p><strong>견적 3건</strong> · 정상 1건 · 기준값 검토 1건 · 파일 읽기 실패 1건</p>", `<p><strong>${e(config.inputSummary)}</strong></p>`, "inputSummary"],
    ["비식별 실습 입력 파일 · 실제 공급업체 연락 또는 주문 없음", e(config.inputMeta), "inputMeta"],
    ["공급업체 선택, 구매주문, 업무 시스템 반영은 이 화면에서 실행되지 않습니다.", `${config.externalActions.map(e).join(", ")}은 이 화면에서 실행되지 않습니다.`, "externalActions"],
    ['<button class="button" type="button" data-external-action disabled>공급업체 선택</button><button class="button" type="button" data-external-action disabled>구매주문 전송</button><button class="button" type="button" data-external-action disabled>ERP 반영</button>', config.externalActions.map((label) => `<button class="button" type="button" data-external-action disabled>${e(label)}</button>`).join(""), "externalActionButtons"]
  ];
  for (const [search, replacement, field] of replacements) html = replaceOnce(html, search, replacement, field);

  const tracePattern = /<script type="application\/json" id="trace-data">[\s\S]*?<\/script>/;
  const traceBlock = `<script type="application/json" id="trace-data">${JSON.stringify(config.trace, null, 2).replaceAll("<", "\\u003c")}</script>`;
  if (!tracePattern.test(html)) throw new ActivityMockupConfigError("trace", "기준 목업의 trace-data 블록을 찾지 못했습니다");
  html = html.replace(tracePattern, traceBlock);
  await writeFile(outputPath, html, "utf8");
}

const entryPath = process.argv[1];
if (entryPath && import.meta.url === pathToFileURL(entryPath).href) {
  const [configPath, outputPath] = process.argv.slice(2);
  if (!configPath || !outputPath) {
    throw new ActivityMockupConfigError("command", "node scripts/render-activity-mockup.mjs <config.json> <agent-mockup.html>");
  }
  const config = JSON.parse(await readFile(configPath, "utf8"));
  await renderActivityMockup(config, outputPath);
  console.log(`Activity 목업 생성: ${outputPath}`);
}
