const state = { flow: null, mode: "unknown" };

const byId = (id) => document.getElementById(id);

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function setState(id, label, tone = "neutral") {
  const node = byId(id);
  node.textContent = label;
  node.className = `state state-${tone}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function suggestedCorrection(flow) {
  let text = flow.draft.text;
  const replacement = "Nimbus Ledger is designed to streamline onboarding workflows.";
  for (const finding of flow.claim_review.findings) {
    if (finding.severity === "block") text = text.replace(finding.excerpt, replacement);
  }
  return text;
}

function renderFlow(flow) {
  state.flow = flow;
  byId("draftText").textContent = flow.draft.text;
  byId("draftText").classList.remove("muted");
  byId("draftMeta").innerHTML = `
    <span>${escapeHtml(flow.draft.model)}</span>
    <span>${escapeHtml(flow.draft.mode.toUpperCase())}</span>
    <span>Flow ${escapeHtml(flow.flow_id.slice(0, 8))}</span>`;
  setState("draftState", "Created", "good");

  byId("riskClass").textContent = flow.risk.risk_class;
  byId("riskDisposition").textContent = flow.risk.disposition.replaceAll("_", " ");
  const blocked = flow.claim_review.blocked;
  setState("gateState", blocked ? "Stopped" : "Review", blocked ? "bad" : "warn");
  byId("findings").classList.remove("muted");
  byId("findings").innerHTML = flow.claim_review.findings.length
    ? flow.claim_review.findings.map((finding) => `
      <div class="finding">
        <strong>${escapeHtml(finding.category.replaceAll("_", " "))}</strong>
        <p>${escapeHtml(finding.excerpt)}</p>
        <small>${escapeHtml(finding.rule_id)} · ${escapeHtml(finding.rationale)}</small>
      </div>`).join("")
    : '<div class="finding finding-clear">No blocking deterministic finding.</div>';

  if (flow.stage === "BLOCKED") {
    byId("correctionText").disabled = false;
    byId("correctionText").value ||= suggestedCorrection(flow);
    byId("safeEditButton").disabled = false;
    byId("approveButton").disabled = false;
    setState("humanState", "Action needed", "warn");
  }

  if (["SIGNED", "REGRESSION_PASSED", "REGRESSION_FAILED"].includes(flow.stage)) {
    byId("correctionText").value = flow.corrected_text;
    byId("correctionText").disabled = true;
    byId("safeEditButton").disabled = true;
    byId("approveButton").disabled = true;
    byId("rerunButton").disabled = false;
    byId("verifyButton").disabled = false;
    byId("tamperButton").disabled = false;
    setState("humanState", "Approved", "good");
    setState("evidenceState", "Signed", "good");
    const record = flow.approval_record;
    byId("evidenceSummary").classList.remove("muted");
    byId("evidenceSummary").innerHTML = `
      <div><span>Key ID</span><code>${escapeHtml(record.key_id)}</code></div>
      <div><span>Record hash</span><code>${escapeHtml(record.record_hash.slice(0, 24))}…</code></div>
      <div><span>Decision</span><strong>${escapeHtml(record.decision.replaceAll("_", " "))}</strong></div>`;
    byId("humanMessage").textContent = "Corrected artifact approved; no external action was executed.";
    byId("humanMessage").className = "inline-message message-good";
  }

  if (flow.regression) renderRegression(flow.regression);
  renderEvents(flow.events);
}

function renderRegression(report) {
  const beforeTone = report.before.passed ? "pass" : "fail";
  const afterTone = report.after.passed ? "pass" : "fail";
  setState("examState", report.all_green ? "Passed" : "Failed", report.all_green ? "good" : "bad");
  setState("proofState", report.all_green ? "Proven" : "Needs repair", report.all_green ? "good" : "bad");
  byId("regressionView").classList.remove("muted");
  byId("regressionView").innerHTML = `
    <div class="result-card result-${beforeTone}">
      <span>Before correction context</span><strong>${report.before.passed ? "PASS" : "FAIL"}</strong>
      <small>${escapeHtml(report.before.details.join(" · "))}</small>
    </div>
    <div class="result-arrow">→</div>
    <div class="result-card result-${afterTone}">
      <span>Fresh agent rerun</span><strong>${report.after.passed ? "PASS" : "FAIL"}</strong>
      <small>${escapeHtml(report.after.details.join(" · "))}</small>
    </div>
    <div class="result-card result-${report.prior_cases_green ? "pass" : "fail"}">
      <span>Prior eval suite</span><strong>${report.prior_cases_green ? "GREEN" : "FAILED"}</strong>
      <small>${report.prior_cases.length} baseline cases executed</small>
    </div>
    <div class="rerun-artifact">
      <span class="label">Actual rerun artifact · ${escapeHtml(report.rerun_artifact.model)} · ${escapeHtml(report.rerun_artifact.mode)}</span>
      <pre>${escapeHtml(report.rerun_artifact.text)}</pre>
    </div>`;
}

function renderEvents(events) {
  byId("eventTrail").classList.remove("muted");
  byId("eventTrail").innerHTML = events.map((event) => `
    <div class="event-row">
      <span class="event-seq">${String(event.seq).padStart(2, "0")}</span>
      <div><strong>${escapeHtml(event.event_type.replaceAll("_", " "))}</strong><small>${escapeHtml(event.actor_id)}</small></div>
      <span class="event-decision">${escapeHtml(event.decision.replaceAll("_", " "))}</span>
      <code>${escapeHtml(event.record_hash.slice(0, 12))}…</code>
    </div>`).join("");
}

async function startFlow() {
  const button = byId("startButton");
  button.disabled = true;
  button.textContent = "Running governed agent…";
  try {
    const flow = await request("/api/flow/start", { method: "POST", body: "{}" });
    byId("correctionText").value = "";
    renderFlow(flow);
  } catch (error) {
    alert(error.message);
    button.disabled = false;
  } finally {
    button.textContent = "Start new governed draft";
    button.disabled = false;
  }
}

async function approveFlow() {
  if (!state.flow) return;
  try {
    const flow = await request(`/api/flow/${state.flow.flow_id}/correct`, {
      method: "POST",
      body: JSON.stringify({
        corrected_text: byId("correctionText").value,
        actor_id: byId("actorInput").value,
      }),
    });
    renderFlow(flow);
  } catch (error) {
    byId("humanMessage").textContent = error.message;
    byId("humanMessage").className = "inline-message message-bad";
  }
}

async function rerunFlow() {
  if (!state.flow) return;
  const button = byId("rerunButton");
  button.disabled = true;
  button.textContent = "Running generated eval…";
  try {
    const flow = await request(`/api/flow/${state.flow.flow_id}/rerun`, {
      method: "POST",
      body: "{}",
    });
    renderFlow(flow);
  } catch (error) {
    alert(error.message);
  } finally {
    button.textContent = "Compile eval + rerun agent";
    button.disabled = false;
  }
}

async function verifyFlow() {
  const result = await request(`/api/flow/${state.flow.flow_id}/verify`);
  byId("verificationResult").textContent = result.valid
    ? `PASS · ${result.record_count} signed records · head ${result.chain_head.slice(0, 16)}…`
    : `FAIL · ${result.errors.join(" · ")}`;
  byId("verificationResult").className = `inline-message ${result.valid ? "message-good" : "message-bad"}`;
}

async function tamperFlow() {
  const result = await request(`/api/flow/${state.flow.flow_id}/tamper-check`, {
    method: "POST",
    body: "{}",
  });
  const passed = result.before.valid && !result.after.valid;
  byId("verificationResult").textContent = passed
    ? "PASS · original chain verifies; edited copy is rejected"
    : "FAIL · tamper test did not produce the expected verification result";
  byId("verificationResult").className = `inline-message ${passed ? "message-good" : "message-bad"}`;
}

async function initialize() {
  try {
    const health = await request("/api/health");
    state.mode = health.agent_mode;
    byId("modeBadge").textContent = health.agent_mode === "live" ? "LIVE GPT‑5.6 MODE" : "FIXTURE MODE";
    byId("modeBadge").className = `badge ${health.agent_mode === "live" ? "badge-live" : "badge-neutral"}`;
  } catch {
    byId("modeBadge").textContent = "SERVER UNAVAILABLE";
  }
}

byId("startButton").addEventListener("click", startFlow);
byId("safeEditButton").addEventListener("click", () => {
  if (state.flow) byId("correctionText").value = suggestedCorrection(state.flow);
});
byId("approveButton").addEventListener("click", approveFlow);
byId("rerunButton").addEventListener("click", rerunFlow);
byId("verifyButton").addEventListener("click", verifyFlow);
byId("tamperButton").addEventListener("click", tamperFlow);
initialize();

