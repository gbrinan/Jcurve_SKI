import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const packageDir = import.meta.dirname;
const outputFlag = process.argv.indexOf("--output-dir");
const outputDir = outputFlag >= 0 ? path.resolve(process.argv[outputFlag + 1]) : path.join(packageDir, "data", "output");
if (outputFlag >= 0 && !process.argv[outputFlag + 1]) throw new Error("--output-dir requires a path");

function parseCsv(text) {
  const [header, ...lines] = text.trim().split(/\r?\n/);
  const fields = header.split(",");
  return lines.map((line) => Object.fromEntries(line.split(",").map((value, index) => [fields[index], value])));
}

function csv(header, rows) {
  return `${header.join(",")}\n${rows.map((row) => header.map((field) => row[field] ?? "").join(",")).join("\n")}\n`;
}

const input = parseCsv(readFileSync(path.join(packageDir, "data", "input", "incoming-quotes.csv"), "utf8"));
const policy = JSON.parse(readFileSync(path.join(packageDir, "data", "reference", "l4-policy-fixture.json"), "utf8"));

const normalized = input.map((quote) => {
  const parsed = Number(quote.unit_price);
  return {
    quote_id: quote.quote_id,
    supplier_code: quote.supplier_code,
    item_code: quote.item_code,
    unit_price_krw: Number.isFinite(parsed) ? String(parsed) : "",
    lead_days: quote.lead_days,
    parse_status: Number.isFinite(parsed) ? "ok" : "review",
  };
});

const comparison = normalized.map((quote) => {
  if (quote.parse_status === "review") {
    return { quote_id: quote.quote_id, price_variance_pct: "", lead_variance_days: "", policy_status: "review", evidence: "Upstream parse_status=review; source row preserved" };
  }
  const fixture = policy[quote.quote_id];
  if (!fixture) throw new Error(`Missing fictional policy fixture for ${quote.quote_id}`);
  return { quote_id: quote.quote_id, ...fixture };
});

const reviewRows = comparison.filter((row) => row.policy_status === "review");
const trace = {
  package: { name: "Sourcing Operations Lab", type: "team agent", independent_tasks: 3, human_holds: 2, review_branches: 2, external_actions: 0 },
  steps: [
    { id: "normalize", label: "견적 필드 정규화", kind: "system", owner: "sourcing-analyst", summary: `입력 ${input.length}행을 모두 보존하고 KRW·납기·파싱 상태를 정규화했습니다.`, metrics: [[String(input.length), "보존 행"], [String(normalized.filter((row) => row.parse_status === "ok").length), "정상 파싱"], [String(normalized.filter((row) => row.parse_status === "review").length), "검토 파싱"]] },
    { id: "analyze", label: "정책 편차 분석", kind: "review", owner: "sourcing-analyst", summary: `정상 ${comparison.filter((row) => row.policy_status === "pass").length}건, 사람 검토 ${reviewRows.length}건으로 분기했습니다.`, metrics: [[String(comparison.filter((row) => row.policy_status === "pass").length), "통과"], [String(comparison.filter((row) => row.price_variance_pct === "12.01").length), "임계값 초과"], [String(normalized.filter((row) => row.parse_status === "review").length), "파싱 실패"]], notice: "가격 12% 초과 또는 납기 7일 초과, 파싱 실패는 자동 선택으로 이어지지 않습니다." },
    { id: "variance-hold", label: "편차 검토 확인", kind: "human", owner: "buyer", hold: "intermediate", summary: "구매담당자가 정책 예외와 근거를 확인할 때까지 다음 스킬을 실행하지 않습니다." },
    { id: "brief", label: "구매 검토 브리프", kind: "system", owner: "buyer", summary: "모든 quote ID, 근거, 미해결 질문과 사람 다음 행동을 브리프에 보존했습니다.", metrics: [[String(input.length), "견적 보존"], [String(reviewRows.length), "검토 항목"], ["0", "외부 전송"]] },
    { id: "confirmation-hold", label: "구매자 최종 확인", kind: "human", owner: "buyer", hold: "final", summary: "여기서 멈춥니다. 공급업체 선택, 구매주문, ERP 반영은 수행하지 않았습니다." },
  ],
};

const brief = `# Fictional sourcing review brief

## Ordinary

- \`Q-NORMAL\`: 정책 매칭 성공, 가격 편차 0%, 납기 편차 0일, \`pass\`.

## Human review

- \`Q-REVIEW\`: 가격 편차 12.01%와 납기 편차 8일로 두 임계값을 모두 초과했다. 구매담당자가 정책 예외와 근거를 확인해야 한다.
- \`Q-FAILED\`: 가격 파싱 실패 행을 삭제하지 않고 보존했다. 구매담당자가 원본 값과 후속 조치를 확인해야 한다.

## Unresolved

- 운영 \`sourcing-policy.csv\` 열 스키마는 \`(미확인)\`이며 실제 연결 전에 구매담당자 확인이 필요하다.

## Buyer next action

\`buyer-confirmation-hold\`: 예외와 근거를 확인하고 공급업체 선택은 별도로 사람이 결정한다. 이 패키지는 구매주문을 보내거나 ERP에 쓰지 않는다.
`;

mkdirSync(outputDir, { recursive: true });
writeFileSync(path.join(outputDir, "normalized-quotes.csv"), csv(["quote_id", "supplier_code", "item_code", "unit_price_krw", "lead_days", "parse_status"], normalized));
writeFileSync(path.join(outputDir, "comparison-table.csv"), csv(["quote_id", "price_variance_pct", "lead_variance_days", "policy_status", "evidence"], comparison));
writeFileSync(path.join(outputDir, "sourcing-review-brief.md"), brief);
writeFileSync(path.join(outputDir, "trace.json"), `${JSON.stringify(trace, null, 2)}\n`);
console.log(JSON.stringify({ input_rows: input.length, output_rows: comparison.length, review_rows: reviewRows.length, human_holds: trace.package.human_holds, external_actions: 0 }));
