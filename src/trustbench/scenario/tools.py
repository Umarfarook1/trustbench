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
