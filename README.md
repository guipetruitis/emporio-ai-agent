# Emporio da Musica - AI Customer Support

A small, read-only Python agent for the Artefact AI Engineer technical challenge. It answers instrument-catalog questions, retrieves store policies, checks scoped order records and redirects requests outside the store's scope.

Prepared for Guilherme Petruitis Cantagesso. All authored documentation and example answers are in English. The original Portuguese data and policy text remain unchanged as evidence.

Public repository: [github.com/guipetruitis/emporio-ai-agent](https://github.com/guipetruitis/emporio-ai-agent).

Submission document: [English README and documentation PDF](https://github.com/guipetruitis/emporio-ai-agent/blob/development/docs/submission.pdf).

## 1. What is implemented

- A live-agent integration using the OpenAI Responses API and four validated function tools.
- A deterministic offline demo using the same real CSV/PDF tools. This is a limited demonstration, not an LLM.
- Exact prices in integer BRL cents, stock/status checks and active, non-cumulative promotions.
- Bilingual lexical retrieval over a small policy index, with the original PDF pages attached to tool results.
- Order lookup restricted to a trusted local fictional-customer context; customer contact data is not loaded.
- In-memory conversation history, reset support, bounded model/tool execution and actionable errors.
- Automated behavioral tests, CI configuration, five reproducible conversations and a PDF exporter.

The data is the supplied static challenge snapshot. There is no live ERP, payment, delivery-carrier or WhatsApp integration. The agent cannot place orders, approve refunds, create support tickets or contact a human.

## 2. Quick start: no API key needed

Use Python 3.11 or later. Run commands from the extracted repository root, where `data/` is located.

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate on macOS/Linux:

```bash
source .venv/bin/activate
```

Install and start:

```bash
python -m pip install -r requirements.txt
python -m emporio --mode demo
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` directly in place of `python`; changing your execution policy is unnecessary.

Try a single question:

```bash
python -m emporio --mode demo --message "What is the store address?"
```

For a budget search, start an interactive session and ask: `Which acoustic guitars are available under BRL 1000?` Follow with `How much does the Takamine GD20 cost?` and `What about the PIX price?`

The demo supports a small set of English/Portuguese patterns, named instrument searches and selected policy topics. Flexible phrasing and general multi-step follow-ups require the live LLM mode. Demo answers are always English. Use plain numeric budgets such as `1000` or `999.90`; thousands separators are not supported by the demo parser.

## 3. Run the live LLM agent

Install the optional provider dependency:

```bash
python -m pip install -r requirements-live.txt
```

Set environment variables in Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
$env:OPENAI_MODEL="gpt-5.6-terra"
python -m emporio --mode openai
```

On macOS/Linux:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
export OPENAI_MODEL="gpt-5.6-terra"
python -m emporio --mode openai
```

`--model` overrides `OPENAI_MODEL`; the default is `gpt-5.6-terra`. Choose a Responses-compatible model with function calling available to your account. An API key, provider access and usage credits are required. The application reads the shell environment; `.env.example` is documentation, not an automatically loaded file. Never commit a real key.

Live integration has been exercised with the real Python SDK and local HTTP fixtures. No paid, real-model request was performed for this delivery. Model quality, live account access, latency and cost are not validated results.

## 4. Order lookup and CLI controls

For a fictional customer session with access to order 1:

```bash
python -m emporio --mode demo --customer-id 3
```

Ask `What is the status of order 1?` Then ask for order 8: it is unavailable in that session. Saying a different customer ID in chat does not change the session.

`--customer-id` is a developer-controlled demo setting. It is not production authentication. Do not expose this CLI as a public customer service. A production adapter must derive identity from verified authentication rather than accepting a customer-supplied identifier.

- `/reset`: erase conversation memory; the current customer context stays fixed.
- `/quit`: end the session. EOF and Ctrl+C also exit.
- `--message "..."`: answer one message and exit.
- `--trace`: print tool names and minimized results locally; use only with fictional data.
- `--data-dir PATH`: point to a complete copy of the project's data folder.

Restart the application after changing source data. Nothing is saved to a conversation database.

## 5. Why this architecture

I chose direct function calling plus lightweight policy retrieval. Structured operations such as price filtering, active promotions and order ownership belong in Python/SQL. Policy wording belongs in retrieved evidence. Keeping those responsibilities separate makes both easier to test.

SQLite and the standard library avoid a database service. Integer cents and Decimal avoid binary floating-point pricing errors. Allowlisted queries avoid an unrestricted SQL agent. A bilingual lexical index is sufficient for an eight-page manual, has no embedding cost and exposes its evidence clearly. It will need replacement or expansion for a larger or frequently changing corpus.

The OpenAI SDK handles the provider protocol; no agent framework is needed for four tools and a bounded loop. The chosen model is configurable, and its suitability is a design hypothesis rather than a measured comparison. A CLI keeps the challenge focused on agent behavior.

See [Technical documentation](docs/DOCUMENTATION.md) for tool contracts, retrieval, prompts, security and ambiguity handling.

## 6. Verification and examples

```bash
python -m unittest discover -s tests -v
python scripts/generate_examples.py
```

Install `requirements-live.txt` before testing to include the real-SDK HTTP contract test; otherwise that one test is explicitly skipped. Tests and examples make no model requests and require no API key.

The five conversations under `examples/` cover budget search and price follow-up, active/expired promotions, a return request with missing receipt information, scoped orders and attempted identity switching, and store information/scope boundaries. They are generated from actual offline runs, not represented as live LLM transcripts.

See [Validation record](docs/VALIDATION.md) for observed results and remaining checks.

## 7. Known limitations and next steps

- The source snapshot is not a current inventory or delivery system. No actual receipt dates exist, so return eligibility cannot be confirmed from order records alone.
- Policy contradictions are surfaced for staff confirmation: phone numbers, installment conditions and the undefined shipping fee at exactly BRL 500.
- Lexical retrieval has limited recall and the offline demo has narrow language coverage. The live LLM can still select the wrong tool, misread evidence or hallucinate; the prompt is not a proof of factual correctness.
- No production authentication, public API, persistent storage, rate-limiting service or authenticated human handoff is implemented.
- The bounded loop limits one answer to four provider requests and eight tool calls, with a 1,800-token output cap per request. It is not a monthly spending cap.

With more time, I would first run a real-model evaluation, including adversarial and multilingual questions; resolve source ambiguities with the store; add authenticated access and fresh ERP/carrier adapters; and introduce versioned retrieval, answer-quality monitoring and a minimal UI only after those controls work.

## 8. AI-assistance disclosure

OpenAI Codex was used to inspect the supplied materials, propose the design, implement the Python modules, write tests, investigate failures, generate examples, draft the English documentation and produce the PDF. The implementation and technical rationale were drafted by the coding assistant at the candidate's request. The Git commits record actual stages of that work and use Codex as the author; they are not presented as a history of unaided candidate work. Guilherme should review, understand and adapt the solution before submitting it or discussing its decisions in an interview.

## 9. PDF and submission

To rebuild the documentation PDF from these exact Markdown sources:

```bash
python -m pip install -r requirements-report.txt
python scripts/export_pdf.py --output submission.pdf
```

The export includes this README, technical documentation, validation record and five example conversations. The original challenge PDFs are evidence files, not substituted for the project's documentation.

The public GitHub repository preserves the staged development commits. Submit its verified URL together with the documentation PDF according to the recruiter's instructions. Live-model validation remains pending, and no application has been submitted by this project.
