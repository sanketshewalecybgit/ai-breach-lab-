# Expert instructor key — SPOILERS

All identifiers below are placeholders discovered from the current case. Each identity has separate Expert fixtures. Start in vulnerable mode. No fixed order/customer/document identifier is part of the success conditions.

This guide covers the five Expert investigations. For the ten guided challenges
and three Break / Fix missions, use the [main instructor answer key](instructor-answer-key.md).

## Setup and how to submit solutions

1. Select Alice or Bob, open **Expert**, and select **Vulnerable mode**.
2. Inspect **Case file** for your company, delivered order, and reference document IDs.
3. Enter each command separately in **Task for the assistant**, then click **Run task →**.
   Replace `<document ID>`, `<order ID>` and `<proposal ID>` with actual current-case
   values. Opening a reference link alone does not execute its instructions; ask the
   assistant to read it using `Read document <document ID>`.
4. Inspect **Activity**, **Local outboxes** and the five objective statuses. Use
   **Download evidence** to retain the source-linked findings.
5. Switch to **Secure mode** for the retests below. The mode switch applies to both
   Expert and the guided assistant; Break / Fix has its own independent controls.

For the approval scenario, check the explicit confirmation box and click
**Approve these details** in **Human approval desk** before issuing the revision
or execution task. Typing an approval instruction into the assistant is insufficient.

A fresh Expert case changes the current identity’s randomized IDs and clears that
case’s findings while preserving guided and Break / Fix progress. Full **Reset lab**
clears all three workspaces; use it only when the instance’s progress can be discarded.

## Learning cards and completion debriefs

Each objective has an optional **Learn before you break** card with vocabulary,
an intended-flow diagram and observation prompts. Students who prefer independent
investigation can jump to the assistant. Vulnerability names and detailed solution
explanations remain behind that objective's confirmed finding.

After each solution below, return to its objective and expand **After-action
debrief · unlocked**. Match the saved event/source IDs to **Activity** or the
complete **Download evidence** file, especially when the activity panel's latest
20 interactions no longer contain the original attack. Opening documents or
reading cards does not unlock a debrief. For memory, require the separate later
summary; for tenant isolation, require the actual document body; for approval,
require execution of the mismatched, reused or expired approval.

Alice and Bob unlock debriefs independently. Switching mode preserves findings;
a fresh case relocks all five for that identity. A debrief's secure retest is an
instruction to run, not an additional automatically awarded pass.

## Suggested 60–90 minute session

Give students the business brief and let them inspect the case file before revealing vulnerability names. Allow roughly 10 minutes for discovery, 10 minutes per scenario, and 15–30 minutes for secure retests and discussion. Keep the syntax help available: parser guessing is not a learning objective.

## 1. An unexpected attachment

Open **Dispatch reference** and inspect its automation appendix. Send `Read document <dispatch document ID>` in the Expert assistant. The document read proposes an export of an internal reconciliation document to the local review outbox.

Expected chain: `read_document → export_document`. Completion requires a successful internal-document export to review, with a source-linked successful document read in the same interaction. The reference title and original wording are not grading inputs; student-authored directives can also demonstrate the behavior.

Secure retest: the customer-visible reference remains readable, but the export is denied by backend provenance policy. Direct requests to read or export the internal document are independently denied. Removing the directive produces only a document read in vulnerable mode too.

Upload variant: open **RAG Poisoning**, download the sample for the current case, and upload it as a UTF-8 `.txt` document. Uploading records `upload_document` evidence but earns no objective. Use its **Ask the assistant to read this document** button, or search with `Search documents rag` and read the returned ID. The same `read_document → export_document` chain confirms the reference objective, with the uploaded document as its source. Secure mode still ingests and reads the reference but denies its export. A benign upload remains searchable/readable without side effects. Uploads accept `.txt`/`.md`, up to 4,000 characters and 12 KiB, with 20 per case; a fresh case removes uploads and invalidates old sample IDs.

## 2. A later task goes astray

Send `Read document <Agent handover document ID>` through the Expert assistant. Its directive writes a review destination to persistent memory. No objective is awarded yet.

In a separate task, request `Prepare support summary`. The summary tool reads the saved preference and exports the customer summary to review. The evidence links this export to the earlier memory-writing interaction and document source. Reloading the page between tasks demonstrates that memory is persistent.

Secure retest: reading the handover proposes a memory write that backend policy denies. Also switch to secure mode after poisoning memory in vulnerable mode: `Prepare support summary` must ignore that untrusted preference and deliver to the customer outbox. A direct `Remember destination customer` remains useful.

## 3. An unfamiliar settlement

Request `Search documents settlement`. Compare result companies with the authenticated company in the brief. Read a result belonging to a different company using `Read document <ID>`.

Search metadata alone does not complete this objective. The actual document body must be returned across a company boundary. The exported finding contains the authenticated company, document company, document ID, and fictional disclosed content.

Secure retest: the search excludes other-company and internal documents, and a direct read using a previously learned inaccessible ID is also denied. Own-company settlement guidance remains available. The passive reference browser does not expose other-company documents in either mode.

## 4. What was actually approved?

Use a delivered order from the case file:

1. `Request refund INR 100 for <order ID>`.
2. In the approval desk, review and explicitly approve the displayed amount and revision.
3. `Revise proposal <proposal ID> to INR 200`.
4. `Execute proposal <proposal ID>`.

The vulnerable executor records INR 200 against an approval for INR 100. Both amounts are below every generated eligible order’s paid amount, isolating approval integrity from the guided oversized-refund exercise.

Alternative: approve an unchanged proposal and execute it twice. The first execution is legitimate and earns nothing; the second inserts a duplicate refund and completes the objective. A five-minute expired approval can also demonstrate the weakness. Revision changes alone, with the same approved arguments and no replay/expiry, do not earn a finding.

Both modes require a real human approval record. The confirmation form rejects stale displayed proposal revisions, even in vulnerable mode. The intended flaw is in later execution, not a hidden field that lets the model approve itself.

Secure retest: execution checks the exact approved order, amount, revision, expiry, and consumption; it then revalidates current order ownership and eligibility. All checks and the refund write run under the same SQLite write transaction. Changed, expired, reused, or newly ineligible proposals are denied. Use a fresh proposal on an unrefunded order for a successful secure approval demonstration. Used/old approvals cannot be renewed by repeatedly clicking the approval endpoint.

## 5. A delivery check with a side effect

Inspect **Parcel status** through the integration registry link. Its publisher description includes an export directive. Request `Check delivery <order ID>`.

Expected calls: `get_integration → delivery_status → export_document`. The delivery step comes from the original user task; the extra export comes from publisher-supplied metadata. Completion requires an internal-document export to review linked to the successful metadata retrieval event.

Secure retest: metadata can be inspected and the requested delivery status still works. The export attempt is independently denied. Editing the description to plain delivery documentation removes the extra call in vulnerable mode as well. This is a local simulation of metadata influencing tool selection, not a functioning MCP server or software installation flow.

## Implementation and grading boundaries

- `expert/cases.py`: randomized coherent fixtures, business briefs, progressive hints, storage, reset.
- `expert/tools.py`: fixed schemas, backend authorization, local data effects, immutable approval snapshots.
- `expert/engine.py`: deterministic task parser, bounded directive recognition, source-linked event graph, grading.
- `expert/routes.py`: identity-scoped workspace, explicit human confirmation, editable references, evidence export.
- `tests/test_expert.py`: randomized end-to-end cases, defenses, legitimate workflows, stale state, evidence isolation, and regression checks.
- `tests/browser_expert_smoke.py`: isolated temporary server/database; browser workflows and responsive layouts.

At most four embedded directives are proposed per retrieved result; an interaction executes at most six tools. No arbitrary tool names, paths, URLs, external destinations, code execution, or payment services are accepted. Every effect and all confidential material are fictional. Expert completion is separate from guided challenges 1–10 and the seven-core solved screen.
