"use strict";
(() => {
  let operatorToken = "", selected = null, incidents = [], busy = false, sessionVersion = 0;
  const $ = (id) => document.getElementById(id);
  const terminal = new Set(["resolved", "contained", "denied", "escalated", "cancelled"]);
  const nice = (value) => String(value ?? "pending").replaceAll("_", " ");
  const json = (value) => JSON.stringify(value ?? {}, null, 2);
  const notice = (message) => { $("notice").textContent = message; $("notice").hidden = !message; };
  async function request(path, options = {}, token = operatorToken) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(path, {...options, signal: controller.signal,
        headers: {"Content-Type": "application/json", ...(token ? {Authorization: `Bearer ${token}`} : {})}});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`);
      return data;
    } finally { clearTimeout(timer); }
  }
  function element(tag, text, className) {
    const node = document.createElement(tag); node.textContent = text;
    if (className) node.className = className; return node;
  }
  function badge(status) { return element("span", nice(status), `status ${status}`); }
  function latest(record, field) {
    if (record[field] != null) return record[field];
    for (const event of [...(record.events || [])].reverse()) if (event.payload?.[field] != null) return event.payload[field];
    return null;
  }
  function renderQueue() {
    const list = $("incident-list"); list.replaceChildren();
    if (!incidents.length) list.append(element("p", "No incidents yet. Start a case above.", "muted"));
    for (const record of incidents) {
      const button = element("button", "", `incident-item${selected === record.incident_id ? " active" : ""}`);
      button.type = "button"; button.append(badge(record.status), element("strong", record.symptom), element("small", `${record.target_id} · ${record.environment}`));
      button.addEventListener("click", () => { selected = record.incident_id; refresh(); }); list.append(button);
    }
    $("count-active").textContent = incidents.filter(x => !terminal.has(x.status)).length;
    $("count-resolved").textContent = incidents.filter(x => x.status === "resolved").length;
    $("count-contained").textContent = incidents.filter(x => x.status === "contained").length;
    $("count-attention").textContent = incidents.filter(x => ["denied", "escalated"].includes(x.status)).length;
  }
  function render(record) {
    $("empty-state").hidden = true; $("incident-detail").hidden = false;
    $("incident-context").textContent = `${record.environment} / ${record.scope} / ${record.target_id}`;
    $("incident-title").textContent = record.symptom;
    $("incident-id").textContent = record.incident_id;
    $("incident-status").textContent = nice(record.status); $("incident-status").className = `status ${record.status}`;
    const phases = new Set((record.events || []).map(x => x.phase));
    const stage = terminal.has(record.status) ? 5 : record.status === "verifying" ? 4 : record.status === "executing" ? 3 : record.status.includes("approval") || phases.has("planned") ? 2 : record.status === "diagnosing" ? 1 : 0;
    $("lifecycle").replaceChildren(...["01 Observe", "02 Diagnose", "03 Authorize", "04 Execute", "05 Verify"].map((label, i) => element("span", label, i < stage ? "done" : i === stage ? "current" : "")));
    const evidence = latest(record, "evidence"), snapshot = evidence?.snapshot;
    const facts = $("observations"); facts.replaceChildren();
    if (snapshot) for (const [label, key] of [["State revision", "revision"], ["Source schema", "source_schema"], ["Accepted schema", "accepted_schema"], ["Rows pending", "backlog_rows"], ["Rows rejected", "rejected_rows"], ["Rows curated", "curated_rows"], ["Freshness lag (s)", "freshness_lag_seconds"], ["Batch state", "batch_status"]]) facts.append(element("dt", label), element("dd", nice(snapshot[key])));
    else facts.append(element("dt", "Waiting for a complete evidence snapshot"));
    $("source-logs").textContent = (evidence?.logs || []).join("\n");
    const diagnosis = latest(record, "diagnosis"), trace = latest(record, "model_trace") || latest(record, "trace");
    $("diagnostic-engine").textContent = trace?.mode || trace?.model || "DIAGNOSIS";
    const diagnosticFailure = [...(record.events || [])].reverse().find(x => x.phase === "diagnostic_failed" || x.phase === "escalated");
    $("diagnosis-summary").textContent = diagnosis?.summary || (terminal.has(record.status) ? "No valid diagnostic proposal was produced." : "Awaiting diagnostic evidence.");
    $("diagnosis-rationale").textContent = diagnosis?.rationale || diagnosticFailure?.payload?.reason || diagnosticFailure?.payload?.result?.reason || "";
    $("diagnosis-citations").textContent = diagnosis ? `Evidence: ${diagnosis.evidence_refs.join(", ")}` : "";
    $("model-trace").textContent = json(trace);
    const plan = latest(record, "plan"), policy = latest(record, "policy");
    $("plan-action").textContent = plan ? plan.actions.map(x => x.tool).join(", ") : "Awaiting plan";
    $("plan-revision").textContent = plan ? `Revision ${plan.expected_revision} · policy ${plan.policy_version}` : "";
    $("plan-hash").textContent = record.plan_hash || "No plan fingerprint yet";
    $("policy-reasons").textContent = (policy?.reasons || []).join("; ");
    $("approval-form").hidden = !["awaiting_approval", "approval_invalid", "approval_delivery_pending"].includes(record.status);
    $("cancel").hidden = terminal.has(record.status);
    const verification = latest(record, "verification"), result = latest(record, "result");
    $("verification-status").textContent = verification ? nice(verification.outcome).toUpperCase() : "PENDING";
    $("result-reason").textContent = result?.reason || (verification?.reasons || []).join("; ") || "A completed tool call is not a verified resolution.";
    $("verification-state").textContent = verification ? json(verification.snapshot) : "";
    const timeline = $("timeline"); timeline.replaceChildren();
    for (const event of record.events || []) {
      const li = document.createElement("li"), data = document.createElement("div"), detail = document.createElement("details");
      const time = new Date(event.created_at); li.append(element("time", Number.isNaN(time.valueOf()) ? event.created_at : time.toLocaleTimeString()));
      data.append(element("strong", nice(event.phase))); detail.append(element("summary", `Event ${event.sequence} · inspect payload`), element("pre", json(event.payload))); data.append(detail); li.append(data); timeline.append(li);
    }
    $("event-count").textContent = `${record.events?.length || 0} recorded events`;
  }
  async function refresh() {
    if (!operatorToken || busy) return; busy = true;
    const version = sessionVersion;
    try {
      const data = await request("/api/incidents"); if (version !== sessionVersion) return; incidents = Array.isArray(data) ? data : data.incidents;
      if (!selected && incidents.length) selected = incidents[0].incident_id;
      renderQueue(); if (selected) { const target = selected, detail = await request(`/api/incidents/${encodeURIComponent(target)}`); if (version !== sessionVersion || selected !== target) return; render(detail); }
      $("session-state").textContent = "Connected · refreshes every 4 seconds";
    } catch (error) { if (version === sessionVersion) notice(error.message); } finally { busy = false; }
  }
  $("connect").addEventListener("click", () => { sessionVersion += 1; operatorToken = $("operator-token").value.trim(); $("operator-token").value = ""; $("approver-token").value = ""; selected = null; incidents = []; $("incident-detail").hidden = true; $("empty-state").hidden = false; for (const id of ["observations", "timeline", "model-trace", "source-logs", "diagnosis-summary", "diagnosis-rationale", "diagnosis-citations", "incident-context", "incident-title", "incident-id", "plan-hash", "result-reason", "verification-state"]) $(id).replaceChildren(); renderQueue(); notice(""); refresh(); });
  $("refresh").addEventListener("click", refresh);
  $("incident-form").addEventListener("submit", async event => {
    event.preventDefault(); const button = event.submitter, version = sessionVersion; button.disabled = true; notice("");
    try { const result = await request("/api/demo/incidents", {method:"POST", body:json({scenario:$("scenario").value, mode:$("mode").value, simulate_lost_response:$("lost-response").checked})}); if (version !== sessionVersion) return; selected = result.incident_id; await refresh(); }
    catch (error) { notice(error.message); } finally { button.disabled = false; }
  });
  $("approval-form").addEventListener("submit", async event => {
    event.preventDefault(); const token = $("approver-token").value.trim(); $("approver-token").value = ""; event.submitter.disabled = true;
    try { await request(`/api/incidents/${encodeURIComponent(selected)}/approval`, {method:"POST",body:json({plan_hash:$("plan-hash").textContent, ttl_seconds:300})}, token); notice("Approval submitted. The worker will recheck live state before execution."); await refresh(); }
    catch (error) { notice(error.message); } finally { event.submitter.disabled = false; }
  });
  $("cancel").addEventListener("click", async () => { try { await request(`/api/incidents/${encodeURIComponent(selected)}/cancel`, {method:"POST",body:"{}"}); notice("Cancellation requested. Any effect already dispatched must still be reconciled."); await refresh(); } catch (error) { notice(error.message); } });
  async function health() { try { const state = await request("/health", {}, ""); $("service-status").textContent = state.status === "ok" ? "Workflow service available" : "Service degraded"; } catch { $("service-status").textContent = "Service unavailable"; } }
  health(); setInterval(refresh, 4000); setInterval(health, 30000);
})();
