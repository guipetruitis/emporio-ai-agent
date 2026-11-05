# Technical Documentation

## 1. Request-to-answer flow

The CLI constructs a read-only in-memory database from CSVs and extracts the eight-page policy PDF. A trusted fictional-customer context is fixed when the process starts. The live agent receives a user message together with up to six completed turns of conversational context.

The first provider request must select a tool. The application validates its name, exact argument keys, JSON types and domain constraints before execution. The result is returned as a `function_call_output`, associated with its call ID. Further calls can retrieve complementary evidence. A final answer is accepted only after at least one tool result exists in that turn. The loop stops after four requests or eight calls and offers a clear recovery message if it cannot finish.

This control flow encourages grounding; it does not semantically prove that every sentence follows from the evidence. Model-grounding quality must be evaluated separately. The provider's text is never executed as code or SQL.

The offline demo replaces intent interpretation and prose generation with deterministic patterns and English policy summaries. It still reads the actual same database and PDF. Its single product-query memory supports a price/PIX follow-up; it does not implement general conversation reasoning.

## 2. Repository map

- `emporio/store.py`: CSV ingestion, integer-cent pricing, catalog search and customer-scoped order queries.
- `emporio/policies.py`: original PDF extraction and bilingual lexical ranking.
- `emporio/tools.py`: four provider schemas, argument validation and allowlisted dispatch.
- `emporio/agent.py`: persona/instructions, Responses loop, input and execution limits, conversation memory.
- `emporio/demo.py`: explicitly deterministic demonstration of tools and policies.
- `emporio/__main__.py`: configuration, optional SDK loading and terminal interaction.
- `data/`: selected original challenge fixtures and an authored English policy index.
- `tests/`: offline behavioral and SDK-transport checks.
- `examples/`: five conversations reproduced by `scripts/generate_examples.py`.
- `scripts/export_pdf.py`: reproducible export of README, documentation, validation and examples.
- `.github/workflows/tests.yml`: configured Linux/Windows, Python 3.11/3.14 CI matrix. Its remote execution is not claimed as completed.

## 3. Data treatment and provenance

The project retains 65 products, 9 categories, 25 promotion records, 20 orders and 22 order-item rows. Product statuses are 62 active, 2 discontinued and 1 coming soon. One active product has zero stock. A positive quantity alone therefore does not imply purchasability.

The six original operational CSVs are selectively used: `customers.csv` is omitted because order ownership can be enforced using the order's existing customer ID. Names, emails, phones and cities from the customer table are unnecessary. The five retained CSVs are copied byte-for-byte from the supplied challenge, with shorter filenames. The policy PDF is also copied without alteration as `store_policies.pdf`. `data/PROVENANCE.json` records their hashes.

CSV files are read as UTF-8 with optional BOM. IDs, quantities and flags are parsed explicitly. Prices are parsed as Decimal and quantized to integer cents using half-up rounding. The SQLite connection is switched to `query_only` after loading. It is closed on exit and never written to disk.

Product descriptions and specs remain Portuguese. English replies and the authored policy summaries are presentation aids, not rewritten source records. Historical order totals are preserved; they are not recomputed from today's catalog prices. `estimated_delivery` is passed through with an explicit warning, never renamed to an actual delivery date. Free-text order notes are excluded from tool responses.

## 4. Tool contracts

### search_products

Arguments: `query` (1-200 characters), `max_price_brl` (non-negative finite number or null) and `available_only` (boolean). The tool accepts model names or simple categories such as `acoustic guitar`, `violao` or `ukulele`. The live prompt tells the LLM to extract these from the full question.

Known category aliases map to category IDs. Other queries use accent-insensitive token matching against product names/descriptions. SQL values are bound parameters and LIKE wildcards are escaped. Results are sorted by effective price and product ID; at most eight are returned, with a separate total count. Narrow the query when more matches exist.

Purchasable means `status == active` and `stock_quantity > 0`. Exact-product queries may include unavailable records so a model is not silently replaced by another instrument. The response contains list price, active discount, effective price, PIX price, availability and source/freshness metadata.

Only promotions with `is_active == 1` apply. There are no start/end dates, so the active flag is treated as the supplied authority. If multiple active promotions exist for one product, use the highest single percentage, never their sum. PIX is 5% off list when there is no active promotion; a promotional price receives no additional PIX discount. Budget filtering uses the effective price before payment-specific PIX conditions.

Example: Crafter HT-100 is BRL 2,399.00 list, with an active 18% discount, resulting in BRL 1,967.18. PIX remains BRL 1,967.18. A historical promotion for Martin D-28 is inactive and is not applied.

### search_policies

Argument: `query` (1-300 characters). Results contain up to two index entries with English summaries, exact original page text, page references and a confirmation flag for known contradictions. No evidence is returned for a query with zero keyword overlap.

### get_order

Argument: positive integer `order_id`. Customer identity is absent from the schema. The dispatcher binds the trusted process context, and SQL filters by both order and customer IDs. Missing identity yields `identity_required`; a nonexistent or unowned order yields the same `order_unavailable` response. Results include minimized status, total, dates, recorded tracking code and item descriptions. They exclude owner IDs, contact data and free-text notes.

### handoff

Argument: a short `reason`. This returns a limitation message and recommends speaking with the team. It performs no external action and creates no ticket. Scope handling is reinforced by the original instrument-only store policy.

## 5. Policy retrieval and source conflicts

The manual is small enough for a curated lexical index. Nine topic entries map bilingual keywords to original page ranges. Queries are lowercased, accents normalized and common stopwords removed. Ranking sums inverse-topic-frequency weights for unique matching keywords; an explicit warranty term receives an additional topic boost so generic delivery-time words do not win. Remaining ties retain the explicit index order. Up to two topics and their original pages are sent to the LLM. The PDF is extracted once per process.

The English summaries in `policy_index.json` were authored from the supplied manual. They are editable retrieval aids with page evidence, not machine-extracted assertions. Manual changes require reviewing this index and its page numbers together. This deliberate simplicity trades semantic recall and automatic updates for transparent behavior and minimal infrastructure.

Known source issues are handled explicitly:

- Contact: pages 1-2 give (67) 3341-4444; section 7 gives (67) 3321-4500. The email spelling also differs. Ask staff to confirm, without declaring either number verified.
- Installments: the payment table gives a BRL 100 minimum, while section 3.1 specifies different minimums by installment range. Explain the conflict and ask staff.
- Local shipping: the manual specifies amounts above and below BRL 500 but omits exactly BRL 500. Do not guess the boundary fee.
- Returns: actual receipt date, purchase channel and condition are missing from order records. Ask for them; an estimated date is not evidence of receipt. Exceptions that may conflict with customer rights go to staff rather than an automated legal ruling.
- Tracking: preserve the supplied code as recorded, without rewriting it to match the manual's example format or promising a carrier update.

These are applications of fictional store materials, not independent legal or regulatory advice.

## 6. Prompt and memory strategy

The system prompt lives in `agent.py` and is kept separate from user messages. It defines the music-specialist persona, English response requirement, instrument-only scope, evidence requirements, monetary units, privacy boundaries and honest limitations. Retrieved policy pages are data; any instructions contained in them are not granted authority over the application.

The prompt directs the model to query structured data for prices/stock/orders and the manual for policies. It asks for a focused clarifying question when facts are missing. No chain-of-thought is requested or logged. Tool traces expose observable tool evidence, not private reasoning.

Only six completed user/assistant turns are retained. Tool payloads are used within the current turn but are not saved as durable conversation state. Every new turn requires a fresh tool call. `/reset` clears conversational context but cannot switch the trusted customer identity. Closing the process clears all memory. Live requests use `store=False`; that setting does not imply a blanket guarantee about the provider's retention policies.

## 7. Reliability and security boundaries

- Input is limited to 3,000 non-whitespace characters. Tool-specific strings and numeric ranges are validated independently of provider strict mode.
- Tool names and exact keys are allowlisted; SQL and shell execution are not exposed. Integer identity checks reject booleans masquerading as IDs.
- Each reply permits four provider requests, eight tool calls and 1,800 output tokens per request. SDK calls have a 25-second timeout and automatic retries disabled. No provider spend budget is claimed.
- Provider errors produce a generic message without raw exception text, credentials or request contents. A failed reply does not enter conversation history.
- API keys are environment-only; `.env` files are ignored before the first code commit. No network listener, browser renderer or public endpoint exists.
- No raw chats are written to logs. `--trace` is an explicit local debugging option and can contain the current fictional customer's minimized order details.

Prompt injection cannot be eliminated by wording alone. The main protections are capabilities: read-only tools, validated arguments, no model-controlled identity, no arbitrary queries and no external side effects. The prototype is not ready to serve real customers until authentication, access auditing, rate limits, privacy review and source refresh controls are added.

## 8. Evaluation plan and tradeoffs

The offline suite checks business logic, policy lookup, source ambiguity, denied order access, malformed model calls, tool budgets, memory and CLI recovery. A real SDK over an in-memory HTTP transport checks request/response compatibility without consuming model credits.

Before claiming LLM quality, build a labeled set of English/Portuguese single- and multi-turn questions. Measure correct tool selection, source retrieval, price/discount accuracy, policy faithfulness, clarification of missing facts, scope handling and protection against cross-customer requests. Include mixed intents, unavailable instruments, expired promotions, conflicting contacts, exact monetary boundaries, unknown terms, provider outages and injection attempts. Record model identifier, prompt/index versions, token usage and latency; compare candidates using the same questions. Require zero unauthorized disclosures and zero invented refund or order actions. Review failures manually rather than using a model judge alone.

Embeddings, a larger agent framework, persistent memory and a web UI were deferred because the supplied corpus and task are small. The first useful production work is resolving source contradictions and adding authenticated, current business-system tools, not increasing orchestration complexity.

## 9. External implementation references

- [OpenAI function calling guide](https://developers.openai.com/api/docs/guides/function-calling): tool schemas and function-call/output protocol.
- [OpenAI GPT-5.6 Terra model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-terra): the configurable model chosen for the integration; no comparative benchmark is claimed.
- [Python sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html): local database and bound SQL parameters.
- [pypdf documentation](https://pypdf.readthedocs.io/): extraction of the supplied policy PDF.

The source of business facts is the supplied challenge material. External references explain implementation interfaces; they do not override store policies.
