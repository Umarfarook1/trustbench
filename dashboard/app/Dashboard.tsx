"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import CaseExplorer from "./CaseExplorer";
import {
  byIntent,
  caseById,
  metricNames,
  overall,
  prettyMetric,
  type RegressionReport,
  type Run,
} from "@/lib/aggregate";
import { CITATIONS, CITE_BY_ID } from "@/lib/citations";

const SHORT: Record<string, string> = {
  resolution_accuracy: "Resolution",
  escalation_intelligence: "Escalation",
  policy_adherence: "Policy",
  policy_guardrail_hard: "Guardrails",
  completeness: "Complete",
  tone_empathy: "Tone",
  groundedness: "Grounded",
  tool_coverage: "Tools",
};

const SECTIONS = [
  { id: "story", label: "story" },
  { id: "problem", label: "problem" },
  { id: "approach", label: "approach" },
  { id: "evidence", label: "evidence" },
  { id: "regression", label: "regression" },
  { id: "roi", label: "ROI" },
  { id: "about", label: "about" },
  { id: "references", label: "references" },
];

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

function barColor(s: number): string {
  if (s >= 0.9) return "var(--lime-600)";
  if (s >= 0.7) return "var(--ok)";
  return "var(--bad)";
}

function cellStyle(s: number) {
  if (s >= 0.9) return { background: "var(--good-bg)", color: "var(--good)" };
  if (s >= 0.7) return { background: "var(--ok-bg)", color: "var(--ok)" };
  return { background: "var(--bad-bg)", color: "var(--bad)" };
}

const tipStyle = {
  background: "#fff",
  border: "1px solid #ebede4",
  borderRadius: 10,
  fontSize: 12,
  fontFamily: "var(--font-mono), monospace",
  boxShadow: "0 8px 24px -12px rgba(16,20,10,.3)",
};

function Cite({ id }: { id: string }) {
  const c = CITE_BY_ID[id];
  if (!c) return null;
  return (
    <a className="cite" href={`#ref-${id}`} title={`${c.label} — ${c.source}`}>
      [{c.n}]
    </a>
  );
}

export default function Dashboard({
  v1,
  v2,
  reg,
}: {
  v1: Run;
  v2: Run;
  reg: RegressionReport;
}) {
  const [version, setVersion] = useState<"v1" | "v2">("v1");
  const [active, setActive] = useState("story");
  const run = version === "v1" ? v1 : v2;

  const names = metricNames(v1);
  const ov = overall(run);
  const intents = byIntent(run);

  const radarData = names.map((n) => ({ metric: SHORT[n] ?? n, score: Math.round(ov[n] * 100) }));
  const changed = reg.overall.filter((d) => Math.abs(d.delta) > 0.001);
  const regBarData = changed.map((d) => ({
    metric: SHORT[d.metric] ?? d.metric,
    v1: Math.round(d.baseline * 100),
    v2: Math.round(d.candidate * 100),
  }));
  const ov1 = overall(v1);
  const ov2 = overall(v2);
  const disputeV1 = caseById(v1, "dispute_unrecognized_charge");
  const disputeV2 = caseById(v2, "dispute_unrecognized_charge");

  const resolution = ov["resolution_accuracy"] ?? 0;
  const policy = ov["policy_adherence"] ?? 0;

  useEffect(() => {
    const els = SECTIONS.map((s) => document.getElementById(s.id)).filter(Boolean) as HTMLElement[];
    const obs = new IntersectionObserver(
      (entries) => {
        const vis = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (vis[0]) setActive(vis[0].target.id);
      },
      { rootMargin: "-35% 0px -55% 0px", threshold: [0, 0.2, 0.5, 1] },
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  const go = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <>
      <nav className="nav">
        <div className="nav-inner">
          <span className="brand-dot" />
          <span className="brand-mark">TrustBench</span>
          <div className="nav-links">
            {SECTIONS.map((s) => (
              <button key={s.id} className={active === s.id ? "active" : ""} onClick={() => go(s.id)}>
                {s.label}
              </button>
            ))}
          </div>
          <div className="nav-right">
            <span className="pill pill-sample">live · groq</span>
            <a href="https://github.com/Umarfarook1/trustbench" target="_blank" rel="noreferrer">
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <main className="shell">
        {/* STORY */}
        <section id="story" className="hero">
          <div className="eyebrow">a working sample of the role</div>
          <h1>
            I onboarded a neobank to an AI support agent, then caught a regression{" "}
            <span className="hl">before it reached a customer.</span>
          </h1>
          <p className="prose">
            This is the Fini AI Solutions Engineer job, run end to end before applying: configure the
            agent, evaluate it on the seven trust dimensions Fini publishes, catch what breaks, and
            show what it is worth. Everything below explains not just what I built, but <strong>why</strong>,
            with sources.
          </p>
          <div className="cta-row">
            <button className="btn btn-primary" onClick={() => go("regression")}>
              See the regression
            </button>
            <button className="btn btn-ghost" onClick={() => go("approach")}>
              How it works, and why
            </button>
          </div>

          <div className="scorecard" style={{ marginTop: 38 }}>
            <div className="card stat-card">
              <div className="bigstats">
                <div className="bigstat">
                  <div className="n">
                    {v1.cases.length}
                    <small> scenarios</small>
                  </div>
                  <div className="l">A golden set of support tickets, including adversarial ones.</div>
                </div>
                <div className="bigstat">
                  <div className="n">
                    7<small> trust metrics</small>
                  </div>
                  <div className="l">Named after Fini&apos;s own framework, judged by an independent model.</div>
                </div>
              </div>
              <div className="bigstat">
                <div className="n" style={{ color: "var(--bad)" }}>
                  {reg.regressed_slices.length}
                  <small> regressed slices</small>
                </div>
                <div className="l">Category-level failures the overall averages hid.</div>
              </div>
            </div>
            <div className="card radar-card">
              <div className="rt">trust shape · agent v1 baseline</div>
              <div style={{ width: "100%", height: 296 }}>
                <ResponsiveContainer>
                  <RadarChart data={names.map((n) => ({ metric: SHORT[n] ?? n, score: Math.round(overall(v1)[n] * 100) }))} outerRadius="70%">
                    <PolarGrid stroke="#e6e8df" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "#7b8170" }} />
                    <Radar
                      dataKey="score"
                      stroke="var(--lime-600)"
                      fill="var(--lime)"
                      fillOpacity={0.45}
                      strokeWidth={2}
                      animationDuration={650}
                    />
                    <Tooltip contentStyle={tipStyle} formatter={(v) => [`${v}%`, "score"]} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </section>

        {/* PROBLEM */}
        <section id="problem" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">the problem</div>
              <h2>Why you cannot just trust a support agent</h2>
            </div>
          </div>
          <div className="prose">
            <p>
              Most AI support metrics measure the wrong thing. A bot that deflects 70 percent of
              tickets but actually resolves 30 percent is not helping customers, it is blocking them
              from help. Fini makes this argument directly: deflection is a vanity metric, resolution
              is what counts.<Cite id="fini-trust" />
            </p>
            <p>
              Support is also not a document-retrieval problem. It is a reasoning and policy problem:
              when can this customer get a refund, is their identity verified, does this need a human.
              <Cite id="fini-ragless" />
            </p>
            <p>
              So you do not earn trust because the agent demos well. You earn it because someone
              measured how often it is right, proved the measurement itself can be trusted, and can
              show exactly why it fails. <strong>That measurement is the job</strong>, and it is what
              this project does.
            </p>
          </div>
        </section>

        {/* APPROACH */}
        <section id="approach" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">what I built</div>
              <h2>Six decisions, and why each one</h2>
            </div>
            <div className="section-note">Every choice is grounded in current practice, not guesswork.</div>
          </div>
          <div className="decisions">
            <div className="decision">
              <div className="d-k">the agent</div>
              <h3 className="d-h">A real agent, not a chatbot</h3>
              <p className="d-why">
                RAG over a policy and help center, plus deterministic tools: issue refund, check KYC,
                freeze card, open dispute, escalate. Support is about taking the right action, the way
                Fini frames its own agent Sophie.<Cite id="fini-ragless" />
              </p>
            </div>
            <div className="decision">
              <div className="d-k">ground truth</div>
              <h3 className="d-h">A versioned golden set</h3>
              <p className="d-why">
                Benchmark tickets with expected tools, policy constraints, and reference answers,
                including adversarial cases. Versioned like code so every change is gated against it.
                <Cite id="inspect" />
                <Cite id="abcd" />
                <Cite id="bitext" />
              </p>
            </div>
            <div className="decision">
              <div className="d-k">what to measure</div>
              <h3 className="d-h">Seven trust metrics</h3>
              <p className="d-why">
                Named after Fini&apos;s own framework. Hard rules get deterministic checks, soft
                qualities get an LLM judge. Resolution and policy adherence, never deflection.
                <Cite id="fini-trust" />
              </p>
            </div>
            <div className="decision">
              <div className="d-k">trust the judge</div>
              <h3 className="d-h">A calibrated LLM judge</h3>
              <p className="d-why">
                A stronger model grades a weaker one at temperature zero, then I measure how often the
                judge agrees with my own labels using Cohen&apos;s kappa. LLM judges carry position and
                verbosity bias, so you prove agreement, you do not assume it.<Cite id="llm-judge" />
                <Cite id="kappa" />
              </p>
            </div>
            <div className="decision">
              <div className="d-k">the top failure</div>
              <h3 className="d-h">Groundedness checks</h3>
              <p className="d-why">
                Decompose each answer into claims and verify every one against the retrieved context
                and tool results, because hallucinated refunds and policies are the number one support
                failure.<Cite id="ragas" />
              </p>
            </div>
            <div className="decision">
              <div className="d-k">improvement</div>
              <h3 className="d-h">A self-learning loop</h3>
              <p className="d-why">
                Every failure becomes a permanent regression case. That feedback loop is what separates
                a 95 percent agent from a 70 percent plateau, and it mirrors Fini&apos;s open-source
                Paramount tool.<Cite id="langchain-loop" />
                <Cite id="paramount" />
              </p>
            </div>
          </div>
          <p className="prose" style={{ marginTop: 16 }}>
            The same harness is designed to run against tau-bench, the strongest public benchmark for
            tool-using support agents, so it generalizes beyond this one scenario.<Cite id="taubench" />
          </p>
        </section>

        {/* EVIDENCE */}
        <section id="evidence" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">the evidence</div>
              <h2>The agent, measured</h2>
            </div>
            <div className="section-note">Toggle the version. Open any ticket to see exactly why it passed or failed.</div>
          </div>

          <div className="scorecard">
            <div className="card stat-card">
              <div className="toggle" role="tablist" aria-label="agent version">
                <button className={version === "v1" ? "on" : ""} onClick={() => setVersion("v1")}>
                  agent v1
                </button>
                <button className={version === "v2" ? "on" : ""} onClick={() => setVersion("v2")}>
                  agent v2
                </button>
              </div>
              <div className="bigstats">
                <div className="bigstat">
                  <div className="n" style={{ color: resolution < 0.9 ? "var(--bad)" : "var(--ink)" }}>
                    {pct(resolution)}
                    <small> resolved</small>
                  </div>
                  <div className="l">Resolution accuracy, judged against a reference answer.</div>
                </div>
                <div className="bigstat">
                  <div className="n" style={{ color: policy < 0.9 ? "var(--bad)" : "var(--ink)" }}>
                    {pct(policy)}
                    <small> on policy</small>
                  </div>
                  <div className="l">Policy adherence, the metric v2 quietly broke.</div>
                </div>
              </div>
            </div>
            <div className="card radar-card">
              <div className="rt">trust shape · agent {version}</div>
              <div style={{ width: "100%", height: 296 }}>
                <ResponsiveContainer>
                  <RadarChart data={radarData} outerRadius="70%">
                    <PolarGrid stroke="#e6e8df" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "#7b8170" }} />
                    <Radar
                      dataKey="score"
                      stroke="var(--lime-600)"
                      fill="var(--lime)"
                      fillOpacity={0.45}
                      strokeWidth={2}
                      animationDuration={500}
                    />
                    <Tooltip contentStyle={tipStyle} formatter={(v) => [`${v}%`, "score"]} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="kpis" style={{ marginTop: 16 }}>
            {names.map((name, i) => (
              <div className="kpi" key={name}>
                <div className="kpi-label">{prettyMetric(name)}</div>
                <div className="kpi-num">{pct(ov[name])}</div>
                <div className="kpi-bar">
                  <span style={{ width: pct(ov[name]), background: barColor(ov[name]), animationDelay: `${i * 55}ms` }} />
                </div>
              </div>
            ))}
          </div>

          <div className="heat-wrap" style={{ marginTop: 16 }}>
            <table className="heat">
              <thead>
                <tr>
                  <th className="intent">intent</th>
                  {names.map((n) => (
                    <th key={n}>{SHORT[n] ?? n}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.keys(intents).map((intent) => (
                  <tr key={intent}>
                    <td className="intent">{intent}</td>
                    {names.map((n) => (
                      <td key={n}>
                        <span className="cell" style={cellStyle(intents[intent][n])}>
                          {pct(intents[intent][n])}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: 18 }}>
            <CaseExplorer key={version} cases={run.cases} metrics={names} />
          </div>
        </section>

        {/* REGRESSION */}
        <section id="regression" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">the regression</div>
              <h2>Caught side by side, before it shipped</h2>
            </div>
            <div className="section-note">v2 looked better on average. The harness disagreed.</div>
          </div>

          <div className="reg-callout">
            <span className="mark">!</span>
            <div>
              On aggregate, v2 looked like an upgrade: warmer tone, more complete answers, more tool
              use. The harness caught what the average hid. <b>Policy adherence fell from{" "}
              {pct(ov1["policy_adherence"])} to {pct(ov2["policy_adherence"])}</b> and groundedness
              from {pct(ov1["groundedness"])} to {pct(ov2["groundedness"])}. Told to resolve
              everything itself and avoid handing off, the agent started cutting corners: opening a
              dispute before confirming the charge, freezing a card before verifying identity, and
              making claims it could not support.
            </div>
          </div>

          <div className="versus">
            <div className="vcol good">
              <div className="vlabel">
                <span>unrecognized charge · same ticket</span>
                <span className="ver">v1 · confirmed first</span>
              </div>
              <p>{disputeV1?.agent_text}</p>
            </div>
            <div className="vcol bad">
              <div className="vlabel">
                <span>unrecognized charge · same ticket</span>
                <span className="ver">v2 · skipped the check</span>
              </div>
              <p>{disputeV2?.agent_text}</p>
            </div>
          </div>

          {disputeV2?.metrics?.policy_adherence ? (
            <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 10, fontStyle: "italic" }}>
              Judge on v2: &ldquo;{disputeV2.metrics.policy_adherence.detail}&rdquo;
            </p>
          ) : null}

          <div className="reg-grid" style={{ marginTop: 18 }}>
            <div className="card chart-card">
              <div className="ct">v1 vs v2 on the metrics that moved</div>
              <div style={{ width: "100%", height: 250 }}>
                <ResponsiveContainer>
                  <BarChart data={regBarData} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eef0e8" vertical={false} />
                    <XAxis dataKey="metric" tick={{ fontSize: 11, fill: "#7b8170" }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#7b8170" }} />
                    <Tooltip contentStyle={tipStyle} formatter={(v) => [`${v}%`, ""]} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="v1" name="agent v1" fill="var(--lime)" radius={[4, 4, 0, 0]} animationDuration={600} />
                    <Bar dataKey="v2" name="agent v2" fill="var(--ink-soft)" radius={[4, 4, 0, 0]} animationDuration={600} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card chart-card">
              <div className="ct">is it real, or noise? (McNemar paired test)<Cite id="mcnemar" /></div>
              <table className="plain">
                <thead>
                  <tr>
                    <th>metric</th>
                    <th className="num">regressed</th>
                    <th className="num">improved</th>
                    <th className="num">p-value</th>
                  </tr>
                </thead>
                <tbody>
                  {reg.mcnemar
                    .filter((m) => m.regressed > 0 || m.improved > 0)
                    .map((m) => (
                      <tr key={m.metric}>
                        <td>{prettyMetric(m.metric)}</td>
                        <td className="num">{m.regressed}</td>
                        <td className="num">{m.improved}</td>
                        <td className={`num ${m.p_value < 0.1 ? "sig" : ""}`}>{m.p_value.toFixed(4)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
              <p style={{ fontSize: 12.5, color: "var(--muted)", marginTop: 10 }}>
                Same cases under both versions, so this paired test isolates real change from noise.
                Policy adherence regressed on 3 cases and improved on 0, a clean direction, but with 20
                cases the exact p is 0.25: directionally clear, not yet significant. That caveat is
                itself a finding, the slice needs a bigger golden set. Catching regressions this way is
                what Fini&apos;s own Test Suite does.<Cite id="paramount" />
              </p>
            </div>
          </div>
        </section>

        {/* ROI */}
        <section id="roi" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">what it is worth</div>
              <h2>From an eval table to a line item</h2>
            </div>
          </div>
          <div className="prose">
            <p>
              Solutions engineering is judged on outcomes, not dashboards. At an illustrative 100,000
              tickets a month, 80 percent automation, and a fully loaded human cost of 5 dollars a
              ticket against Fini&apos;s published 0.69 dollars per AI resolution, the agent saves
              roughly <strong>345,000 dollars a month</strong>.
            </p>
            <p>
              The caught regression has its own number. If refunds are 12 percent of volume and v2
              quietly drops refund resolution five points, that pushes about <strong>600 tickets a
              month</strong> back to humans, real money, avoided by gating the change on a per-category
              golden set instead of an aggregate. The exact figures come from a live run; the point is
              that the number exists and is defensible.
            </p>
          </div>
        </section>

        {/* ABOUT */}
        <section id="about" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">the honest part</div>
              <h2>Who built this, and the gap</h2>
            </div>
          </div>
          <div className="prose">
            <p>
              Straight version: the role asks for three or more years in a customer-facing technical
              role. I do not have that on paper. I graduated in 2024.
            </p>
            <p>
              What I do have is the work itself. I am the CTO of an AI startup shipping LLM systems to
              paying customers, so I live in prompts, evaluations, and production reliability every day.
              I built this so you could judge the work directly rather than the resume, because for this
              role the work is the only honest signal.
            </p>
            <p>
              <strong>The ask is twenty minutes.</strong> The full engine, 82 passing tests, the golden
              set, the agent, the judge, and the regression tooling are on GitHub, and the whole eval
              re-runs end to end on one command.
            </p>
          </div>
          <div className="cta-row">
            <a className="btn btn-primary" href="https://github.com/Umarfarook1/trustbench" target="_blank" rel="noreferrer">
              Read the code
            </a>
            <button className="btn btn-ghost" onClick={() => go("story")}>
              Back to top
            </button>
          </div>
        </section>

        {/* REFERENCES */}
        <section id="references" className="section">
          <div className="section-head">
            <div>
              <div className="kicker">sources</div>
              <h2>References</h2>
            </div>
            <div className="section-note">Real papers, tools, and Fini&apos;s own writing. Nothing invented.</div>
          </div>
          <div className="refs">
            {CITATIONS.map((c) => (
              <div className="ref" id={`ref-${c.id}`} key={c.id}>
                <span className="rn">[{c.n}]</span>
                <div>
                  <a className="rlink" href={c.url} target="_blank" rel="noreferrer">
                    {c.label}
                  </a>
                  <div className="src">{c.source}</div>
                  <div className="rnote">{c.note}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <footer className="foot">
          <span>Live run on Groq: agent openai/gpt-oss-20b, judged by meta-llama/llama-4-scout-17b. Real conversations, real scores.</span>
          <a href="https://github.com/Umarfarook1/trustbench" target="_blank" rel="noreferrer">
            github.com/Umarfarook1/trustbench
          </a>
        </footer>
      </main>
    </>
  );
}
