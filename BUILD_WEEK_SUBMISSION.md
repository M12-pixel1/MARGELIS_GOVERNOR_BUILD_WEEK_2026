# Build Week submission draft

## Project

**Margelis Governor — Verified Agent Operations**

Track: **Developer Tools**

One-line description: AI agent operations with human approval, cryptographic evidence, and a correction-to-eval regression loop.

## What we built

Margelis Governor is a working safety and evidence demonstration for AI agent operations. GPT‑5.6 is the governed drafting agent. A deterministic control layer classifies a proposed synthetic external email as R3, detects an unsupported marketing statement, and stops the action. A human must correct the draft before it can be approved. The resulting flow is recorded in an Ed25519-signed, hash-chained Evidence Passport.

The correction is then compiled into a structured eval and bounded correction context for a fresh GPT‑5.6 draft. Exam Runner shows the original artifact failing the new case, evaluates the actual rerun, and reruns all prior cases. The interface reports PASS only when the new artifact is clean and the prior suite remains green.

The system never sends the proposed email. All organizations, names, addresses, and operational details are synthetic.

## Why it matters

Teams adopting agents need more than a final answer. They need an observable approval boundary, evidence of what happened, and a way to turn expert corrections into reproducible regression checks. This demo makes that loop concrete and testable for agent developers and operational teams.

## Build Week work

All code, interface, tests, API integration, evidence signing, Exam Runner, and packaging in this repository were created during the submission period. Prior Margelis work contributed four concept names: Governor, Human Gate, Claim Guard, and Evidence Passport. No prior implementation or production asset was copied.

## How GPT‑5.6 and Codex were used

- GPT‑5.6 Terra produces the synthetic first draft and the fresh post-correction rerun.
- A second GPT‑5.6 advisory can add claim-review context but has no authority to weaken deterministic controls.
- Codex implemented the isolated repository, tests, repair loop, web experience, and submission documentation from the project specification.
- Fixed code, not model-generated executable logic, owns the R-class, blocking, signature verification, and eval assertions.

## Demonstrated proof

- full hero flow runs through one public interface;
- unsupported draft is stopped before approval;
- unchanged and still-unsafe edits are rejected;
- correction creates a structured eval;
- stored original fails and fresh rerun must pass;
- all prior evals rerun;
- Evidence Passport verifies;
- edited record copy fails verification;
- network-free tests reproduce the full flow.

## Testing instructions

1. Open the hosted URL.
2. Select **Start governed draft**.
3. Inspect the R3 decision and Claim Guard findings.
4. Apply or edit the suggested human correction.
5. Select **Approve + sign**.
6. Verify the signed evidence chain and run the tamper check.
7. Select **Compile eval + rerun agent**.
8. Confirm the original is FAIL, the actual rerun is PASS, and the prior suite is GREEN.

Repository setup and local verification commands are in `README.md`.

Hosted URL: **pending deployment**

