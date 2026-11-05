# Validation Record

## 1. Observed results

Validation date: 04 November 2026. Local environment: Windows, Python 3.14, pypdf 6.10.0, OpenAI Python SDK 2.54.0 and reportlab 4.4.9, installed in an isolated virtual environment.

The full offline suite completed with **36 tests passed, zero failures and zero skipped tests** after the review fixes. The SDK contract test used the real SDK against an in-memory HTTP transport. No API key, external model inference or paid request was used.

```bash
python -m unittest discover -s tests -v
```

The five example files were produced by executing the deterministic demo with the supplied CSV/PDF fixtures. Their generation fails if any reply reports an execution error.

```bash
python scripts/generate_examples.py
```

## 2. What the tests establish

- Catalog filtering: category aliases, stock/status, unavailable instruments and a monetary boundary at BRL 323.10.
- Price calculations: original prices, active promotions, inactive offers and prevention of PIX/promotion stacking.
- Input boundaries: negative/non-finite/bool budgets, numeric strings at the model boundary, malformed JSON, unexpected keys, booleans as order IDs and integers too large for SQLite.
- Access control: a customer can read its own order, missing and unauthorized orders are indistinguishable, and chat/tool arguments cannot replace trusted identity.
- Retrieval: English/Portuguese return queries, source pages, unknown topics, conflicting contacts and warranty questions with generic delivery-time words.
- Agent control: real tool execution, serialized call outputs, four-request/eight-call limits, provider-error privacy and bounded/resettable memory.
- Demo behavior: budget search, product-to-PIX context, explicit category changes, return clarification, orders and scope redirection.
- CLI: single-message and interactive use, reset/exit, missing key recovery and invalid customer IDs.
- SDK compatibility: typed function-call parsing, real evidence serialization and final message parsing through a local HTTP fixture.

## 3. Review findings and fixes

A separate code-review pass found one important and two minor issues. Each was reproduced with a failing regression test before changing the implementation.

- Very large positive order/customer IDs could overflow SQLite's integer binding. Both identifiers now require the positive signed-64-bit range and produce controlled errors outside it.
- A PIX follow-up containing a new category could reuse the old product query. Explicit categories and brands now override the previous product context.
- A Portuguese warranty question could tie with shipping and receive an unrelated demo response. Weighted lexical scoring and an explicit warranty-topic boost resolve the reproduced case.

No cross-customer order disclosure or unrestricted SQL/tool execution was found in that review. This is a scoped review result, not a general security certification.

## 4. What remains unverified

No real-model conversation has been run. The live mode's quality, tool-selection reliability, adversarial robustness, response latency, token cost and account/model availability remain unmeasured. A mocked provider transcript cannot establish those properties.

The GitHub Actions configuration targets Linux/Windows and Python 3.11/3.14, but remote CI has not been executed. Local validation was on Windows/Python 3.14; support for other environments is an implementation target rather than an observed matrix result.

The project is published at [guipetruitis/emporio-ai-agent](https://github.com/guipetruitis/emporio-ai-agent) with its development history. Public publication is separate from the offline validation above; no deployed service or submitted application is claimed. Production authentication, fresh operational data, human escalation and independent legal review are outside the prototype.

## 5. Before submission

- Read the code and rationale and adapt decisions you would not defend in an interview.
- Configure your own API key and run representative live conversations, recording failures honestly.
- Review the supplied fictional fixtures before publishing; customer contact data has been omitted from this project.
- Use the public repository URL in the application form: https://github.com/guipetruitis/emporio-ai-agent.
- Confirm the candidate's full name, the requested filename and the recruiter's deadline. Do not change the submitted repository after the applicable cutoff.

The generated PDF includes the exact authored Markdown sources and examples, making its claims inspectable against the code and fixtures.
