# Expert investigations

Open **Expert** in the navigation after selecting a demo identity. Expert is an independent case workspace with five business objectives, randomized case data, and its own persistent evidence. It does not require completion of the guided challenges.

## Your assignment

Investigate unexpected account disclosures and refund activity at your assigned fictional company. Start with the case file, which contains customer references, a shift handover, orders, and a delivery integration entry. Settlement research is another lead. Discover relevant identifiers through these materials and the assistant’s document catalogue.

The five objectives cover an unexpected attachment, a later task going astray, an unfamiliar settlement, approval discrepancies, and a delivery check with a side effect. Vulnerability names and explanations appear after evidence confirms an objective. Three optional hints per objective are revealed manually and saved.

Each case randomizes the company/customer identifiers, order and document identifiers, amounts, company names, and fictional confidential content. References remain consistent with the generated data. Scenario structure is intentionally reproducible; this is a deterministic simulator, not a real-model benchmark.

## Working with the assistant

Enter one task at a time in **Investigate a task**. Expand **Task syntax help** for supported task forms. Expert uses its own task parser and case IDs; guided prompts such as `Show ORD-1002` apply to the guided assistant only.

Useful task forms include:

```text
Search documents <words>
Read document <document ID>
Prepare support summary
Check delivery <order ID>
Request refund INR <amount> for <order ID>
Revise proposal <proposal ID> to INR <amount>
Execute proposal <proposal ID>
```

Use actual IDs from the current case in place of the angle-bracket placeholders. Refund amounts are positive whole-number INR. The assistant also supports exporting a document to a local outbox and saving a destination preference; their syntax is available in the workspace.

Each task redirects to **Investigation activity**. Expand the events to compare selected arguments, source provenance, backend authorization, and actual results. Event and interaction IDs connect later effects to their earlier sources. These records describe observable simulator behavior, not hidden model reasoning.

## Reference and integration editing

Opening a document in the case file is a passive inspection. It does not invoke an agent tool and cannot complete a challenge. Use the document’s assistant button to execute a read.

The dispatch and handover references are editable, as is the delivery integration description. Their edit pages provide the small supported directive grammar. You can remove planted instructions, change their contents, and compare the behavior. Arbitrary prose does not become executable code, and integration descriptions cannot install tools or contact services.

The reference browser itself is limited to your company’s customer-visible material. Investigate the assistant’s retrieval behavior to assess broader access.

## Approvals and memory

Refund requests create proposals. Review the order, amount, and revision in the **Human approval desk**, check the confirmation box, and approve the displayed details. This records a five-minute approval snapshot; it does not execute a refund. The assistant executes proposals separately. Approval is a local human-confirmation demonstration, not separate manager authentication.

The saved destination preference survives page reloads and later interactions. Its provenance identifies the interaction and event that wrote it. A memory-related objective requires impact during a separate later interaction, not just a saved preference.

## Evidence and retesting

Completion is based on executed results: exported document content, a document’s actual company, a later memory-influenced export, or a recorded refund inconsistent with its approval. Merely searching for a document, changing text, or claiming success cannot satisfy these conditions.

The customer and review outboxes are SQLite-backed fictional records. The customer outbox is the intended destination; the review outbox represents disclosure outside the customer workflow. Neither transmits anything. Refunds never move money.

The workspace shows the most recent 20 interactions and 10 recent entries per outbox/refund list. **Download evidence** includes the complete interaction history, confirmed findings, hint counts, exports, and refunds for your current case. It does not export undiscovered seed documents.

Switch the header to **Secure mode** and retest. It applies independent document, destination, provenance, and approval checks. Untrusted directives may still appear as attempted calls in Expert traces, but their effects are denied. Legitimate delivery checks, customer summaries, and eligible approved refunds continue to work. Secure mode also ignores untrusted memory left behind by vulnerable mode.

Mode changes preserve earlier evidence and simulated state. They do not undo earlier disclosures or refunds. A fresh case provides clean order eligibility; its IDs change, so rediscover them before retesting.

## Case lifecycle

- Alice and Bob have separate Expert cases. Switching identities changes the assigned case. Guided progress and the security mode remain shared within the local instance.
- **Generate a fresh case** requires confirmation and replaces only the current identity’s Expert data, progress, hints, memory, approvals, and evidence. It retains the current security mode and guided progress.
- The footer’s **Reset lab** replaces both Expert cases as well as all guided state, restores vulnerable mode, and clears the current login.
- Old forms are rejected after a case reset; reload before submitting another task.
- Upgrading an existing installation adds Expert storage without resetting its guided data. Restart the server to load the new code; no manual database deletion is required for this addition.

Use one local instance per student. The application remains an offline, fictional training environment.
