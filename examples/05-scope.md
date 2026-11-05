# Store information, source conflict and scope boundaries

Execution mode: deterministic offline demo; real CSV/PDF tools, no LLM or network.
Trusted fictional customer session: none.

Reproduce all five examples: `python scripts/generate_examples.py`.

## Customer
What is the store address and opening hours?

## Assistant
The store is at Rua 14 de Maio, 3200 - Centro, Campo Grande/MS, CEP 79202-333. Opening hours: Monday-Friday 09:00-18:00; Saturday 09:00-13:00; closed Sundays and holidays. WhatsApp follows these hours. Please confirm any special-date schedule with the team. [Store policy, p. 2]

**Tools executed:** search_policies.

## Customer
What is the WhatsApp phone number?

## Assistant
The manual is inconsistent: pages 1-2 list (67) 3341-4444, while section 7 on page 6 lists WhatsApp (67) 3321-4500. Email spelling also differs across pages. The current contact details need confirmation from the store team. [Store policy, p. 1, 2, 6]

**Tools executed:** search_policies.

## Customer
Sell me guitar strings

## Assistant
We specialize in musical instruments and do not sell accessories. Please ask the team for a suitable retailer. [Store policy, p. 2, 6]

**Tools executed:** search_policies.

## Customer
Write an essay about elections

## Assistant
I can help with musical instruments and store policies. For this request, please speak with the store team. No ticket has been created. The offline demo understands only a small set of patterns; use --mode openai for flexible conversation.

**Tools executed:** search_policies, handoff.
