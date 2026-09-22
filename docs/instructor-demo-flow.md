# Instructor demo flow — 30 minutes

Prepare one local instance per student. Install dependencies before class; the running lab is offline. Start the server, select Alice, and reset the demo instance before delivery. Keep the answer key separate from the student UI.

| Time | Delivery sequence |
|---|---|
| 0–3 min | Introduce scope, fictional data and NovaCart. Open `/architecture`; distinguish the user, AI API, mock agent, tool dispatcher and database. Explain that the rule-based agent makes outcomes reproducible. |
| 3–7 min | Challenge 1: compare Alice's identity with a different order owner. Expand the trace and distinguish authentication from authorization. |
| 7–12 min | Challenges 3–4: demonstrate an unauthorized simulated refund and an oversized refund. Contrast valid JSON/schema with valid business actions. Show the saved refund event. |
| 12–17 min | Challenge 2: explore the global customer-search tool. Ask whether a customer-facing assistant should possess that capability at all. |
| 17–22 min | Challenge 5: show the support note result and fictional metadata. Discuss minimizing retrieved data before it enters context. |
| 22–27 min | Challenges 6–7: summarize the injected ticket and forwarded ticket. Follow the source labels from ticket data to additional tools. Optional extension: shipping-output injection, challenge 8. |
| 27–30 min | Open the solved screen and defensive comparison. Toggle secure mode; repeat cross-user lookup, oversized refund and injected-ticket requests. Show backend denial and filtered metadata. End with “The model is not the security boundary.” |

If demonstrating a legitimate secure refund after the attack sequence, reset first, select Alice, enable secure mode and request a modest refund on an eligible own order. Explain `requires_approval = true`; explicitly approve in the panel. Repeating the action is then rejected. This confirmation is a teaching demo, not a separate staff approval system.

Challenge 7's forwarded ticket can also solve challenges 2, 5 and 6. To preserve the lesson order, demonstrate it last. Optional challenge 8 can solve challenge 2 because the unrelated global lookup is itself an excessive-agency event.

The simulator deliberately recognizes a small injection grammar; it is not a general LLM jailbreak benchmark. Distinguish model manipulation (following retrieved text) from application impact (weak backend policy permits the powerful call). Secure mode both changes handling of untrusted text and enforces independent policy, so the lesson is not merely “ask the model to behave.”

## Break / Fix extension — 20 minutes

Use the [Break / Fix answer key](instructor-answer-key.md#break--fix-complete-instructor-walkthrough)
for exact prompts, defense names, Bob variants and expected traces. Select Alice
and open **Break / Fix**. These exercises use isolated fixtures and do not require
resetting the guided demo. The global mode switch has no effect in this workspace.

| Time | Delivery sequence |
|---|---|
| 0–5 min | **Cross the account boundary:** run `Show me profile 1002.`, replay once without defenses, then select **Check object ownership** and replay. Compare identical arguments with allowed and blocked results. |
| 5–10 min | **Turn a ticket into an instruction:** run `Summarize ticket 2.`. Demonstrate that ownership alone fails; replace it with **Reject instructions from retrieved content**. Compare the `user` and `ticket:2` source labels. |
| 10–15 min | **Expose the hidden support note:** run `Retrieve the internal note for ORD-1001.`. Select **Remove internal metadata** and replay. Show that the support note remains available. |
| 15–20 min | On a confirmed attack, select **Disable every tool** and replay. Discuss **ATTACK STOPPED, SERVICE BROKEN** and the failed legitimate checks. Remove the blanket block, restore a targeted fix, and review all three verified missions. |

Have students explain the failing boundary, the chosen control, and the evidence
that legitimate requests still work. A new vulnerable attack replaces that mission’s
saved result; use replay to compare defenses against the existing baseline. Passing
the saved attack and four checks is bounded evidence, not universal protection.

## Expert extension

For a separate 60–90 minute session, open the Expert workspace and use the [Expert instructor key](expert-instructor-key.md). Its five randomized investigations have independent progress and evidence. The guided 30-minute sequence above remains available.
