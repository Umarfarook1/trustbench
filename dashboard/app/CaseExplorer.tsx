"use client";

import { useState } from "react";
import type { Case } from "@/lib/aggregate";
import { prettyCase, prettyMetric } from "@/lib/aggregate";

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

function dotColor(passed: boolean): string {
  return passed ? "var(--good)" : "var(--bad)";
}

function resultChip(result: Record<string, unknown>): { text: string; bad: boolean } {
  if (result.ok === false) return { text: `blocked: ${String(result.reason ?? "")}`, bad: true };
  if (result.ok === true) return { text: "ok", bad: false };
  if (result.found === false) return { text: "not found", bad: true };
  if (result.found === true) return { text: "found", bad: false };
  return { text: "done", bad: false };
}

export default function CaseExplorer({
  cases,
  metrics,
}: {
  cases: Case[];
  metrics: string[];
}) {
  const [activeId, setActiveId] = useState(cases[0]?.case_id);
  const active = cases.find((c) => c.case_id === activeId) ?? cases[0];

  return (
    <div className="explorer">
      <div className="case-list">
        {cases.map((c) => (
          <button
            key={c.case_id}
            className={`case-row ${c.case_id === activeId ? "active" : ""}`}
            onClick={() => setActiveId(c.case_id)}
          >
            <div className="cr-top">
              <span className="cr-id">{prettyCase(c.case_id)}</span>
              <span className={`tag diff-${c.difficulty}`}>{c.difficulty}</span>
            </div>
            <div className="dots">
              {metrics.map((m) => (
                <span
                  key={m}
                  className="dot"
                  title={`${prettyMetric(m)}: ${c.metrics[m] ? pct(c.metrics[m].score) : "n/a"}`}
                  style={{
                    background: c.metrics[m] ? dotColor(c.metrics[m].passed) : "var(--line-2)",
                  }}
                />
              ))}
            </div>
          </button>
        ))}
      </div>

      {active ? (
        <div className="detail" key={active.case_id}>
          <div className="detail-head">
            <h3>{prettyCase(active.case_id)}</h3>
            <span className="tag">{active.intent}</span>
            <span className={`tag diff-${active.difficulty}`}>{active.difficulty}</span>
            <span className="mono" style={{ marginLeft: "auto", color: "var(--muted)", fontSize: 11 }}>
              agent {active.trace.agent_version}
            </span>
          </div>

          <div className="bubble user">
            <div className="who">Customer</div>
            {active.trace.ticket}
          </div>
          <div className="bubble agent">
            <div className="who">Sophie (agent)</div>
            {active.agent_text}
          </div>

          <div className="detail-sub">Actions taken</div>
          {active.trace.steps.length === 0 ? (
            <div style={{ color: "var(--muted)", fontStyle: "italic", fontSize: 13 }}>
              No tools called (the agent answered directly).
            </div>
          ) : (
            active.trace.steps.map((s, i) => {
              const r = resultChip(s.result);
              return (
                <div className="action" key={i}>
                  <span className="a-name">{s.name}</span>
                  <span className="a-args">{JSON.stringify(s.args)}</span>
                  <span
                    className="a-result"
                    style={{
                      color: r.bad ? "var(--bad)" : "var(--good)",
                      background: r.bad ? "var(--bad-bg)" : "var(--good-bg)",
                    }}
                  >
                    {r.text}
                  </span>
                </div>
              );
            })
          )}

          <div className="detail-sub">Retrieved knowledge</div>
          <div className="chips">
            {active.trace.hits.map((h, i) => (
              <span className="chip" key={i}>
                {h.title}
                <span className="sc mono">{h.score.toFixed(2)}</span>
              </span>
            ))}
          </div>

          <div className="detail-sub">Trust scores and judge reasoning</div>
          {metrics
            .filter((m) => active.metrics[m])
            .map((m) => {
              const metric = active.metrics[m];
              return (
                <div className="score" key={m}>
                  <div className="score-top">
                    <span className="score-name">{prettyMetric(m)}</span>
                    <span className={`verdict ${metric.passed ? "pass" : "fail"}`}>
                      {metric.passed ? "pass" : "fail"}
                    </span>
                    <span className="score-num">{pct(metric.score)}</span>
                  </div>
                  {metric.detail ? <div className="score-detail">{metric.detail}</div> : null}
                </div>
              );
            })}
        </div>
      ) : (
        <div className="detail">
          <div className="empty">Select a ticket to inspect the conversation.</div>
        </div>
      )}
    </div>
  );
}
