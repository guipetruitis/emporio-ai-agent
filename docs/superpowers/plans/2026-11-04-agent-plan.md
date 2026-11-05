# Emporio Agent Implementation Plan

> **For agentic workers:** implement inline using superpowers:executing-plans, with test-first changes and final review.

**Goal:** Build and document the read-only support agent and export a submission PDF.

**Architecture:** CSV-backed SQLite tools plus page-grounded lexical retrieval feed a bounded LLM function-calling loop. A deterministic offline demonstration reuses the tools.

**Tech Stack:** Python 3.11+, sqlite3, pypdf, OpenAI Python SDK; reportlab for PDF export.

**Spec:** ../specs/2026-11-04-agent-design.md

## Global constraints
English authored materials; original Portuguese fixtures retained as evidence. No customer contact CSV, secrets, public posting, model-supplied identity, arbitrary SQL, fabricated receipt dates or fabricated live validation.

## Review focus
Boundary monetary values, unknown bilingual terms, policy contradictions, cross-customer requests, and provider failures each need behavioral tests.

## Task 1: Read-only evidence tools
Files: emporio/store.py, emporio/policies.py, emporio/tools.py, data/*, tests/test_tools.py.
Interfaces: Store(data_dir), search_products(query, max_price_brl, available_only); get_order(order_id, customer_id); Policies(data_dir).search(query); Tools.execute(name, arguments).
- [ ] Write failing tests for discounts (active versus expired), stock, injection strings, ownership, invalid amounts and policy routing.
- [ ] Run unittest and observe missing implementation failure.
- [ ] Implement tools, original PDF extraction and the curated bilingual policy index.
- [ ] Run tests and commit a working evidence layer.

## Task 2: Agent loop and CLI
Files: emporio/agent.py, emporio/demo.py, emporio/__main__.py, pyproject.toml, requirements.txt, tests/test_agent.py, tests/test_cli.py.
Interfaces: Agent(tools, client, model).reply(message) returns answer and trace; DemoAgent(tools).reply(message) returns same result type. CLI: python -m emporio --mode demo|openai [--message TEXT] [--customer-id INT].
- [ ] Write and run failing tests for function-call/output flow, invalid calls, tool limits, provider outage, history, input bounds and CLI output.
- [ ] Implement strict schemas, bounded agent, deterministic demo and CLI.
- [ ] Run full suite, smoke-test commands and commit.

## Task 3: Documentation, examples and submission
Files: README.md, docs/DOCUMENTATION.md, docs/VALIDATION.md, examples/*.md, scripts/*, PDF and ZIP outside the repo.
- [ ] Generate five conversations from real offline runs.
- [ ] Write English setup, rationale, prompt/retrieval design, limitations, evaluation and honest AI-assistance disclosure.
- [ ] Add CI and a reproducible reportlab Markdown-to-PDF exporter.
- [ ] Run clean-environment tests, verify all requested scenarios, review code/security and render/inspect every PDF page.
- [ ] Commit documentation and package the source with Git history; verify archive and final PDF.
