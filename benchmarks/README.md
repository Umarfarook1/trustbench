# External benchmark anchor (tau-bench)

Status: documented, not yet implemented. This is the one deliberately deferred stretch item.

## Why it belongs here

The Northwind scenario proves the harness works end to end, but it is a scenario the author
built. To show the harness generalizes beyond a self-authored toy, the same metrics should be
run against a respected public benchmark. tau-bench (Sierra Research) is the strongest fit: it
evaluates tool-using support agents against policy documents in retail and airline domains,
with a `pass^k` reliability metric, and state-of-the-art models still score under fifty percent
on it. That difficulty is a feature here: it produces a rich set of real failures to classify
and attribute.

## The adapter shape

TrustBench is already structured for this. tau-bench provides its own environment, user
simulator, and tasks, so the integration is a thin adapter, not a rewrite:

1. Wrap a tau-bench task as something with a `ticket` (the initial user goal) and a way to run
   the agent loop inside tau-bench's environment, returning a transcript and tool calls.
2. Map the tau-bench outcome onto an `AgentResult` and `AgentTrace` so the existing metrics,
   failure taxonomy, and root-cause attribution apply unchanged.
3. Report tau-bench's native `pass^1` and `pass^k` alongside the seven trust metrics, so the
   numbers are comparable to published baselines.

## How to add it

- `pip install tau-bench` (or vendor the repo from sierra-research/tau-bench).
- Add `benchmarks/taubench_adapter.py` implementing the `Agent` protocol from
  `trustbench.evals.runner` over a tau-bench environment.
- Add `benchmarks/run_taubench.py` to score and print `pass^k` plus the trust metrics.

It is left as documented rather than half-built on purpose: shipping a broken integration would
be worse than a clear plan for a real one.
