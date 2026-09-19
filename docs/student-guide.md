# AI BreachLab — student guide

Welcome to **AI BreachLab**, a hands-on workshop on **Advanced AI Attack Surfaces**. You are an authorized tester of NovaCart Support, a fictional customer-support application. Investigate how natural-language requests become backend actions, then compare the same requests under defensive controls.

## Rules

Run only on localhost. Use only the supplied fictional accounts and lab data. Do not enter real credentials, payment details or private information. Do not target other hosts. Use the AI application to complete challenges: do not edit cookies or database records. All refunds are simulations and all tickets stay local.

## Getting started

1. Open `http://127.0.0.1:5000`.
2. Select Alice on the demo identity page. No password is needed.
3. Read your profile and orders to understand your authenticated identity.
4. Open the challenge dashboard and select a challenge.
5. Read the story and objective, then open the assistant.

The header always shows your current identity and mode. Each student should use a separate local instance. Switching between Alice and Bob does not reset the shared lab progress.

## Architecture

```text
User → Web frontend → AI API → Mock agent → Tool selection
     → Backend functions → SQLite data / simulated actions
```

The architecture page lists available tool signatures. The mock agent is rule-based and deterministic; it does not connect to a real model. Supported tasks include profile lookup, orders, refunds, support notes, tickets and shipping. Include an identifier when a task needs one. Ask one task at a time. Refund amounts use whole-number INR values.

## Following evidence

After each response, expand **AI Debug / Tool Trace**. Compare:

- Your authenticated identity and original request.
- The simulator's decision label, selected tool and arguments.
- Whether another tool call came from your request or retrieved content.
- The independent authorization result and actual backend output.
- The final response visible to you.

The debug panel reports executed events. It does not show hidden model reasoning. Try to identify which trust boundary was crossed and what the backend should have checked.

## Tickets and hints

The support-ticket inbox lets you open fictional customer messages or ask the assistant to summarize them. You may create your own lab-only ticket content. Reading a ticket directly does not itself solve a challenge; the relevant agent/tool behavior must occur.

Each challenge has three manually revealed hints. Start with the objective and architecture, then reveal hints one at a time if needed. Usage is saved, with no score penalty. Full solutions are not included in this guide.

## Progress and retesting

The server awards completion from actual tool results, not from a claim that an attack worked. A successful interaction may satisfy more than one challenge. Review the success evidence, root cause and remediation on the challenge page. The dashboard counts seven mandatory challenges; the eighth is optional.

Once all mandatory challenges are complete, open the **LAB SOLVED** screen. Then select **View defensive version** and switch to secure mode. Retest requests and compare traces. An eligible secure refund requires a separate human confirmation before the simulated action runs. No real money is ever moved.

Secure mode preserves earlier progress and fake actions. If a prior refund affects a retest, reset and switch to secure mode again.

## Reset

Open **Reset lab** in the footer. Confirm the reset and select a demo identity again. The reset removes progress, hints, refunds, approvals, custom tickets and execution traces, restores seed data and original tickets, and returns the lab to vulnerable mode.

Discuss at the end: which parts of the system proposed actions, and which parts should have been responsible for authorizing them?

## Choose a difficulty track

Start with **Beginner** (challenges 1–2) to compare identity, ownership, and tool scope. Move to **Intermediate** (3–5) to inspect actions, business rules, and context exposure. **Advanced** (6–8) follows injected instructions through retrieved content and tool chains; challenge 8 is optional.

Use the three track cards or the difficulty filters on the mission board. Each challenge displays its level and an investigation approach. All levels are available from the start, and all retain three progressive hints. Difficulty groups the investigations by complexity; vulnerable/secure mode independently controls the backend defenses.

Your level progress is saved automatically from executed evidence. An attack chain may complete challenges in more than one level. Seven core challenges complete the lab; the optional advanced challenge counts toward its track but is not required for the solved screen.
