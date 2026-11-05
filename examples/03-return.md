# Return policy with missing receipt information

Execution mode: deterministic offline demo; real CSV/PDF tools, no LLM or network.
Trusted fictional customer session: 3.

Reproduce all five examples: `python scripts/generate_examples.py`.

## Customer
I regret my online purchase. Can I return it?

## Assistant
For an online purchase, the manual allows a return request within 7 calendar days after actual receipt, with original packaging, no signs of use, all accessories and manuals. Refunds use the original payment method within 10 business days; the store pays return shipping for regret. Preference exchanges: 7 days, perfect condition, original packaging, subject to availability. Manufacturing-defect exchanges: 30 calendar days after purchase, then manufacturer warranty assistance. Customized items, explicitly final-sale clearance items and wind mouthpieces are excluded in the manual. Eligibility depends on the actual receipt date, purchase channel and item condition. An estimated delivery date does not establish receipt. The team must review exceptions and any questions about statutory rights. [Store policy, p. 4] Was this an online purchase, when did you actually receive it, and is it unused in the original packaging?

**Tools executed:** search_policies.

## Customer
Can I return order 1?

## Assistant
Order 1 is delivered in the supplied snapshot. Total: BRL 11,499.00. Recorded tracking code: BRAB1234567BR. Recorded estimated delivery: 2025-10-25; this is not proof of receipt or a current delivery promise. [orders.csv; not live carrier tracking]
For an online purchase, the manual allows a return request within 7 calendar days after actual receipt, with original packaging, no signs of use, all accessories and manuals. Refunds use the original payment method within 10 business days; the store pays return shipping for regret. Preference exchanges: 7 days, perfect condition, original packaging, subject to availability. Manufacturing-defect exchanges: 30 calendar days after purchase, then manufacturer warranty assistance. Customized items, explicitly final-sale clearance items and wind mouthpieces are excluded in the manual. Eligibility depends on the actual receipt date, purchase channel and item condition. An estimated delivery date does not establish receipt. The team must review exceptions and any questions about statutory rights. [Store policy, p. 4]

**Tools executed:** get_order, search_policies.
