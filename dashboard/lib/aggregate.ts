import fs from "node:fs";
import path from "node:path";

export type Metric = { name: string; score: number; passed: boolean; detail: string };
export type Case = {
  case_id: string;
  intent: string;
  difficulty: string;
  agent_text: string;
  metrics: Record<string, Metric>;
};
export type Run = { run_label: string; agent_version: string; cases: Case[] };

export type MetricDelta = { metric: string; baseline: number; candidate: number; delta: number };
export type SliceRegression = {
  intent: string;
  metric: string;
  baseline: number;
  candidate: number;
  delta: number;
};
export type McNemar = {
  metric: string;
  regressed: number;
  improved: number;
  statistic: number;
  p_value: number;
};
export type RegressionReport = {
  baseline_label: string;
  candidate_label: string;
  overall: MetricDelta[];
  regressed_slices: SliceRegression[];
  mcnemar: McNemar[];
};

function readJson<T>(file: string): T {
  const full = path.join(process.cwd(), "data", file);
  return JSON.parse(fs.readFileSync(full, "utf-8")) as T;
}

export function loadRun(): Run {
  return readJson<Run>("sample-run.json");
}

export function loadRegression(): RegressionReport {
  return readJson<RegressionReport>("sample-regression.json");
}

export function metricNames(run: Run): string[] {
  const names: string[] = [];
  for (const c of run.cases) {
    for (const name of Object.keys(c.metrics)) {
      if (!names.includes(name)) names.push(name);
    }
  }
  return names;
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function overall(run: Run): Record<string, number> {
  const out: Record<string, number> = {};
  for (const name of metricNames(run)) {
    out[name] = mean(run.cases.filter((c) => name in c.metrics).map((c) => c.metrics[name].score));
  }
  return out;
}

export function byIntent(run: Run): Record<string, Record<string, number>> {
  const names = metricNames(run);
  const intents = Array.from(new Set(run.cases.map((c) => c.intent)));
  const out: Record<string, Record<string, number>> = {};
  for (const intent of intents) {
    const cases = run.cases.filter((c) => c.intent === intent);
    out[intent] = {};
    for (const name of names) {
      out[intent][name] = mean(
        cases.filter((c) => name in c.metrics).map((c) => c.metrics[name].score),
      );
    }
  }
  return out;
}

export function prettyMetric(name: string): string {
  return name.replace(/_/g, " ");
}
