# Demo video script — target 2:50

Language: English  
Format: AI-generated intro still followed by a live screen recording with AI-assisted or human voice, no background music  
Intro/thumbnail asset: `assets/margelis-governor-build-week-visual.png`

The abstract visual contains no synthetic person. The live Human Gate action is performed by Tomas on screen.

## 0:00–0:12 — Problem and thesis

“AI agents can draft and propose real actions, but a useful operational system also needs a decision boundary and evidence. Margelis Governor demonstrates one complete loop: draft, gate, correct, sign, learn, and prove.”

Show the live URL and the six stages. Point to **Synthetic data only** and the message that no email is sent.

## 0:12–0:38 — Governed GPT‑5.6 draft

Select **Start governed draft**.

“GPT‑5.6 Terra is the governed drafting agent. It receives a fixed synthetic campaign brief and produces this proposed outreach email. The action is classified as R3 because it is an external communication.”

Point to the model/mode label, R3, and the proposed-not-sent status.

## 0:38–1:00 — Claim Guard stop

“The campaign brief contains an unsupported numerical and universal statement. Deterministic Claim Guard rules detect it and stop the action. A model advisory may add context, but it cannot remove this block.”

Show the finding, rule identifier, excerpt, and STOP status.

## 1:00–1:35 — Human correction and signed evidence

In the prefilled draft, manually replace the blocked sentence with: **“The pilot will measure whether the workflow reduces repetitive follow-up.”** Then select **Approve + sign**.

“I correct the unsupported statement myself. Human Gate runs Claim Guard again and refuses unchanged or still-blocked text. Only the corrected artifact is approved. Every stage is written to a hash chain and signed with a local Ed25519 demo key.”

Select **Verify chain**.

“The original chain verifies.”

Select **Run tamper check**.

“An edited copy fails verification while the stored ledger remains unchanged.”

## 1:35–2:08 — Correction-to-eval regression

Select **Compile eval + rerun agent**.

“Exam Runner converts the human correction into a structured eval and bounded correction example. It does not retrain the model. The original artifact fails the generated eval. A fresh GPT‑5.6 draft is produced with the correction context, Claim Guard evaluates the actual output, and all baseline cases run again.”

Point to **FAIL → PASS → GREEN**, then show the actual rerun artifact and event trail.

## 2:08–2:38 — How this was built with Codex

Show the primary Codex build thread or test output for 2–3 seconds. Do not show API keys or other secrets.

“I built this project in Codex from a written Build Week specification with hard isolation rules and a definition of done. Codex implemented the flow engine, deterministic Claim Guard, Ed25519 evidence ledger, Exam Runner, web interface, tests, and Docker deployment. It repeatedly tested and repaired the implementation until twenty-two tests passed. Two constraints shaped the result: deterministic rules own blocking decisions, while GPT‑5.6 can only add advisory context; and every governance component was re-implemented inside this isolated repository without touching any production Margelis system.”

## 2:38–2:50 — Close

“This is a narrow, testable pattern for agent developers: consequential operations require a human boundary, signed evidence, and reproducible checks that make expert corrections useful on the next run.”

End on the live regression result. Keep the hosted URL and repository link in the YouTube description.
