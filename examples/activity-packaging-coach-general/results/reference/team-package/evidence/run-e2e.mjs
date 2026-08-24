import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const packageDir = path.resolve(import.meta.dirname, "..");
const outputDir = mkdtempSync(path.join(tmpdir(), "activity-procurement-"));
execFileSync(process.execPath, [path.join(packageDir, "run.mjs"), "--output-dir", outputDir], {
  cwd: packageDir,
  stdio: "inherit",
});

const rows = readFileSync(path.join(outputDir, "comparison-table.csv"), "utf8").trim().split(/\r?\n/);
const trace = JSON.parse(readFileSync(path.join(outputDir, "trace.json"), "utf8"));
const ids = rows.slice(1).map((row) => row.split(",")[0]);
const checks = {
  allSourceRowsPreserved: ids.join("|") === "Q-NORMAL|Q-REVIEW|Q-FAILED",
  ordinaryPasses: rows.some((row) => row.startsWith("Q-NORMAL,0,0,pass,")),
  thresholdStops: rows.some((row) => row.startsWith("Q-REVIEW,12.01,8,review,")),
  parseFailureStops: rows.some((row) => row.startsWith("Q-FAILED,,,review,")),
  humanHoldsPreserved: trace.package.human_holds === 2 && trace.steps.filter((step) => step.hold).length === 2,
  externalActionsAbsent: trace.package.external_actions === 0,
  fiveReachableSteps: trace.steps.length === 5,
};

console.log(JSON.stringify(checks));
if (Object.values(checks).some((passed) => !passed)) process.exitCode = 1;
