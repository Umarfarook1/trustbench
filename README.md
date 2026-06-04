# TrustBench

A production-readiness harness for AI support agents. Built around a fictional
neobank, "Northwind". It runs a support agent, scores it against a versioned
golden set using Fini-style Trust Metrics, catches regressions by ticket category,
and packages the result with an onboarding playbook and ROI writeup.

Status: Phase 1 (working agent). See `docs/superpowers/plans/`.

## Setup

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -e ".[dev]"
    copy .env.example .env          # then add your GEMINI_API_KEY

## Test

    pytest
