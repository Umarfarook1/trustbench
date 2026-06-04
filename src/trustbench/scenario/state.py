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
