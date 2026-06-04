from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parent          # src/trustbench
PROJECT_ROOT = PACKAGE_ROOT.parents[1]                  # repo root

KB_DIR = PACKAGE_ROOT / "scenario" / "knowledge_base"
POLICY_PATH = PACKAGE_ROOT / "scenario" / "policy.md"

DATA_DIR = PROJECT_ROOT / "data"
GOLDEN_DIR = DATA_DIR / "golden"
RESULTS_DIR = DATA_DIR / "results"

# Verify current model ids with client.models.list() before trusting these.
AGENT_MODEL = os.getenv("TRUSTBENCH_AGENT_MODEL", "gemini-2.5-flash")
JUDGE_MODEL = os.getenv("TRUSTBENCH_JUDGE_MODEL", "gemini-2.5-pro")
EMBED_MODEL = os.getenv("TRUSTBENCH_EMBED_MODEL", "gemini-embedding-001")

# Groq path (OpenAI-compatible). Used when Gemini access is unavailable. A small, cheap
# agent (where failures are part of the point) graded by a larger, different-family judge,
# so the judge is not grading itself. Chosen to fit Groq free-tier daily token limits:
# llama-3.1-8b-instant has a 500k/day budget vs only 100k/day for the 70b model.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_AGENT_MODEL = os.getenv("TRUSTBENCH_GROQ_AGENT_MODEL", "openai/gpt-oss-20b")
GROQ_JUDGE_MODEL = os.getenv(
    "TRUSTBENCH_GROQ_JUDGE_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)

MAX_AGENT_STEPS = 6
RETRIEVAL_K = 3


def load_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in.")
    return key


def load_groq_key() -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env.")
    return key
