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
