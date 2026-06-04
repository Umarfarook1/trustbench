import {
  byIntent,
  loadRegression,
  loadRun,
  metricNames,
  overall,
  prettyMetric,
} from "@/lib/aggregate";

function pct(x: number): string {
  return `${(x * 100).toFixed(0)}%`;
}

function tone(score: number): string {
  if (score >= 0.9) return "tone-good";
  if (score >= 0.7) return "tone-ok";
  return "tone-bad";
}

function barColor(score: number): string {
  if (score >= 0.9) return "var(--good)";
  if (score >= 0.7) return "var(--ok)";
  return "var(--bad)";
}

export default function Page() {
  const run = loadRun();
  const reg = loadRegression();
  const ov = overall(run);
  const names = metricNames(run);
  const intents = byIntent(run);

  const sigRegressions = reg.mcnemar.filter((m) => m.regressed > m.improved && m.p_value < 0.1);

  return (
    <main className="wrap">
      <div className="header">
        <div>
          <div className="wordmark">
            TrustBench<span className="dot">.</span>
          </div>
          <div className="subtitle">
            Northwind support agent · run {run.run_label} · agent {run.agent_version}
          </div>
        </div>
        <span className="badge">sample data</span>
      </div>

      <section className="section">
        <h2>Trust metrics (overall)</h2>
        <div className="grid">
          {names.map((name) => (
            <div className="card" key={name}>
              <div className="label">{prettyMetric(name)}</div>
              <div className="value">{pct(ov[name])}</div>
              <div className="bar">
                <div
                  className="bar-fill"
                  style={{ width: pct(ov[name]), background: barColor(ov[name]) }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>Scores by ticket category</h2>
        <table className="heat">
          <thead>
            <tr>
              <th className="intent">Intent</th>
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
                    <div className={`cell ${tone(intents[intent][n])}`}>
                      {pct(intents[intent][n])}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="section">
        <h2>
          Regression incident · {reg.candidate_label} vs {reg.baseline_label}
        </h2>
        <div className="panel">
          {reg.regressed_slices.length > 0 ? (
            <div className="callout">
              {reg.regressed_slices.length} slice
              {reg.regressed_slices.length > 1 ? "s" : ""} regressed. The overall numbers can look
              flat, but {reg.regressed_slices[0].intent} tickets dropped on{" "}
              {prettyMetric(reg.regressed_slices[0].metric)}. Root cause: the v2 prompt dropped the
              tool-confirmation guardrail.
            </div>
          ) : (
            <div>No slice regressed beyond threshold.</div>
          )}

          <table className="plain">
            <thead>
              <tr>
                <th>Intent</th>
                <th>Metric</th>
                <th>Baseline</th>
                <th>Candidate</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              {reg.regressed_slices.map((s, i) => (
                <tr key={i}>
                  <td>{s.intent}</td>
                  <td>{prettyMetric(s.metric)}</td>
                  <td>{pct(s.baseline)}</td>
                  <td>{pct(s.candidate)}</td>
                  <td className="delta-neg">{(s.delta * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>

          <table className="plain">
            <thead>
              <tr>
                <th>Metric (McNemar)</th>
                <th>Regressed</th>
                <th>Improved</th>
                <th>p-value</th>
              </tr>
            </thead>
            <tbody>
              {sigRegressions.length > 0 ? (
                sigRegressions.map((m, i) => (
                  <tr key={i}>
                    <td>{prettyMetric(m.metric)}</td>
                    <td>{m.regressed}</td>
                    <td>{m.improved}</td>
                    <td className="sig">{m.p_value.toFixed(4)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4}>No statistically notable regressions in this sample.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="foot">
        Sample data generated from the real EvalRun schema via
        scripts/make_sample_dashboard_data.py. Replace data/sample-run.json and
        data/sample-regression.json with a live run to see real numbers.
      </div>
    </main>
  );
}
