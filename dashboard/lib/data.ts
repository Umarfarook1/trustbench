import fs from "node:fs";
import path from "node:path";
import type { RegressionReport, Run } from "@/lib/aggregate";

function readJson<T>(file: string): T {
  const full = path.join(process.cwd(), "data", file);
  return JSON.parse(fs.readFileSync(full, "utf-8")) as T;
}

export function loadRun(): Run {
  return readJson<Run>("sample-run.json");
}

export function loadRunV2(): Run {
  return readJson<Run>("sample-run-v2.json");
}

export function loadRegression(): RegressionReport {
  return readJson<RegressionReport>("sample-regression.json");
}
