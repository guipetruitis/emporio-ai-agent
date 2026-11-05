# Active and expired promotions

Execution mode: deterministic offline demo; real CSV/PDF tools, no LLM or network.
Trusted fictional customer session: none.

Reproduce all five examples: `python scripts/generate_examples.py`.

## Customer
How much does the Crafter HT-100 cost?

## Assistant
Here is what I found in the supplied catalog snapshot:
- Crafter HT-100 Folk Aço Natural: BRL 1,967.18; in stock (3). List BRL 2,399.00, 18% active discount. PIX is not cumulative.
[products.csv + promotions.csv; PIX policy, p. 3, 6. Not live inventory.]

**Tools executed:** search_products.

## Customer
Can I combine a promotion with PIX?

## Assistant
PIX has a 5% list-price discount, which cannot be combined with promotional prices. Debit cards and boleto are accepted; boleto clearing takes up to 3 business days. The payment table says credit up to 12 interest-free installments with a BRL 100 minimum, while section 3.1 says up to 3 installments with a BRL 50 exception, 4-6 installments with BRL 80 minimum and 7-12 with BRL 100 minimum. Please confirm installment eligibility with staff due to the contradiction. Combined payment methods are allowed for purchases above BRL 2,000. [Store policy, p. 3, 6]

**Tools executed:** search_policies.

## Customer
How much does the Martin D-28 cost?

## Assistant
Here is what I found in the supplied catalog snapshot:
- Martin D-28 Dreadnought Natural: BRL 11,499.00; in stock (2). PIX: BRL 10,924.05 (5% off list; no active promotion).
- Martin D-28E Elétrico Aço Natural: BRL 12,000.00; in stock (1). PIX: BRL 11,400.00 (5% off list; no active promotion).
[products.csv + promotions.csv; PIX policy, p. 3, 6. Not live inventory.]

**Tools executed:** search_products.
