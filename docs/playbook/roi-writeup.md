# ROI writeup: what an accuracy gain is worth

Solutions Engineering is judged on business outcomes, not eval dashboards. This is how I would
frame the value of a TrustBench-driven deployment to a customer like Northwind, and how the
eval numbers convert into money.

## The model

The lever is the share of tickets the agent resolves without a human, and how reliably it does
so. Two costs matter: the human cost of every ticket that escalates, and the per-resolution
cost of the AI.

```
monthly_human_cost_saved =
    monthly_tickets
    * (automation_rate)
    * cost_per_human_handled_ticket

monthly_ai_cost =
    monthly_tickets
    * automation_rate
    * cost_per_ai_resolution

net_monthly_value = monthly_human_cost_saved - monthly_ai_cost
```

The second lever, which most teams miss, is regression risk. A silent two-point drop in
resolution on a high-volume intent quietly pushes thousands of tickets back to humans. Catching
it before it ships is real money, not hygiene.

## Worked example (illustrative; replace with the live numbers)

These inputs are illustrative. The automation and escalation rates come from your TrustBench
run; the cost inputs come from the customer.

| Input | Illustrative value |
| --- | --- |
| Monthly tickets | 100,000 |
| Automation rate (from eval) | 80 percent |
| Cost per human-handled ticket | 5.00 USD |
| Cost per AI resolution | 0.69 USD (Fini's published figure) |

```
human_cost_saved = 100,000 * 0.80 * 5.00   = 400,000 USD / month
ai_cost          = 100,000 * 0.80 * 0.69   =  55,200 USD / month
net_value        = 400,000 - 55,200        = 344,800 USD / month
```

## What a caught regression is worth

Suppose v2 ships and resolution on refund tickets drops from 94 to 89 percent, and refunds are
12 percent of volume. The regressed tickets per month:

```
regressed_tickets = 100,000 * 0.12 * (0.94 - 0.89) = 600 tickets / month
extra_human_cost   = 600 * 5.00                      = 3,000 USD / month
```

That is the monthly cost of one silent five-point slip on a single mid-size intent. Catching it
in CI before it reaches customers is the entire argument for gating changes on a per-intent
golden set rather than an aggregate number.

## How to fill this in for real

1. Run `run_eval` on the live agent to get the automation and per-intent resolution rates.
2. Get the customer's monthly ticket volume and fully-loaded cost per human-handled ticket.
3. Plug both into the formulas above.
4. Report net monthly value and the regression-avoidance value separately, because they come
   from two different parts of the work: tuning, and quality gating.

The point for a Solutions Engineer interview is not the exact number. It is that the number
exists, is defensible, and connects an eval table to a line item the customer's finance team
recognizes.
