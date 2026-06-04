# TrustBench Phase 1: Scenario + Working Support Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Gemini-powered support agent for a fictional neobank ("Northwind") that retrieves from a knowledge base, calls deterministic mocked tools (refunds, KYC, etc.), and emits a structured trace of everything it did.

**Architecture:** The agent loop runs against a small `LLMClient` protocol so all decision logic is testable with a scripted fake client (no live API needed for tests). A real `GeminiClient` adapter translates that protocol to the `google-genai` SDK. Retrieval runs against an injectable `Embedder` protocol (fake in tests, Gemini in production). Tools mutate an in-memory `NorthwindState` and return structured success/failure dicts, so later phases can detect policy violations by comparing tool results to the agent's words.

**Tech Stack:** Python 3.11+, `google-genai`, `numpy`, `pydantic` v2, `pytest`, `python-dotenv`. Src layout, editable install.

**Ownership gate (end of phase):** Umar writes five plain-English sentences explaining (1) how the agent loop decides to call a tool vs reply, (2) why the agent depends on `LLMClient` instead of the SDK directly, (3) how retrieval picks articles, (4) what the trace records and why, (5) how a policy violation would become detectable. If any can't be written, simplify before Phase 2.

---

## File structure (created in this phase)

```
trustbench/
  pyproject.toml                         # project + pytest config
  .gitignore
  .env.example                           # GEMINI_API_KEY=
  README.md                              # short stub, expanded in Phase 4
  src/trustbench/
    __init__.py
    config.py                            # model ids, paths, constants, api key loader
    llm/
      __init__.py
      types.py                           # ToolCall, ToolResult, Message, ToolSpec, LLMResponse
      base.py                            # LLMClient protocol
      fakes.py                           # ScriptedClient for tests
      gemini_client.py                   # real google-genai adapter
    scenario/
      __init__.py
      state.py                           # Account/Transaction/Card/Subscription/NorthwindState + seed_state
      tools.py                           # tool functions, TOOL_SPECS, ToolRegistry
      policy.md                          # the policy document (data)
      knowledge_base/                    # markdown KB articles (data)
        refunds.md
        kyc-verification.md
        card-management.md
        disputes-and-chargebacks.md
    retrieval/
      __init__.py
      embedder.py                        # Embedder protocol
      gemini_embedder.py                 # real Gemini embedder
      index.py                           # Doc, load_knowledge_base, KnowledgeIndex
    agent/
      __init__.py
      trace.py                           # pydantic trace models
      prompts.py                         # SYSTEM_PROMPT_V1 + build_system
      support_agent.py                   # SupportAgent, AgentResult, format_context
    cli/
      __init__.py
      run_ticket.py                      # manual end-to-end smoke runner (live API)
  tests/
    conftest.py                          # FakeEmbedder + shared fixtures
    test_tools.py
    test_retrieval.py
    test_trace.py
    test_agent.py
```

---

## Task 0: Repo scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/trustbench/__init__.py` (empty)

- [ ] **Step 1: Initialize the repo**

Run from `C:\Users\Umar\Documents\Github_personal\trustbench`:
```bash
git init
```
Expected: "Initialized empty Git repository".

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "trustbench"
version = "0.1.0"
description = "A production-readiness harness for AI support agents"
requires-python = ">=3.11"
dependencies = [
    "google-genai>=1.0",
    "numpy>=1.26",
    "pydantic>=2.6",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/trustbench"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
*.sqlite
.DS_Store
# dashboard (Phase 4)
node_modules/
.next/
dist/
```

- [ ] **Step 4: Write `.env.example`**

```dotenv
# Copy to .env and fill in. Get a key at https://aistudio.google.com/apikey
GEMINI_API_KEY=
```

- [ ] **Step 5: Write `README.md` stub**

```markdown
# TrustBench

A production-readiness harness for AI support agents. Built around a fictional
neobank, "Northwind". It runs a support agent, scores it against a versioned
golden set using Fini-style Trust Metrics, catches regressions by ticket category,
and packages the result with an onboarding playbook and ROI writeup.

Status: Phase 1 (working agent). See `docs/superpowers/plans/`.

## Setup

    python -m venv .venv
    .venv\Scripts\activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
    pip install -e ".[dev]"
    copy .env.example .env          # then add your GEMINI_API_KEY

## Test

    pytest
```

- [ ] **Step 6: Create the package marker**

Create `src/trustbench/__init__.py` as an empty file.

- [ ] **Step 7: Create the virtualenv and install**

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```
Expected: installs `trustbench` plus deps without error.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore .env.example README.md src/trustbench/__init__.py
git commit -m "chore: scaffold trustbench python project"
```

---

## Task 1: LLM abstraction (types, protocol, fake)

This is the seam that makes the agent testable. Define our own small types so the
agent loop never touches the SDK directly.

**Files:**
- Create: `src/trustbench/llm/__init__.py` (empty)
- Create: `src/trustbench/llm/types.py`
- Create: `src/trustbench/llm/base.py`
- Create: `src/trustbench/llm/fakes.py`
- Test: `tests/test_agent.py` (start it here, extend in Task 7)

- [ ] **Step 1: Write the failing test**

Create `tests/test_agent.py`:
```python
from trustbench.llm.types import ToolCall, LLMResponse


def test_llmresponse_is_final_when_no_tool_calls():
    resp = LLMResponse(text="Hi there")
    assert resp.is_final is True


def test_llmresponse_not_final_when_tool_calls_present():
    resp = LLMResponse(tool_calls=[ToolCall(name="issue_refund", args={"transaction_id": "t1"})])
    assert resp.is_final is False
    assert resp.text is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'trustbench.llm'`.

- [ ] **Step 3: Write `src/trustbench/llm/types.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class ToolResult:
    name: str
    result: dict[str, Any]


@dataclass
class ToolSpec:
    """A tool declaration handed to the model."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema object


@dataclass
class Message:
    """One turn in the agent conversation, in our own neutral form."""
    role: str  # "user", "model", or "tool"
    text: str | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None


@dataclass
class LLMResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def is_final(self) -> bool:
        return not self.tool_calls
```

- [ ] **Step 4: Write `src/trustbench/llm/base.py`**

```python
from __future__ import annotations

from typing import Protocol

from trustbench.llm.types import LLMResponse, Message, ToolSpec


class LLMClient(Protocol):
    """Anything the agent can talk to: real Gemini, or a scripted fake."""

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResponse:
        ...
```

- [ ] **Step 5: Write `src/trustbench/llm/fakes.py`**

```python
from __future__ import annotations

from trustbench.llm.types import LLMResponse, Message, ToolSpec


class ScriptedClient:
    """Returns pre-canned responses in order. Records every call for assertions."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self.calls: list[tuple[str, list[Message], list[ToolSpec]]] = []

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResponse:
        self.calls.append((system, list(messages), list(tools)))
        if not self._responses:
            raise AssertionError("ScriptedClient ran out of scripted responses")
        return self._responses.pop(0)
```

- [ ] **Step 6: Create the empty package marker**

Create `src/trustbench/llm/__init__.py` as an empty file.

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_agent.py -v`
Expected: 2 passed.

- [ ] **Step 8: Commit**

```bash
git add src/trustbench/llm tests/test_agent.py
git commit -m "feat: add llm abstraction (types, client protocol, scripted fake)"
```

---

## Task 2: Scenario state and tools

Deterministic tools over an in-memory state. Tools never raise on business failure;
they return `{"ok": False, "reason": ...}` so failures are inspectable.

**Files:**
- Create: `src/trustbench/scenario/__init__.py` (empty)
- Create: `src/trustbench/scenario/state.py`
- Create: `src/trustbench/scenario/tools.py`
- Test: `tests/test_tools.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tools.py`:
```python
import pytest

from trustbench.scenario.state import seed_state
from trustbench.scenario.tools import ToolRegistry, TOOL_SPECS


@pytest.fixture
def state():
    return seed_state()


@pytest.fixture
def registry():
    return ToolRegistry()


def test_lookup_existing_transaction(state, registry):
    out = registry.execute("lookup_transaction", state, {"transaction_id": "txn_settled_refundable"})
    assert out["found"] is True
    assert out["transaction"]["status"] == "settled"


def test_lookup_missing_transaction(state, registry):
    out = registry.execute("lookup_transaction", state, {"transaction_id": "nope"})
    assert out["found"] is False


def test_refund_succeeds_on_refundable_settled_txn(state, registry):
    out = registry.execute("issue_refund", state, {"transaction_id": "txn_settled_refundable"})
    assert out["ok"] is True
    assert state.transactions["txn_settled_refundable"].status == "refunded"


def test_refund_blocked_when_not_refundable(state, registry):
    out = registry.execute("issue_refund", state, {"transaction_id": "txn_settled_nonrefundable"})
    assert out["ok"] is False
    assert out["reason"] == "not_refundable_per_policy"


def test_refund_blocked_when_pending(state, registry):
    out = registry.execute("issue_refund", state, {"transaction_id": "txn_pending"})
    assert out["ok"] is False
    assert out["reason"] == "not_settled"


def test_freeze_card_sets_flag(state, registry):
    out = registry.execute("freeze_card", state, {"card_id": "card_main"})
    assert out["ok"] is True
    assert state.cards["card_main"].frozen is True


def test_check_kyc_status(state, registry):
    out = registry.execute("check_kyc_status", state, {"account_id": "acct_1"})
    assert out["kyc_status"] == "verified"


def test_pause_subscription(state, registry):
    out = registry.execute("pause_subscription", state, {"subscription_id": "sub_pro"})
    assert out["ok"] is True
    assert state.subscriptions["sub_pro"].active is False


def test_unknown_tool_returns_structured_error(state, registry):
    out = registry.execute("nonexistent", state, {})
    assert out["ok"] is False
    assert out["reason"] == "unknown_tool"


def test_bad_arguments_return_structured_error(state, registry):
    out = registry.execute("issue_refund", state, {"wrong_arg": "x"})
    assert out["ok"] is False
    assert out["reason"] == "bad_arguments"


def test_every_tool_spec_has_a_registered_callable(registry):
    for spec in TOOL_SPECS:
        assert spec.name in registry.names()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'trustbench.scenario'`.

- [ ] **Step 3: Write `src/trustbench/scenario/state.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Account:
    id: str
    name: str
    email: str
    kyc_status: str  # "verified", "pending", "failed"


@dataclass
class Transaction:
    id: str
    account_id: str
    amount_cents: int
    merchant: str
    status: str        # "settled", "pending", "refunded"
    refundable: bool


@dataclass
class Card:
    id: str
    account_id: str
    last4: str
    frozen: bool = False


@dataclass
class Subscription:
    id: str
    account_id: str
    plan: str
    active: bool = True


@dataclass
class NorthwindState:
    accounts: dict[str, Account] = field(default_factory=dict)
    transactions: dict[str, Transaction] = field(default_factory=dict)
    cards: dict[str, Card] = field(default_factory=dict)
    subscriptions: dict[str, Subscription] = field(default_factory=dict)


def seed_state() -> NorthwindState:
    """A fresh, deterministic fixture for one customer account."""
    state = NorthwindState()
    state.accounts["acct_1"] = Account(
        id="acct_1", name="Priya Nair", email="priya@example.com", kyc_status="verified"
    )
    state.transactions["txn_settled_refundable"] = Transaction(
        id="txn_settled_refundable", account_id="acct_1", amount_cents=4200,
        merchant="Blue Bottle Coffee", status="settled", refundable=True,
    )
    state.transactions["txn_settled_nonrefundable"] = Transaction(
        id="txn_settled_nonrefundable", account_id="acct_1", amount_cents=999900,
        merchant="Crypto Exchange XYZ", status="settled", refundable=False,
    )
    state.transactions["txn_pending"] = Transaction(
        id="txn_pending", account_id="acct_1", amount_cents=1500,
        merchant="Corner Store", status="pending", refundable=True,
    )
    state.cards["card_main"] = Card(
        id="card_main", account_id="acct_1", last4="4242", frozen=False
    )
    state.subscriptions["sub_pro"] = Subscription(
        id="sub_pro", account_id="acct_1", plan="Northwind Pro", active=True
    )
    return state
```

- [ ] **Step 4: Write `src/trustbench/scenario/tools.py`**

```python
from __future__ import annotations

from typing import Any, Callable

from trustbench.llm.types import ToolSpec
from trustbench.scenario.state import NorthwindState


def lookup_transaction(state: NorthwindState, transaction_id: str) -> dict[str, Any]:
    txn = state.transactions.get(transaction_id)
    if txn is None:
        return {"found": False}
    return {
        "found": True,
        "transaction": {
            "id": txn.id,
            "amount_cents": txn.amount_cents,
            "merchant": txn.merchant,
            "status": txn.status,
            "refundable": txn.refundable,
        },
    }


def issue_refund(state: NorthwindState, transaction_id: str) -> dict[str, Any]:
    txn = state.transactions.get(transaction_id)
    if txn is None:
        return {"ok": False, "reason": "transaction_not_found"}
    if not txn.refundable:
        return {"ok": False, "reason": "not_refundable_per_policy"}
    if txn.status != "settled":
        return {"ok": False, "reason": "not_settled"}
    txn.status = "refunded"
    return {"ok": True, "refunded_cents": txn.amount_cents}


def check_kyc_status(state: NorthwindState, account_id: str) -> dict[str, Any]:
    acct = state.accounts.get(account_id)
    if acct is None:
        return {"found": False}
    return {"found": True, "kyc_status": acct.kyc_status}


def pause_subscription(state: NorthwindState, subscription_id: str) -> dict[str, Any]:
    sub = state.subscriptions.get(subscription_id)
    if sub is None:
        return {"ok": False, "reason": "subscription_not_found"}
    sub.active = False
    return {"ok": True, "plan": sub.plan, "active": sub.active}


def update_account_details(
    state: NorthwindState, account_id: str, email: str | None = None
) -> dict[str, Any]:
    acct = state.accounts.get(account_id)
    if acct is None:
        return {"ok": False, "reason": "account_not_found"}
    if email is not None:
        acct.email = email
    return {"ok": True, "email": acct.email}


def freeze_card(state: NorthwindState, card_id: str) -> dict[str, Any]:
    card = state.cards.get(card_id)
    if card is None:
        return {"ok": False, "reason": "card_not_found"}
    card.frozen = True
    return {"ok": True, "last4": card.last4, "frozen": card.frozen}


def open_dispute(state: NorthwindState, transaction_id: str, reason: str) -> dict[str, Any]:
    txn = state.transactions.get(transaction_id)
    if txn is None:
        return {"ok": False, "reason": "transaction_not_found"}
    return {"ok": True, "dispute_id": f"disp_{txn.id}", "status": "open"}


def escalate_to_human(state: NorthwindState, summary: str) -> dict[str, Any]:
    return {"ok": True, "escalated": True, "summary": summary}


TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="lookup_transaction",
        description="Look up a transaction by id to see amount, merchant, status, and refund eligibility.",
        parameters={
            "type": "object",
            "properties": {"transaction_id": {"type": "string"}},
            "required": ["transaction_id"],
        },
    ),
    ToolSpec(
        name="issue_refund",
        description="Issue a refund for a transaction. Only succeeds if the transaction is settled and refundable per policy.",
        parameters={
            "type": "object",
            "properties": {"transaction_id": {"type": "string"}},
            "required": ["transaction_id"],
        },
    ),
    ToolSpec(
        name="check_kyc_status",
        description="Check an account's KYC/identity verification status.",
        parameters={
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
        },
    ),
    ToolSpec(
        name="pause_subscription",
        description="Pause an active subscription.",
        parameters={
            "type": "object",
            "properties": {"subscription_id": {"type": "string"}},
            "required": ["subscription_id"],
        },
    ),
    ToolSpec(
        name="update_account_details",
        description="Update account details such as email.",
        parameters={
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["account_id"],
        },
    ),
    ToolSpec(
        name="freeze_card",
        description="Freeze a card to block further spending.",
        parameters={
            "type": "object",
            "properties": {"card_id": {"type": "string"}},
            "required": ["card_id"],
        },
    ),
    ToolSpec(
        name="open_dispute",
        description="Open a dispute/chargeback on a transaction.",
        parameters={
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["transaction_id", "reason"],
        },
    ),
    ToolSpec(
        name="escalate_to_human",
        description="Escalate the conversation to a human agent with a short summary.",
        parameters={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    ),
]

_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "lookup_transaction": lookup_transaction,
    "issue_refund": issue_refund,
    "check_kyc_status": check_kyc_status,
    "pause_subscription": pause_subscription,
    "update_account_details": update_account_details,
    "freeze_card": freeze_card,
    "open_dispute": open_dispute,
    "escalate_to_human": escalate_to_human,
}


class ToolRegistry:
    """Executes tools by name against a state, returning structured results."""

    def __init__(self, handlers: dict[str, Callable[..., dict[str, Any]]] | None = None):
        self._handlers = handlers if handlers is not None else dict(_HANDLERS)

    def names(self) -> list[str]:
        return list(self._handlers.keys())

    def execute(self, name: str, state: NorthwindState, args: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            return {"ok": False, "reason": "unknown_tool"}
        try:
            return handler(state, **args)
        except TypeError:
            return {"ok": False, "reason": "bad_arguments"}
```

- [ ] **Step 5: Create the empty package marker**

Create `src/trustbench/scenario/__init__.py` as an empty file.

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/trustbench/scenario/state.py src/trustbench/scenario/tools.py src/trustbench/scenario/__init__.py tests/test_tools.py
git commit -m "feat: add northwind state and deterministic tool registry"
```

---

## Task 3: Policy document and knowledge base content

This is content, not logic. Author the policy and a starter set of KB articles in a
consistent format. More articles get added in Phase 2 when the golden set needs them.

**Files:**
- Create: `src/trustbench/scenario/policy.md`
- Create: `src/trustbench/scenario/knowledge_base/refunds.md`
- Create: `src/trustbench/scenario/knowledge_base/kyc-verification.md`
- Create: `src/trustbench/scenario/knowledge_base/card-management.md`
- Create: `src/trustbench/scenario/knowledge_base/disputes-and-chargebacks.md`

- [ ] **Step 1: Write `src/trustbench/scenario/policy.md`**

```markdown
# Northwind Support Agent Policy

You are Sophie, the AI support agent for Northwind, a consumer neobank. Follow these
rules exactly. When a rule and a customer request conflict, the rule wins.

## Refunds
- A refund may only be issued when the transaction is both SETTLED and marked
  refundable. Use `issue_refund`; if it returns `ok: false`, do NOT tell the customer
  the refund was issued. Explain the reason instead.
- Never promise a refund timeline beyond "5 to 10 business days".
- Transactions to crypto exchanges are non-refundable. Do not override this.

## Identity and KYC
- For any request to move money, change account ownership, or unfreeze a card, first
  confirm KYC status with `check_kyc_status`. If status is not "verified", escalate.
- Never reveal full card numbers, full account numbers, or another customer's data.

## Cards
- If a customer reports a lost or stolen card, freeze it immediately with `freeze_card`
  before anything else.

## Escalation
- Escalate with `escalate_to_human` when: the customer is reporting fraud over a
  threshold you cannot verify, the request requires an action no tool supports, KYC is
  not verified for a sensitive action, or the customer explicitly asks for a human.

## Tone
- Be warm, brief, and concrete. Acknowledge frustration once, then solve the problem.
- Never speculate about Northwind internal systems or make commitments policy forbids.
```

- [ ] **Step 2: Write `src/trustbench/scenario/knowledge_base/refunds.md`**

```markdown
# Refunds at Northwind

Northwind can refund eligible card transactions back to the original payment method.

A transaction is eligible when it has settled (not pending) and the merchant category
allows refunds. Refunds typically appear in 5 to 10 business days.

Crypto purchases and gambling transactions are not refundable. Pending transactions
cannot be refunded until they settle; ask the customer to wait until settlement.

To request a refund, the customer should provide the transaction id or the merchant
name and amount so the agent can locate it.
```

- [ ] **Step 3: Write `src/trustbench/scenario/knowledge_base/kyc-verification.md`**

```markdown
# Identity Verification (KYC)

Northwind verifies customer identity before sensitive actions like large transfers,
changing account ownership, or unfreezing a card.

KYC status can be "verified", "pending", or "failed". Customers with pending or failed
KYC must complete verification in the app under Settings, Identity, before sensitive
actions can proceed. Support agents cannot bypass KYC.
```

- [ ] **Step 4: Write `src/trustbench/scenario/knowledge_base/card-management.md`**

```markdown
# Card Management

Customers can freeze and unfreeze cards from the app, or ask support to freeze a card.

If a card is lost or stolen, freeze it immediately, then order a replacement. A frozen
card declines all new charges. Recurring subscriptions tied to the card will also fail
while it is frozen.

Unfreezing a card is a sensitive action and requires verified KYC.
```

- [ ] **Step 5: Write `src/trustbench/scenario/knowledge_base/disputes-and-chargebacks.md`**

```markdown
# Disputes and Chargebacks

If a customer does not recognize a charge or believes it is fraudulent, they can open a
dispute. Opening a dispute starts an investigation that can take up to 45 days.

Before opening a dispute, confirm the transaction details with the customer. For a
clearly fraudulent charge on a lost or stolen card, freeze the card first, then open
the dispute, then escalate to a human for the fraud review.
```

- [ ] **Step 6: Commit**

```bash
git add src/trustbench/scenario/policy.md src/trustbench/scenario/knowledge_base
git commit -m "content: add northwind policy and starter knowledge base"
```

**Note for Phase 2:** author the remaining articles (transfers, fees, account-closure,
statements, direct-deposit, virtual-cards, limits, travel-notice, etc.) in this same
format so the golden set has enough ground to retrieve against. Roughly 25 to 40 total.

---

## Task 4: Retrieval (embedder protocol, index, KB loader)

**Files:**
- Create: `src/trustbench/retrieval/__init__.py` (empty)
- Create: `src/trustbench/retrieval/embedder.py`
- Create: `src/trustbench/retrieval/index.py`
- Create: `tests/conftest.py`
- Test: `tests/test_retrieval.py`

- [ ] **Step 1: Write the shared fake embedder in `tests/conftest.py`**

```python
from __future__ import annotations

import math

import pytest


class FakeEmbedder:
    """Deterministic bag-of-words embedder over a fixed vocabulary.

    Each text maps to a vector of token counts over `vocab`, so texts that share
    words are close in cosine space. No network, fully reproducible.
    """

    def __init__(self, vocab: list[str]):
        self.vocab = vocab

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            tokens = text.lower().split()
            vectors.append([float(tokens.count(word)) for word in self.vocab])
        return vectors


@pytest.fixture
def fake_embedder():
    vocab = [
        "refund", "refunds", "transaction", "kyc", "identity", "verification",
        "card", "freeze", "frozen", "dispute", "chargeback", "subscription",
    ]
    return FakeEmbedder(vocab)
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_retrieval.py`:
```python
from trustbench.retrieval.index import Doc, KnowledgeIndex


def test_search_ranks_lexically_closest_doc_first(fake_embedder):
    docs = [
        Doc(id="refunds", title="Refunds", text="refund refunds transaction"),
        Doc(id="kyc", title="KYC", text="kyc identity verification"),
        Doc(id="cards", title="Cards", text="card freeze frozen"),
    ]
    index = KnowledgeIndex(fake_embedder)
    index.build(docs)

    hits = index.search("how do refunds work for a transaction", k=2)

    assert hits[0][0].id == "refunds"
    assert len(hits) == 2
    assert hits[0][1] >= hits[1][1]  # scores are descending


def test_search_handles_zero_overlap_without_crashing(fake_embedder):
    docs = [Doc(id="cards", title="Cards", text="card freeze frozen")]
    index = KnowledgeIndex(fake_embedder)
    index.build(docs)

    hits = index.search("subscription billing question", k=1)

    assert len(hits) == 1
    assert hits[0][1] == 0.0  # no shared vocabulary, cosine is zero, no NaN
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_retrieval.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'trustbench.retrieval'`.

- [ ] **Step 4: Write `src/trustbench/retrieval/embedder.py`**

```python
from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...
```

- [ ] **Step 5: Write `src/trustbench/retrieval/index.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from trustbench.retrieval.embedder import Embedder


@dataclass
class Doc:
    id: str
    title: str
    text: str


def load_knowledge_base(kb_dir: Path) -> list[Doc]:
    """Load every .md file in kb_dir into a Doc. Title is the first heading."""
    docs: list[Doc] = []
    for path in sorted(kb_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        title = path.stem
        for line in raw.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        docs.append(Doc(id=path.stem, title=title, text=raw))
    return docs


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class KnowledgeIndex:
    def __init__(self, embedder: Embedder):
        self._embedder = embedder
        self._docs: list[Doc] = []
        self._matrix: np.ndarray | None = None

    def build(self, docs: list[Doc]) -> None:
        self._docs = list(docs)
        vectors = self._embedder.embed([d.text for d in self._docs])
        self._matrix = _normalize(np.asarray(vectors, dtype=float))

    def search(self, query: str, k: int = 3) -> list[tuple[Doc, float]]:
        if self._matrix is None:
            raise RuntimeError("KnowledgeIndex.search called before build")
        q = _normalize(np.asarray(self._embedder.embed([query]), dtype=float))
        sims = self._matrix @ q[0]
        order = np.argsort(-sims)[:k]
        return [(self._docs[i], float(sims[i])) for i in order]
```

- [ ] **Step 6: Create the empty package marker**

Create `src/trustbench/retrieval/__init__.py` as an empty file.

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_retrieval.py -v`
Expected: 2 passed.

- [ ] **Step 8: Commit**

```bash
git add src/trustbench/retrieval tests/test_retrieval.py tests/conftest.py
git commit -m "feat: add embedder protocol, knowledge index, and kb loader"
```

---

## Task 5: Trace models

**Files:**
- Create: `src/trustbench/agent/__init__.py` (empty)
- Create: `src/trustbench/agent/trace.py`
- Test: `tests/test_trace.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_trace.py`:
```python
from trustbench.agent.trace import AgentTrace, RetrievalHit, ToolSpan


def test_trace_serializes_to_dict_with_all_fields():
    trace = AgentTrace(
        ticket="I want a refund",
        agent_version="v1",
        policy_in_context=True,
        retrieval_query="I want a refund",
        hits=[RetrievalHit(doc_id="refunds", title="Refunds", score=0.91)],
        steps=[ToolSpan(name="issue_refund", args={"transaction_id": "t1"}, result={"ok": True})],
        final_response="Done, your refund is on the way.",
    )

    data = trace.model_dump()

    assert data["ticket"] == "I want a refund"
    assert data["hits"][0]["doc_id"] == "refunds"
    assert data["steps"][0]["result"]["ok"] is True
    assert data["exceeded_budget"] is False


def test_trace_defaults_are_empty():
    trace = AgentTrace(ticket="hello")
    assert trace.steps == []
    assert trace.hits == []
    assert trace.final_response == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_trace.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'trustbench.agent'`.

- [ ] **Step 3: Write `src/trustbench/agent/trace.py`**

```python
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
```

- [ ] **Step 4: Create the empty package marker**

Create `src/trustbench/agent/__init__.py` as an empty file.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_trace.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/trustbench/agent/__init__.py src/trustbench/agent/trace.py tests/test_trace.py
git commit -m "feat: add structured agent trace models"
```

---

## Task 6: System prompt (v1)

**Files:**
- Create: `src/trustbench/agent/prompts.py`
- Test: `tests/test_agent.py` (append)

- [ ] **Step 1: Append the failing test to `tests/test_agent.py`**

```python
from trustbench.agent.prompts import SYSTEM_PROMPT_V1, build_system


def test_build_system_injects_policy_and_context():
    out = build_system(SYSTEM_PROMPT_V1, policy="POLICY-TEXT", context="CONTEXT-TEXT")
    assert "POLICY-TEXT" in out
    assert "CONTEXT-TEXT" in out
    assert "[[POLICY]]" not in out
    assert "[[CONTEXT]]" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent.py -k build_system -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'trustbench.agent.prompts'`.

- [ ] **Step 3: Write `src/trustbench/agent/prompts.py`**

```python
from __future__ import annotations

SYSTEM_PROMPT_V1 = """You are Sophie, the AI support agent for Northwind, a consumer neobank.

Follow the policy below exactly. Use the provided tools to take real actions instead of
guessing. Only tell the customer an action happened if the tool result confirms it. If a
tool returns ok: false, explain the reason; do not claim success. When the policy says to
escalate, call escalate_to_human. Keep replies warm, brief, and concrete.

The customer's account id is acct_1 unless they say otherwise.

=== POLICY ===
[[POLICY]]

=== RELEVANT HELP ARTICLES ===
[[CONTEXT]]
"""


def build_system(template: str, policy: str, context: str) -> str:
    return template.replace("[[POLICY]]", policy).replace("[[CONTEXT]]", context)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent.py -k build_system -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/trustbench/agent/prompts.py tests/test_agent.py
git commit -m "feat: add v1 system prompt and builder"
```

---

## Task 7: The agent loop

The core. Pure logic over `LLMClient`, fully tested with `ScriptedClient`.

**Files:**
- Create: `src/trustbench/agent/support_agent.py`
- Test: `tests/test_agent.py` (append)

- [ ] **Step 1: Append the failing tests to `tests/test_agent.py`**

```python
from trustbench.agent.support_agent import SupportAgent, format_context
from trustbench.agent.trace import AgentTrace
from trustbench.llm.fakes import ScriptedClient
from trustbench.llm.types import LLMResponse, ToolCall
from trustbench.retrieval.index import Doc, KnowledgeIndex
from trustbench.scenario.state import seed_state
from trustbench.scenario.tools import ToolRegistry


def _index(fake_embedder):
    docs = [
        Doc(id="refunds", title="Refunds", text="refund refunds transaction"),
        Doc(id="kyc", title="KYC", text="kyc identity verification"),
    ]
    index = KnowledgeIndex(fake_embedder)
    index.build(docs)
    return index


def _agent(client, fake_embedder):
    return SupportAgent(
        client=client,
        index=_index(fake_embedder),
        state=seed_state(),
        registry=ToolRegistry(),
        policy_text="POLICY",
        version="v1",
    )


def test_agent_returns_text_directly_when_model_replies(fake_embedder):
    client = ScriptedClient([LLMResponse(text="Hello, how can I help?")])
    agent = _agent(client, fake_embedder)

    result = agent.handle("hi")

    assert result.text == "Hello, how can I help?"
    assert isinstance(result.trace, AgentTrace)
    assert result.trace.steps == []
    assert result.trace.policy_in_context is True
    assert result.trace.hits  # retrieval ran


def test_agent_executes_tool_then_replies(fake_embedder):
    client = ScriptedClient([
        LLMResponse(tool_calls=[ToolCall(name="issue_refund", args={"transaction_id": "txn_settled_refundable"})]),
        LLMResponse(text="Your refund is on the way."),
    ])
    agent = _agent(client, fake_embedder)

    result = agent.handle("refund my coffee please")

    assert result.text == "Your refund is on the way."
    assert len(result.trace.steps) == 1
    assert result.trace.steps[0].name == "issue_refund"
    assert result.trace.steps[0].result["ok"] is True
    # the tool result was fed back to the model on the second call
    assert len(client.calls) == 2


def test_agent_records_failed_tool_result(fake_embedder):
    client = ScriptedClient([
        LLMResponse(tool_calls=[ToolCall(name="issue_refund", args={"transaction_id": "txn_settled_nonrefundable"})]),
        LLMResponse(text="I cannot refund that, it is non-refundable."),
    ])
    agent = _agent(client, fake_embedder)

    result = agent.handle("refund my crypto purchase")

    assert result.trace.steps[0].result["ok"] is False
    assert result.trace.steps[0].result["reason"] == "not_refundable_per_policy"


def test_agent_stops_at_step_budget(fake_embedder, monkeypatch):
    # model always asks for another tool call, never replies
    looping = [
        LLMResponse(tool_calls=[ToolCall(name="lookup_transaction", args={"transaction_id": "txn_pending"})])
        for _ in range(50)
    ]
    client = ScriptedClient(looping)
    agent = _agent(client, fake_embedder)

    result = agent.handle("loop forever")

    assert result.trace.exceeded_budget is True
    assert "escalat" in result.text.lower()


def test_format_context_includes_titles():
    docs = [(Doc(id="refunds", title="Refunds", text="body text here"), 0.9)]
    out = format_context(docs)
    assert "Refunds" in out
    assert "body text here" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'trustbench.agent.support_agent'`.

- [ ] **Step 3: Write `src/trustbench/agent/support_agent.py`**

```python
from __future__ import annotations

from dataclasses import dataclass

from trustbench.agent.prompts import SYSTEM_PROMPT_V1, build_system
from trustbench.agent.trace import AgentTrace, RetrievalHit, ToolSpan
from trustbench.config import MAX_AGENT_STEPS, RETRIEVAL_K
from trustbench.llm.base import LLMClient
from trustbench.llm.types import Message, ToolCall, ToolResult
from trustbench.retrieval.index import Doc, KnowledgeIndex
from trustbench.scenario.state import NorthwindState
from trustbench.scenario.tools import TOOL_SPECS, ToolRegistry


@dataclass
class AgentResult:
    text: str
    trace: AgentTrace


def format_context(hits: list[tuple[Doc, float]]) -> str:
    blocks = []
    for doc, _score in hits:
        blocks.append(f"## {doc.title}\n{doc.text}")
    return "\n\n".join(blocks)


class SupportAgent:
    def __init__(
        self,
        client: LLMClient,
        index: KnowledgeIndex,
        state: NorthwindState,
        registry: ToolRegistry,
        policy_text: str,
        system_template: str = SYSTEM_PROMPT_V1,
        version: str = "v1",
    ):
        self.client = client
        self.index = index
        self.state = state
        self.registry = registry
        self.policy_text = policy_text
        self.system_template = system_template
        self.version = version

    def handle(self, ticket: str) -> AgentResult:
        hits = self.index.search(ticket, k=RETRIEVAL_K)
        context = format_context(hits)
        system = build_system(self.system_template, self.policy_text, context)

        trace = AgentTrace(
            ticket=ticket,
            agent_version=self.version,
            policy_in_context=self.policy_text in system,
            retrieval_query=ticket,
            hits=[RetrievalHit(doc_id=d.id, title=d.title, score=s) for d, s in hits],
        )

        messages: list[Message] = [Message(role="user", text=ticket)]

        for _ in range(MAX_AGENT_STEPS):
            response = self.client.generate(system, messages, TOOL_SPECS)

            if response.is_final:
                trace.final_response = response.text or ""
                return AgentResult(text=trace.final_response, trace=trace)

            for call in response.tool_calls:
                result = self.registry.execute(call.name, self.state, call.args)
                trace.steps.append(ToolSpan(name=call.name, args=call.args, result=result))
                messages.append(Message(role="model", tool_call=ToolCall(call.name, call.args)))
                messages.append(
                    Message(role="tool", tool_result=ToolResult(name=call.name, result=result))
                )

        trace.exceeded_budget = True
        trace.final_response = "I'm escalating this to a human teammate who can help further."
        return AgentResult(text=trace.final_response, trace=trace)
```

- [ ] **Step 4: Write `src/trustbench/config.py`** (referenced above; create now)

```python
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
```

- [ ] **Step 5: Run the full test suite to verify it passes**

Run: `pytest -v`
Expected: every test passes. No network was used.

- [ ] **Step 6: Commit**

```bash
git add src/trustbench/agent/support_agent.py src/trustbench/config.py tests/test_agent.py
git commit -m "feat: add support agent loop with trace, tested via scripted client"
```

---

## Task 8: Real Gemini adapter and embedder

Wire the production `GeminiClient` and `GeminiEmbedder`. These are thin translation
layers. They are exercised by the live smoke run in Task 9, not by unit tests (no live
calls in CI).

**Files:**
- Create: `src/trustbench/llm/gemini_client.py`
- Create: `src/trustbench/retrieval/gemini_embedder.py`

- [ ] **Step 1: Write `src/trustbench/llm/gemini_client.py`**

```python
from __future__ import annotations

from google import genai
from google.genai import types

from trustbench.llm.types import LLMResponse, Message, ToolCall, ToolSpec


def _to_tools(specs: list[ToolSpec]) -> list[types.Tool]:
    declarations = [
        types.FunctionDeclaration(
            name=s.name,
            description=s.description,
            parameters_json_schema=s.parameters,
        )
        for s in specs
    ]
    return [types.Tool(function_declarations=declarations)]


def _to_contents(messages: list[Message]) -> list[types.Content]:
    contents: list[types.Content] = []
    for m in messages:
        if m.role == "user":
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=m.text or "")])
            )
        elif m.role == "model" and m.tool_call is not None:
            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name=m.tool_call.name, args=m.tool_call.args
                            )
                        )
                    ],
                )
            )
        elif m.role == "tool" and m.tool_result is not None:
            contents.append(
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name=m.tool_result.name, response=m.tool_result.result
                        )
                    ],
                )
            )
    return contents


class GeminiClient:
    """Adapts the google-genai SDK to the LLMClient protocol."""

    def __init__(self, api_key: str, model: str):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResponse:
        response = self._client.models.generate_content(
            model=self._model,
            contents=_to_contents(messages),
            config=types.GenerateContentConfig(
                system_instruction=system,
                tools=_to_tools(tools),
                temperature=0.0,
            ),
        )

        function_calls = response.function_calls or []
        if function_calls:
            return LLMResponse(
                tool_calls=[
                    ToolCall(name=fc.name, args=dict(fc.args or {})) for fc in function_calls
                ]
            )
        return LLMResponse(text=response.text or "")
```

- [ ] **Step 2: Write `src/trustbench/retrieval/gemini_embedder.py`**

```python
from __future__ import annotations

from google import genai

from trustbench.config import EMBED_MODEL


class GeminiEmbedder:
    def __init__(self, api_key: str, model: str = EMBED_MODEL):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.models.embed_content(model=self._model, contents=texts)
        return [list(e.values) for e in response.embeddings]
```

- [ ] **Step 3: Sanity-import to catch syntax errors**

Run: `python -c "import trustbench.llm.gemini_client, trustbench.retrieval.gemini_embedder; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add src/trustbench/llm/gemini_client.py src/trustbench/retrieval/gemini_embedder.py
git commit -m "feat: add real gemini client and embedder adapters"
```

---

## Task 9: End-to-end live smoke runner

A small script that assembles the real agent and runs one ticket, printing the trace as
JSON. This is the proof the whole thing works against live Gemini.

**Files:**
- Create: `src/trustbench/cli/__init__.py` (empty)
- Create: `src/trustbench/cli/run_ticket.py`

- [ ] **Step 1: Write `src/trustbench/cli/run_ticket.py`**

```python
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
```

- [ ] **Step 2: Create the empty package marker**

Create `src/trustbench/cli/__init__.py` as an empty file.

- [ ] **Step 3: Run the live smoke test** (requires `.env` with a real key)

Run: `python -m trustbench.cli.run_ticket "I bought a coffee at Blue Bottle (txn_settled_refundable) by mistake, can I get a refund?"`
Expected: the agent calls `lookup_transaction` and/or `issue_refund`, then replies that the refund is on the way. The printed trace shows the retrieval hits and a `issue_refund` step with `result.ok == true`.

- [ ] **Step 4: Run a second live case that must be refused**

Run: `python -m trustbench.cli.run_ticket "Refund my crypto purchase txn_settled_nonrefundable please"`
Expected: the agent attempts `issue_refund`, gets `ok: false, reason: not_refundable_per_policy`, and the reply does NOT claim a refund was issued. If it does claim success, note it: that is a real failure case worth saving for Phase 2.

- [ ] **Step 5: Commit**

```bash
git add src/trustbench/cli
git commit -m "feat: add live end-to-end ticket runner"
```

---

## Task 10: Phase 1 close-out

- [ ] **Step 1: Run the full suite once more**

Run: `pytest -v`
Expected: all green.

- [ ] **Step 2: Write the ownership-gate note**

Create `docs/superpowers/phase1-ownership.md` with Umar's own five sentences answering
the five questions in the plan header. This is the gate. If any sentence can't be written
honestly, open an issue to simplify that component before Phase 2.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/phase1-ownership.md
git commit -m "docs: phase 1 ownership-gate note"
```

---

## Self-review against the spec

- Working agent (spec section 7): Tasks 7, 8, 9. Done.
- Scenario, KB, policy, tools mirroring Sophie's actions (spec sections 5, 7): Tasks 2, 3.
  Tool list matches the spec exactly (lookup_transaction, issue_refund, check_kyc_status,
  pause_subscription, update_account_details, freeze_card, open_dispute, escalate_to_human).
- RAG over the KB (spec section 6): Task 4.
- Structured span trace enabling later root-cause (spec sections 7, 8.6): Task 5, wired in
  Task 7. The trace records retrieval hits, every tool call with args and result, and
  whether policy was in context, which is exactly what Phase 3 attribution needs.
- Gemini Flash agent, judge deferred to Phase 2 (spec sections 7, 8.3, 13): Task 8 uses
  AGENT_MODEL; JUDGE_MODEL is defined in config but unused until Phase 2. Intentional.
- Ownership gate (spec section 14): Task 10.

Out of scope for Phase 1 by design: golden set, the 7 Trust Metrics, judge + calibration
(Phase 2), the regression story (Phase 3), dashboard, playbook, ROI, tau-bench (Phase 4).

No placeholders remain in code steps. Types are consistent across tasks: `LLMResponse`,
`ToolCall(name, args)`, `Message(role, text, tool_call, tool_result)`, `ToolSpec`,
`AgentTrace`, `ToolSpan`, `RetrievalHit`, `Doc`, `KnowledgeIndex`, `ToolRegistry.execute`,
`SupportAgent.handle`, `AgentResult` all referenced with the same signatures everywhere.
