from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parent          # src/trustbench
PROJECT_ROOT = PACKAGE_ROOT.parents[1]                  # repo root

KB_DIR = PACKAGE_ROOT / "scenario" / "knowledge_base"
POLICY_PATH = PACKAGE_ROOT / "scenario" / "policy.md"

# Verify current model ids with client.models.list() before trusting these.
AGENT_MODEL = os.getenv("TRUSTBENCH_AGENT_MODEL", "gemini-2.5-flash")
JUDGE_MODEL = os.getenv("TRUSTBENCH_JUDGE_MODEL", "gemini-2.5-pro")
EMBED_MODEL = os.getenv("TRUSTBENCH_EMBED_MODEL", "gemini-embedding-001")

MAX_AGENT_STEPS = 6
RETRIEVAL_K = 3


def load_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in.")
    return key
