from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RetrievalHit(BaseModel):
    doc_id: str
    title: str
    score: float


class ToolSpan(BaseModel):
    name: str
    args: dict[str, Any]
    result: dict[str, Any]


class AgentTrace(BaseModel):
    ticket: str
    agent_version: str = "v1"
    policy_in_context: bool = False
    retrieval_query: str = ""
    hits: list[RetrievalHit] = Field(default_factory=list)
    steps: list[ToolSpan] = Field(default_factory=list)
    final_response: str = ""
    exceeded_budget: bool = False
