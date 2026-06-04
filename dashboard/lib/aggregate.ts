// Pure, client-safe helpers and types. No node imports here so client components can use
// it. Data loading (fs) lives in lib/data.ts, server only.

export type Metric = { name: string; score: number; passed: boolean; detail: string };
export type ToolStep = {
  name: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
};
export type Hit = { doc_id: string; title: string; score: number };
export type Trace = {
  ticket: string;
  agent_version: string;
  policy_in_context: boolean;
  retrieval_query: string;
  hits: Hit[];
  steps: ToolStep[];
  final_response: string;
  exceeded_budget: boolean;
};
export type Case = {
  case_id: string;
  intent: string;
  difficulty: string;
  agent_text: string;
  metrics: Record<string, Metric>;
  trace: Trace;
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

// The seven trust dimensions, in display order.
export const METRIC_ORDER = [
  "resolution_accuracy",
  "escalation_intelligence",
  "policy_adherence",
  "policy_guardrail_hard",
  "completeness",
  "tone_empathy",
  "groundedness",
  "tool_coverage",
];

export function metricNames(run: Run): string[] {
  const present = new Set<string>();
  for (const c of run.cases) for (const k of Object.keys(c.metrics)) present.add(k);
  const ordered = METRIC_ORDER.filter((m) => present.has(m));
  for (const m of present) if (!ordered.includes(m)) ordered.push(m);
  return ordered;
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

export function caseById(run: Run, id: string): Case | undefined {
  return run.cases.find((c) => c.case_id === id);
}

export function prettyMetric(name: string): string {
  return name.replace(/_/g, " ").replace("policy guardrail hard", "guardrails (hard checks)");
}

export function prettyCase(id: string): string {
  return id.replace(/_/g, " ");
}
