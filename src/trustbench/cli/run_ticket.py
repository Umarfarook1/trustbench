from __future__ import annotations

import argparse
import json

from trustbench.agent.support_agent import SupportAgent
from trustbench.config import AGENT_MODEL, KB_DIR, POLICY_PATH, load_api_key
from trustbench.llm.gemini_client import GeminiClient
from trustbench.retrieval.gemini_embedder import GeminiEmbedder
from trustbench.retrieval.index import KnowledgeIndex, load_knowledge_base
from trustbench.scenario.state import seed_state
from trustbench.scenario.tools import ToolRegistry


def build_agent() -> SupportAgent:
    api_key = load_api_key()
    embedder = GeminiEmbedder(api_key)
    index = KnowledgeIndex(embedder)
    index.build(load_knowledge_base(KB_DIR))
    return SupportAgent(
        client=GeminiClient(api_key, AGENT_MODEL),
        index=index,
        state=seed_state(),
        registry=ToolRegistry(),
        policy_text=POLICY_PATH.read_text(encoding="utf-8"),
        version="v1",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one support ticket through the agent.")
    parser.add_argument("ticket", help="The customer message.")
    args = parser.parse_args()

    agent = build_agent()
    result = agent.handle(args.ticket)

    print("\n=== AGENT REPLY ===")
    print(result.text)
    print("\n=== TRACE ===")
    print(json.dumps(result.trace.model_dump(), indent=2))


if __name__ == "__main__":
    main()
