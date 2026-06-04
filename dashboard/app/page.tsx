import CaseExplorer from "./CaseExplorer";
import { byIntent, caseById, metricNames, overall, prettyMetric } from "@/lib/aggregate";
import { loadRegression, loadRun, loadRunV2 } from "@/lib/data";

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

function barColor(s: number): string {
  if (s >= 0.9) return "var(--good)";
  if (s >= 0.7) return "var(--ok)";
  return "var(--bad)";
}

function cellStyle(s: number) {
  if (s >= 0.9) return { background: "var(--good-bg)", color: "var(--good)" };
  if (s >= 0.7) return { background: "var(--ok-bg)", color: "var(--ok)" };
  return { background: "var(--bad-bg)", color: "var(--bad)" };
}

export default function Page() {
  const run = loadRun();
  const runV2 = loadRunV2();
  const reg = loadRegression();
  const names = metricNames(run);
  const ov = overall(run);
  const intents = byIntent(run);

  const cryptoV1 = caseById(run, "refund_crypto_refused");
  const cryptoV2 = caseById(runV2, "refund_crypto_refused");
  const changed = reg.overall.filter((d) => Math.abs(d.delta) > 0.001);
  const topSlice = reg.regressed_slices[0];

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            Trust<em>Bench</em>
          </span>
          <span className="brand-sub">agent trust instrument · Northwind neobank</span>
        </div>
        <span className="pill pill-sample">sample data</span>
      </header>

      <section className="hero">
        <div className="eyebrow">evaluation · tracing · regression</div>
        <h1>
          We tested a support agent on {run.cases.length} real scenarios, and watched a
          regression try to <em>slip through</em>.
        </h1>
        <p>
          A Sophie-style agent for a fictional neobank, scored on seven trust dimensions with a
          calibrated LLM judge, every answer traced to the tools it called and the policy it read.
          Click any ticket below to see exactly why it passed or failed.
        </p>
      </section>

      <div className="headline">
        <div>
          <div className="big">
            {pct(ov["resolution_accuracy"] ?? 0)}
            <small> resolved</small>
          </div>
          <div className="cap">Resolution accuracy across all {run.cases.length} cases, judged against a reference.</div>
        </div>
        <div className="rule" />
        <div>
          <div className="big">
            {pct(ov["policy_adherence"] ?? 0)}
            <small> on policy</small>
          </div>
          <div className="cap">Policy and guardrail adherence, the metric the v2 regression quietly broke.</div>
        </div>
        <div className="rule" />
        <div>
          <div className="big">
            {reg.regressed_slices.length}
            <small> regressed slices</small>
          </div>
          <div className="cap">Category-level regressions caught comparing agent v1 to v2.</div>
        </div>
      </div>

      <section className="section">
        <div className="section-head">
          <div>
            <div className="kicker">07 dimensions</div>
            <h2>Trust metrics</h2>
          </div>
          <div className="section-note">
            Deterministic checks for hard rules, a calibrated LLM judge for the soft ones.
          </div>
        </div>
        <div className="kpis">
          {names.map((name) => (
            <div className="kpi" key={name}>
              <div className="kpi-label">{prettyMetric(name)}</div>
              <div className="kpi-num">{pct(ov[name])}</div>
              <div className="kpi-bar">
                <span style={{ width: pct(ov[name]), background: barColor(ov[name]) }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <div className="kicker">slice by slice</div>
            <h2>Scores by ticket category</h2>
          </div>
          <div className="section-note">An aggregate hides where the agent is weak. A per-category view does not.</div>
        </div>
        <div className="heat-wrap">
          <table className="heat">
            <thead>
              <tr>
                <th className="intent">intent</th>
                {names.map((n) => (
                  <th key={n}>{prettyMetric(n)}</th>
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
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <div className="kicker">why did it do that</div>
            <h2>Case explorer</h2>
          </div>
          <div className="section-note">Every conversation, the tools it ran, and the judge&apos;s reasoning.</div>
        </div>
        <CaseExplorer cases={run.cases} metrics={names} />
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <div className="kicker">v2 vs v1</div>
            <h2>Regression incident</h2>
          </div>
          <div className="section-note">Overall looked fine. One category did not.</div>
        </div>

        {topSlice ? (
          <div className="reg-callout">
            <span className="mark">!</span>
            <div>
              The v2 prompt was warmer and scored flat-to-better overall, but <b>{topSlice.intent}</b>{" "}
              tickets dropped {Math.round(Math.abs(topSlice.delta) * 100)} points on{" "}
              {prettyMetric(topSlice.metric)} ({pct(topSlice.baseline)} to {pct(topSlice.candidate)}).
              Root cause: v2 silently dropped the tool-confirmation guardrail from the system prompt,
              so the agent began claiming refunds that policy forbids.
            </div>
          </div>
        ) : null}

        {cryptoV1 && cryptoV2 ? (
          <div className="versus">
            <div className="vcol good">
              <div className="vlabel">
                <span>refund_crypto_refused</span>
                <span className="ver">agent v1 · held policy</span>
              </div>
              <p>{cryptoV1.agent_text}</p>
            </div>
            <div className="vcol bad">
              <div className="vlabel">
                <span>refund_crypto_refused</span>
                <span className="ver">agent v2 · broke policy</span>
              </div>
              <p>{cryptoV2.agent_text}</p>
            </div>
          </div>
        ) : null}

        <table className="plain">
          <thead>
            <tr>
              <th>metric (moved)</th>
              <th className="num">v1</th>
              <th className="num">v2</th>
              <th className="num">delta</th>
            </tr>
          </thead>
          <tbody>
            {changed.map((d) => (
              <tr key={d.metric}>
                <td>{prettyMetric(d.metric)}</td>
                <td className="num">{pct(d.baseline)}</td>
                <td className="num">{pct(d.candidate)}</td>
                <td className={`num ${d.delta < 0 ? "delta-neg" : "delta-pos"}`}>
                  {d.delta > 0 ? "+" : ""}
                  {Math.round(d.delta * 100)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <table className="plain" style={{ marginTop: 18 }}>
          <thead>
            <tr>
              <th>McNemar (paired pass/fail)</th>
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
      </section>

      <footer className="foot">
        <span>
          Sample data, generated from the real eval schema. Swap in a live run to see real numbers.
        </span>
        <a href="https://github.com/Umarfarook1/trustbench" target="_blank" rel="noreferrer">
          github.com/Umarfarook1/trustbench
        </a>
      </footer>
    </main>
  );
}
