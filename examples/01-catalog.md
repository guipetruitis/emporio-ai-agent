# Budget-conscious instrument search

Execution mode: deterministic offline demo; real CSV/PDF tools, no LLM or network.
Trusted fictional customer session: none.

Reproduce all five examples: `python scripts/generate_examples.py`.

## Customer
Which acoustic guitars are available under BRL 1000?

## Assistant
Here is what I found in the supplied catalog snapshot:
- Tagima Memphis AC-39 Nylon Natural: BRL 429.90; in stock (15). PIX: BRL 408.41 (5% off list; no active promotion).
- Rozini RC-104 Nylon Estudante: BRL 459.90; in stock (10). PIX: BRL 436.91 (5% off list; no active promotion).
- Shelby SN-100 Folk Aço Preto: BRL 549.00; in stock (5). PIX: BRL 521.55 (5% off list; no active promotion).
- Giannini GF-1R Aço Folk Sunburst: BRL 579.90; in stock (7). PIX: BRL 550.91 (5% off list; no active promotion).
- Yamaha C40 Nylon Natural: BRL 599.90; in stock (12). PIX: BRL 569.91 (5% off list; no active promotion).
- Giannini GN-15 Nylon Cedr Natural: BRL 689.00; in stock (6). PIX: BRL 654.55 (5% off list; no active promotion).
- Yamaha F310 Aço Natural: BRL 699.90; in stock (14). PIX: BRL 664.91 (5% off list; no active promotion).
- Tagima Dallas Tuner Aço Natural: BRL 749.00; in stock (9). PIX: BRL 711.55 (5% off list; no active promotion).
Showing 8 of 12 matches; narrow your search for more.
[products.csv + promotions.csv; PIX policy, p. 3, 6. Not live inventory.]

**Tools executed:** search_products.

## Customer
How much does the Takamine GD20 cost?

## Assistant
Here is what I found in the supplied catalog snapshot:
- Takamine GD20 Dreadnought Natural: BRL 2,199.00; in stock (5). PIX: BRL 2,089.05 (5% off list; no active promotion).
[products.csv + promotions.csv; PIX policy, p. 3, 6. Not live inventory.]

**Tools executed:** search_products.

## Customer
What about the PIX price?

## Assistant
Here is what I found in the supplied catalog snapshot:
- Takamine GD20 Dreadnought Natural: BRL 2,199.00; in stock (5). PIX: BRL 2,089.05 (5% off list; no active promotion).
[products.csv + promotions.csv; PIX policy, p. 3, 6. Not live inventory.]

**Tools executed:** search_products.
