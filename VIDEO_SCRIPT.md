# Demo video script — target 2:50

Language: English  
Format: AI-generated intro still followed by a live screen recording with AI-assisted or human voice, no background music  
Intro/thumbnail asset: `assets/margelis-governor-build-week-visual.png`

The abstract visual contains no synthetic person. The live Human Gate action is performed by Tomas on screen.

## 0:00–0:12 — Problem and thesis

“AI agents can propose real actions. Margelis Governor adds a decision boundary and evidence: draft, gate, correct, sign, learn, and prove.”

Show the live URL and the six stages. Point to **Synthetic data only** and the message that no email is sent.

## 0:12–0:38 — Governed GPT‑5.6 draft

Select **Start governed draft**.

“GPT‑5.6 Terra is the governed drafting agent. It proposes a synthetic outreach email. Because this is an external communication, deterministic policy classifies it as R3.”

Point to the model/mode label, R3, and the proposed-not-sent status.

## 0:38–1:00 — Claim Guard stop

“The draft contains unsupported numerical and universal claims. Deterministic Claim Guard rules stop the action. GPT‑5.6 may add advisory context, but cannot remove the block.”

Show the finding, rule identifier, excerpt, and STOP status.

## 1:00–1:35 — Human correction and signed evidence

Briefly point to the disabled **Approve + sign** button while the draft is unchanged. Change only `95%` to `84%`, select **Approve + sign**, and show the still-blocked rejection. Then replace the full blocked sentence with: **“The pilot will measure whether the workflow reduces repetitive follow-up.”** Select **Approve + sign** again.

“I replace the unsupported statement myself. Human Gate rejects unchanged or still-blocked text. The corrected artifact is added to a hash chain and signed with a local Ed25519 demo key.”

Select **Verify chain**.

“The original chain verifies.”

Select **Run tamper check**.

“An edited copy fails while the stored ledger remains unchanged.”

## 1:35–2:08 — Correction-to-eval regression

Select **Compile eval + rerun agent**.

“Exam Runner converts the correction into a structured eval and bounded context; it does not retrain the model. The original fails, a fresh GPT‑5.6 draft passes, and all baseline cases remain green.”

Point to **FAIL → PASS → GREEN**, then show the actual rerun artifact and event trail.

## 2:08–2:38 — How this was built with Codex

Show the primary Codex build thread or test output for 2–3 seconds. Do not show API keys or other secrets.

“I built this in Codex from a written specification, hard isolation rules, and a definition of done. Codex implemented the flow engine, deterministic Claim Guard, signed ledger, Exam Runner, web interface, tests, and Docker deployment, then tested and repaired the implementation until twenty-two tests passed. Blocking remains deterministic, GPT‑5.6 is advisory at the gate, and no production Margelis system was touched.”

## 2:38–2:50 — Close

“This is a narrow, testable pattern for agent developers: consequential operations require a human boundary, signed evidence, and reproducible checks that make expert corrections useful on the next run.”

End on the live regression result. Keep the hosted URL and repository link in the YouTube description.
