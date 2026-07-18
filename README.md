# Margelis Governor — Build Week 2026

![Abstract visualization of the governed operation flow](assets/margelis-governor-build-week-visual.png)

**AI agent operations with human approval, cryptographic evidence, and a correction-to-eval regression loop.**

This repository is an isolated, self-contained demonstration. A GPT‑5.6 sales drafting action is classified as R3, stopped when deterministic controls find an unsupported marketing statement, corrected by a human, recorded in an Ed25519-signed Evidence Passport, and converted into a structured eval for a fresh agent rerun.

The demo does not send email, connect to production Margelis services, or use customer data.

## What it demonstrates

1. A governed drafting agent proposes an email for two synthetic organizations.
2. A deterministic Governor classifies the proposed external action as R3.
3. Claim Guard blocks unsupported numerical and universal wording.
4. Human Gate requires a corrected artifact before approval.
5. An append-only JSONL Evidence Passport records the flow and signs every record with a local Ed25519 key.
6. Exam Runner converts the correction into structured eval data and bounded correction context.
7. A fresh agent draft is evaluated. The original must fail the new case, the rerun must pass it, and all baseline cases must remain green.

The correction loop changes prompt context and the eval suite. It does not change the base model's weights.

## Built for Build Week

All implementation in this repository was created during the 2026 submission period:

- dependency-light Python HTTP API and state machine;
- GPT‑5.6 Responses API adapter and visibly labelled fixture adapter;
- R0–R5 deterministic action classifier;
- deterministic Claim Guard with an optional model advisory signal that cannot weaken a rule block;
- Human Gate that rejects unchanged or still-blocked copy;
- Ed25519 signer, canonical records, per-flow hash chain, verifier, and tamper demonstration;
- correction compiler, generated eval, actual rerun, and baseline regression suite;
- responsive single-page demonstration interface with a manual Human Gate edit;
- original AI-generated abstract visual for the video intro and thumbnail, with provenance documented under `assets/`;
- network-free tests, repository hygiene checks, container packaging, and submission materials.

## Prior Margelis concepts reused

The names and product concepts **Human Gate**, **Governor**, **Claim Guard**, and **Evidence Passport** existed as prior Margelis design work. No production code, credentials, customer data, deployment configuration, or private keys were copied into this repository. Each component was re-implemented here as new, isolated Build Week code.

## Run from a clean clone

Requirements: Python 3.11 or newer and `pip`.

```bash
git clone <repository-url>
cd MARGELIS_GOVERNOR_BUILD_WEEK_2026
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python server.py
```

Open `http://127.0.0.1:8000`.

The default is **fixture mode**. It is deterministic, requires no network or API key, and is clearly identified in the interface. It exists for reproducible testing and does not represent a live model call.

### Live GPT‑5.6 mode

Copy `.env.example` to `.env`, keep it untracked, and set:

```dotenv
OPENAI_API_KEY=<server-side-secret>
OPENAI_DRAFT_MODEL=gpt-5.6-terra
OPENAI_REVIEW_MODEL=gpt-5.6-terra
MARGELIS_AGENT_MODE=live
```

Then run `python server.py`. API keys must remain server-side. The browser never accepts or stores a key.

The first live call drafts the intentionally unsafe synthetic artifact. A second advisory review may add review findings but cannot remove deterministic Claim Guard findings. After human correction, a fresh GPT‑5.6 call receives the bounded correction example and produces the artifact evaluated by Exam Runner.

Before deployment, run the opt-in live integration check:

```bash
python scripts/live_smoke.py
```

It uses a temporary data directory and exits unless the live first draft is blocked, the corrected rerun passes, prior evals remain green, and the Evidence Passport verifies.

## Test and verify

```bash
python -m pytest
python scripts/verify_repo.py
```

The suite covers:

- R3 classification and R5 default blocks for out-of-scope domains;
- deterministic claim detection and advisory failure behavior;
- Human Gate refusal of unchanged or still-unsafe artifacts;
- correction-to-eval fail-before/pass-after behavior;
- prior-case regression integrity;
- Ed25519 signature and chain verification;
- payload, link, and signature tampering;
- isolated per-flow evidence chains;
- the full HTTP hero flow;
- user-facing claims, common secret markers, and synthetic-data hygiene.

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Mode and service health |
| `POST` | `/api/flow/start` | Run draft, risk classification, and Claim Guard |
| `POST` | `/api/flow/{id}/correct` | Correct, approve, and sign |
| `POST` | `/api/flow/{id}/rerun` | Compile eval and rerun the agent |
| `GET` | `/api/flow/{id}` | Inspect current state |
| `GET` | `/api/flow/{id}/passport` | Read Evidence Passport records |
| `GET` | `/api/flow/{id}/verify` | Verify chain and signatures |
| `POST` | `/api/flow/{id}/tamper-check` | Verify an edited in-memory copy is rejected |

## GPT‑5.6 and Codex usage

- **GPT‑5.6 Terra** is the governed drafting agent and optional claim-review advisory. It does not make the final risk or approval decision.
- **Codex** implemented and iterated on this repository from the Build Week specification, ran the test/repair loop, and prepared the interface, clean-run instructions, and submission materials.
- Deterministic code owns action classification, blocking decisions, signature verification, and eval assertions.
- The model is never asked to generate executable tests. Exam Runner stores structured JSON-compatible eval data and uses fixed evaluators.

## Evidence and trust boundaries

- The private Ed25519 key is generated at `.demo-data/signing/demo-key.pem`, file mode `0600`, and ignored by Git.
- The public key and key identifier are included for local verification.
- The signature proves that records remained intact under the local demo key. It does not independently authenticate the human's legal identity and is not presented as a legal electronic signature.
- Each flow has a separate chain. Records include sequence, previous hash, actor label, decision, UTC time, artifact hash, payload hash, key identifier, record hash, signature, and public key.
- The tamper check edits an in-memory copy. It does not alter the real ledger.

## Deployment

The included `Dockerfile` and `Procfile` support a single server deployment. Configure `MARGELIS_AGENT_MODE=live` and the OpenAI key as host-managed server secrets. The public demo must use a durable HTTPS URL; static-only hosting and browser-entered API keys are outside this design.

**Hosted URL:** https://margelis-governor-build-week-2026.onrender.com/

The hosted service was verified in live GPT-5.6 mode on 2026-07-18: the R3 draft was blocked, corrected and signed, the generated correction eval failed on the original draft and passed on the fresh rerun, all prior evals remained green, and the tamper check rejected an edited record.

## Assumptions log

1. The submitted experience is one fixed synthetic sales scenario; it is not a general outbound system.
2. R0–R5 meanings are demo policy labels, not a statutory risk taxonomy.
3. A percentage without an attached evidence marker is blocked in the demo, even when it could be true elsewhere.
4. The model advisory can add review information but never remove a deterministic block.
5. The human actor identifier is self-asserted because the demo has no identity provider.
6. The correction becomes an eval and bounded prompt example; it is not model retraining.
7. Fixture mode proves deterministic mechanics. The hosted Build Week experience must use live mode to demonstrate GPT‑5.6.
8. No proposed external message is transmitted by this repository.
9. The interface preloads the blocked artifact for review but provides no automatic correction; the human must make a material text edit before approval is enabled.

## Repository status

- Production Margelis connections: none
- Real customer data: none
- External action execution: none
- Private keys committed: none
- License: MIT
