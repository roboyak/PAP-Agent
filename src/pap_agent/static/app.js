const byId = (id) => document.getElementById(id);
const tabs = [...document.querySelectorAll('[role="tab"]')];
let currentScenario = document.body.dataset.defaultSource;
let currentPublication = null;
let busyTimer = null;
const actionButtons = [...document.querySelectorAll(".controls button, #evaluate-outcome")];

for (const id of ["model-context", "agent-comparison", "evidence-context", "calculation-result",
  "run-memory-results", "memory-results", "outcome-feedback", "tool-calls", "agent-activity", "graph-trace", "readiness-result"]) {
  const raw = byId(id), details = document.createElement("details"), label = document.createElement("summary");
  details.className = "raw-data";
  details.id = `details-${id}`;
  label.textContent = "Inspect raw details";
  raw.before(details);
  details.append(label, raw);
}

function beginAction(label) {
  const started = performance.now();
  actionButtons.forEach(button => { button.disabled = true; });
  byId("run-progress").hidden = false;
  const update = () => { byId("run-progress").textContent = `${label}… ${Math.floor((performance.now() - started) / 1000)} seconds elapsed. Waiting for the service result.`; };
  update();
  busyTimer = setInterval(update, 1000);
}

function endAction() {
  clearInterval(busyTimer);
  busyTimer = null;
  byId("run-progress").hidden = true;
  actionButtons.forEach(button => { button.disabled = false; });
  byId("evaluate-outcome").disabled = currentPublication?.status !== "valid";
}

function action(id, callback) {
  byId(id).addEventListener("click", async () => {
    if (busyTimer !== null) return;
    beginAction(byId(id).textContent);
    try { await callback(); }
    catch { appendMessage("Service", "The view could not be completed. Inspect the request in Trace."); }
    finally { endAction(); }
  });
}

function inspectList(id, rows, empty) {
  const root = byId(id);
  root.replaceChildren();
  for (const [title, detail] of rows.length ? rows : [[empty, ""]]) {
    const item = document.createElement("li"), heading = document.createElement("strong"), text = document.createElement("p");
    heading.textContent = title;
    text.textContent = detail;
    item.append(heading, text);
    root.append(item);
  }
}

function clearSelection(title = "No run selected. Run PAP to begin.") {
  currentPublication = null;
  history.replaceState(null, "", location.pathname);
  byId("published-profile").hidden = true;
  byId("view-output").hidden = true;
  byId("forecast-link").href = "/";
  byId("run-status").textContent = title;
  byId("run-meta").replaceChildren();
  byId("next-step").textContent = "Run PAP to create a result and inspect its complete workflow.";
  for (const id of ["model-context", "agent-activity", "run-memory-results", "evidence-context", "calculation-result", "tool-calls", "graph-trace", "search-trace", "outcome-feedback"]) {
    byId(id).textContent = "No record selected.";
  }
  for (const id of ["agent-summary", "run-memory-summary", "tool-summary", "node-summary"]) byId(id).replaceChildren();
  byId("evidence-summary").replaceChildren();
  byId("calculation-summary").textContent = "No calculation yet.";
  byId("model-summary").textContent = "No model calls recorded.";
  byId("model-messages").textContent = byId("model-calls").textContent = "0";
  byId("reasoning-mode").textContent = "Not run";
  byId("reasoning-summary").textContent = "No workflow selected.";
  byId("comparison-summary").textContent = byId("agent-comparison").textContent = "No comparison selected.";
}

function renderEvidence(evidence) {
  byId("evidence-context").textContent = JSON.stringify(evidence.scenario, null, 2);
  byId("evidence-note").textContent = evidence.scenario?.label ?? evidence.reason;
  const telemetry = evidence.scenario?.telemetry;
  byId("evidence-summary").textContent = telemetry
    ? `${telemetry.data_mode === "live" ? "Live scrape" : "Synthetic replay"}: ${telemetry.battery_voltage_v} V battery, ${telemetry.solar_power_kw} kW solar, ${telemetry.load_power_kw} kW load. Floor ${evidence.scenario.policy.min_battery_voltage_v} V. Source time ${telemetry.observed_at}. Weather is synthetic.`
    : evidence.reason;
  byId("tool-calls").textContent = JSON.stringify({available: evidence.tools, calls: evidence.calls}, null, 2);
  inspectList("tool-summary", (evidence.calls ?? []).map(call => [
    `${call.tool}: ${call.result?.status ?? "unavailable"} (${call.duration_ms} ms)`,
    `Read-only source call. ${call.result?.reason ?? ""}`,
  ]), "No MCP calls recorded.");
}

function renderCalculation(result) {
  byId("calculation-result").textContent = JSON.stringify(result, null, 2);
  const rows = result.pap?.intervals ?? [];
  byId("calculation-summary").textContent = rows.length
    ? `${rows[0].available_kw} kW additional in the first interval; ${rows.reduce((sum, row) => sum + row.energy_kwh, 0).toFixed(3)} kWh over 12 hours. Calculated in Python; zero battery discharge.`
    : (result.validation ?? ["No valid calculation."]).join(". ");
}

async function renderSelectedRun(episode, publication = null) {
  clearSelection("Loading completed run…");
  const link = document.createElement("a");
  link.href = `?episode=${encodeURIComponent(episode.episode_id)}`;
  link.textContent = `Run ${episode.episode_id}`;
  byId("run-meta").append(link);
  history.replaceState(null, "", link.href);
  let records, evidence, calculation;
  try {
    [records, publication, evidence, calculation] = await Promise.all([
      readRequired(`/api/v1/episodes/${episode.episode_id}/inspection`),
      publication ?? readRequired(`/api/v1/pap/${episode.publication_id}`),
      readRequired(`/api/v1/evidence/${episode.evidence_id}`),
      episode.calculation_id ? readRequired(`/api/v1/calculations/${episode.calculation_id}`) : null,
    ]);
  } catch (error) {
    byId("run-status").textContent = "Run details unavailable.";
    byId("model-summary").textContent = "Run records could not be loaded.";
    byId("next-step").textContent = "Inspect the failed request in Trace, then reload the run link above.";
    throw error;
  }
  currentScenario = episode.scenario;
  renderInspection(episode, records);
  renderPublication(publication);
  renderEvidence(evidence);
  if (calculation) renderCalculation(calculation);
  byId("graph-trace").textContent = JSON.stringify(episode, null, 2);
  inspectList("node-summary", (episode.trace ?? []).map(node => [node.node.replaceAll("_", " "), `${node.status}${node.duration_ms === undefined ? "" : ` · ${node.duration_ms} ms`}`]), "No completed nodes.");
  byId("run-status").textContent = `${publication.status === "valid" ? "Published evaluation" : "Withheld"}. ${publication.reason}`;
  byId("run-meta").append(document.createTextNode(` · ${publication.generated_at}`));
  byId("empty-session").hidden = true;
  byId("messages").replaceChildren();
  appendMessage("Selected run", `${publication.status}. ${publication.reason}. Saved evidence, memory, model records and workflow belong to the linked run. Health checks the current service.`);
  byId("next-step").textContent = publication.status === "valid"
    ? "Review the hourly result and Context assumptions. This service does not command equipment."
    : "Inspect Trace for the stopping decision and Subagent for the model outputs before running again.";
}

function renderPublication(publication) {
  if (!publication) return;
  currentPublication = publication;
  byId("evaluate-outcome").disabled = publication.status !== "valid";
  byId("evaluate-outcome").textContent = publication.evidence?.telemetry.data_mode === "synthetic"
    ? "Evaluate cloudy demo" : "Evaluate latest reading";
  if (publication.feedback) byId("outcome-feedback").textContent = JSON.stringify(publication.feedback, null, 2);
  byId("published-profile").hidden = false;
  byId("view-output").hidden = false;
  byId("view-output").href = byId("forecast-link").href = `/?episode=${encodeURIComponent(publication.episode_id)}`;
  byId("publication-status").textContent = publication.status;
  const intervals = publication.profile?.intervals ?? [];
  const energy = intervals.reduce((sum, row) => sum + row.energy_kwh, 0);
  byId("profile-summary").textContent = publication.status === "valid"
    ? `${intervals[0].available_kw} kW additional · ${energy.toFixed(3)} kWh over 12 hours · ${publication.profile.confidence} confidence`
    : `Additional power withheld: ${publication.reason}`;
  const evidence = publication.evidence;
  const live = evidence?.telemetry.data_mode === "live";
  const age = live ? Math.round((Date.now() - Date.parse(evidence.telemetry.observed_at)) / 1000) : null;
  byId("profile-provenance").textContent = evidence
    ? `${evidence.telemetry.source} · ${evidence.telemetry.observed_at} · ${live ? `${age} seconds old${age > 300 ? " (stale; run again)" : ""}` : "synthetic replay clock"} · battery ${evidence.telemetry.battery_voltage_v} V · floor ${evidence.policy.min_battery_voltage_v} V. Published ${publication.generated_at}.`
    : publication.reason;
  byId("profile-explanation").textContent = [publication.profile?.explanation ?? "No validated profile is available.",
    publication.interpretation?.advice?.explanation ?? "", publication.search?.guidance?.summary ?? ""].join(" ");
  byId("profile-intervals").replaceChildren();
  for (const interval of intervals) {
    const row = document.createElement("tr");
    for (const value of [interval.starts_at.replace("T", " ").slice(0, 16), interval.available_kw, interval.energy_kwh]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    byId("profile-intervals").append(row);
  }
}

function selectTab(selected) {
  for (const tab of tabs) {
    const active = tab === selected;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    byId(tab.getAttribute("aria-controls")).hidden = !active;
  }
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (event) => {
    const next = { ArrowRight: (index + 1) % tabs.length, ArrowLeft: (index - 1 + tabs.length) % tabs.length,
      Home: 0, End: tabs.length - 1 }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    selectTab(tabs[next]);
    tabs[next].focus();
  });
});

function appendMessage(label, text, request = false) {
  byId("empty-session").hidden = true;
  const message = document.createElement("div");
  message.className = request ? "message request" : "message";
  const heading = document.createElement("strong");
  heading.textContent = label;
  message.append(heading, document.createTextNode(text));
  byId("messages").append(message);
  if (byId("messages").children.length > 20) byId("messages").firstElementChild.remove();
  message.scrollIntoView({ block: "nearest" });
}

async function readApi(path, body) {
  const started = performance.now();
  const event = document.createElement("li"), details = document.createElement("details");
  const summary = document.createElement("summary"), output = document.createElement("pre");
  summary.textContent = `${body ? "POST" : "GET"} ${path} · pending`;
  output.textContent = "Request in progress.";
  details.append(summary, output);
  event.append(details);
  byId("trace-events").append(event);
  if (byId("trace-events").children.length > 20) byId("trace-events").firstElementChild.remove();
  byId("empty-trace").hidden = true;
  let result;
  try {
    const response = await fetch(path, { signal: AbortSignal.timeout(600000), cache: "no-store",
      method: body ? "POST" : "GET", headers: body ? {"Content-Type": "application/json"} : {},
      body: body ? JSON.stringify(body) : undefined });
    result = { status: response.status, body: await response.json() };
  } catch {
    result = { status: "network error", body: { status: "unavailable", error: "Local service did not respond." } };
  }
  summary.textContent = `${body ? "POST" : "GET"} ${path} · ${result.status} · ${Math.round(performance.now() - started)} ms`;
  output.textContent = JSON.stringify(result.body, null, 2);
  return result;
}

async function readRequired(path) {
  const response = await readApi(path);
  if (response.status !== 200) throw new Error("Run record unavailable");
  return response.body;
}

action("check-service", async () => {
  byId("check-service").disabled = byId("reset-view").disabled = true;
  appendMessage("You", "Check service", true);
  const [health, version, readiness] = await Promise.all([readApi("/health"), readApi("/api/v1/version"), readApi("/health/ready")]);
  const healthy = health.status === 200 && readiness.status === 200;
  byId("readiness-result").textContent = JSON.stringify(readiness.body, null, 2);
  const missing = Object.entries(readiness.body.checks ?? {}).filter(([,value]) => !value).map(([name]) => name.replaceAll("_", " "));
  byId("readiness-summary").textContent = `${readiness.body.model_backend ?? "Unknown provider"}: ${readiness.body.agent_model ?? "unknown model"}. ${readiness.body.model_check ?? ""} ${missing.length ? `Needs attention: ${missing.join(", ")}.` : readiness.status === 200 ? "Dependency checks passed." : "Readiness unavailable; inspect Trace."}`;
  byId("service-status").textContent = healthy ? "Service healthy" : "Service unavailable";
  byId("service-status").dataset.status = healthy ? "ok" : "error";
  byId("database-status").textContent = health.body.database ?? "unavailable";
  byId("pgvector-status").textContent = health.body.pgvector ?? "unavailable";
  byId("app-version").textContent = version.body.version ?? "unavailable";
  const note = healthy ? "Configured dependencies passed their checks. See Health for model-check scope." : "Health and Trace show which dependency needs attention.";
  byId("health-note").textContent = note;
  appendMessage("Service", note);
  byId("check-service").disabled = byId("reset-view").disabled = false;
});

action("reset-view", () => {
  clearSelection();
  currentScenario = document.body.dataset.defaultSource;
  currentPublication = null;
  byId("outcome-feedback").textContent = "No outcome evaluated yet.";
  byId("agent-activity").textContent = "No subagent has run.";
  byId("model-context").textContent = "No model context yet.";
  byId("memory-results").textContent = "No retrieval yet.";
  byId("memory-search-summary").textContent = "Search stored guidance or index newly evaluated outcomes.";
  byId("agent-comparison").textContent = "No comparison yet.";
  byId("model-messages").textContent = byId("model-calls").textContent = "0";
  byId("reasoning-mode").textContent = "Not run";
  byId("search-trace").textContent = "No selective search.";
  byId("published-profile").hidden = true;
  byId("calculation-result").textContent = "No calculation yet.";
  byId("graph-trace").textContent = "No workflow run yet.";
  byId("tool-calls").textContent = "No MCP tool calls have run.";
  byId("evidence-context").textContent = "No evidence loaded.";
  byId("evidence-note").textContent = "Run PAP or select a source to inspect its evidence.";
  byId("readiness-result").textContent = "Not checked.";
  byId("readiness-summary").textContent = "Current service configuration has not been checked.";
  byId("messages").replaceChildren();
  byId("trace-events").replaceChildren();
  byId("empty-session").hidden = byId("empty-trace").hidden = false;
  byId("service-status").textContent = "Service not checked";
  delete byId("service-status").dataset.status;
  for (const id of ["database-status", "pgvector-status", "app-version"]) byId(id).textContent = "Not checked";
  byId("health-note").textContent = "Use Check service to refresh.";
});

action("load-mysolark", async () => {
  clearSelection("MySolArk source preview. No workflow selected.");
  currentScenario = "mysolark";
  byId("load-mysolark").disabled = true;
  const result = await readApi("/api/v1/evidence/current?scenario=mysolark");
  const evidence = result.body;
  renderEvidence(evidence);
  if (evidence.status === "valid") {
    currentScenario = "mysolark";
    byId("evidence-context").textContent = JSON.stringify(evidence.scenario, null, 2);
    byId("evidence-note").textContent = evidence.scenario.label;
    byId("tool-calls").textContent = JSON.stringify({ available: evidence.tools, calls: evidence.calls }, null, 2);
    const telemetry = evidence.scenario.telemetry;
    appendMessage("MCP evidence", `${telemetry.battery_voltage_v} V battery · ${telemetry.solar_power_kw} kW solar · ${telemetry.load_power_kw} kW load. Scraped ${evidence.observed_age_seconds} seconds ago at ${telemetry.observed_at}; weather is synthetic.`);
    selectTab(byId("tab-tools"));
  } else appendMessage("Evidence withheld", evidence.reason ?? "Source unavailable.");
  byId("load-mysolark").disabled = false;
});

action("load-fixture", async () => {
  clearSelection("Sunny synthetic source preview. No workflow selected.");
  currentScenario = "sunny";
  byId("load-fixture").disabled = true;
  const result = await readApi("/api/v1/scenarios/sunny");
  if (result.status === 200) {
    currentScenario = result.body.name;
    const { telemetry, policy, weather } = result.body;
    renderEvidence({scenario: result.body, tools: [], calls: []});
    byId("evidence-context").textContent = JSON.stringify({ telemetry, policy, weather_intervals: weather.length }, null, 2);
    byId("evidence-note").textContent = `${result.body.label} loaded from PostgreSQL.`;
    appendMessage("Evidence", `${telemetry.battery_voltage_v} V battery · ${telemetry.solar_power_kw} kW solar · ${telemetry.load_power_kw} kW load. ${weather.length} hourly forecast inputs.`);
    selectTab(byId("tab-context"));
  } else {
    appendMessage("Service", "Fixture unavailable. Run make seed, then load it again.");
  }
  byId("load-fixture").disabled = false;
});

action("calculate-pap", async () => {
  clearSelection("Calculation preview. No published workflow selected.");
  byId("calculate-pap").disabled = true;
  const response = await readApi("/api/v1/pap/calculate", { scenario: currentScenario });
  const result = response.body;
  if (response.status === 200) {
    renderCalculation(result);
    const evidence = (await readApi(`/api/v1/evidence/${result.evidence_id}`)).body;
    renderEvidence(evidence);
    byId("evidence-context").textContent = JSON.stringify(evidence.scenario, null, 2);
    byId("tool-calls").textContent = JSON.stringify({ available: evidence.tools, calls: evidence.calls }, null, 2);
    byId("evidence-note").textContent = evidence.scenario?.label ?? evidence.reason;
    if (result.status === "valid") {
      const total = result.pap.intervals.reduce((sum, item) => sum + item.energy_kwh, 0);
      appendMessage("PAP calculation", `${result.pap.intervals[0].available_kw} kW additional now · ${total.toFixed(3).replace(/0+$/, "").replace(/\.$/, "")} kWh across 12 hours. Solar surplus only; battery discharge budget 0 kWh. Floor ${evidence.scenario.policy.min_battery_voltage_v} V. Evaluation baseline with synthetic weather.`);
    } else appendMessage("PAP withheld", result.validation.join(". "));
    selectTab(byId("tab-context"));
  } else appendMessage("Service", "Calculation unavailable; inspect Trace.");
  byId("calculate-pap").disabled = false;
});

action("run-workflow", async () => {
  clearSelection("Running a new workflow…");
  byId("run-workflow").disabled = true;
  const response = await readApi("/api/v1/pap/run", { scenario: currentScenario });
  if (response.status === 200) {
    const episode = response.body;
    await renderSelectedRun(episode);
    appendMessage("Workflow", `${episode.status} · ${episode.stop_reason}. Episode ${episode.episode_id}`);
    selectTab(byId("tab-trace"));
  } else appendMessage("Workflow", "Run unavailable; inspect Trace.");
  byId("run-workflow").disabled = false;
});

function renderInspection(episode, records) {
  byId("reasoning-mode").textContent = episode.reasoning_mode ?? "linear";
  byId("search-trace").textContent = JSON.stringify(records.filter(record => record.kind === "search"), null, 2);
  const agents = records.filter(record => record.calls !== undefined);
  byId("model-calls").textContent = episode.model_calls ?? 0;
  byId("model-messages").textContent = agents.reduce((sum, record) => sum + 2 * record.calls, 0);
  byId("model-context").textContent = JSON.stringify(agents.map(({kind, system, input}) => ({role: kind, system, input})), null, 2);
  byId("agent-activity").textContent = JSON.stringify(agents, null, 2);
  const models = [...new Set(agents.map(record => `${record.provider ?? "provider not recorded"} / ${record.model}`))];
  byId("model-summary").textContent = models.length ? `Recorded model: ${models.join(", ")}. Two input messages per reserved attempt; no model tools.` : "No model calls recorded for this run.";
  inspectList("agent-summary", agents.map(record => [
    `${record.kind}: ${record.status} (${record.duration_ms} ms)`,
    `${record.provider ?? "Provider not recorded"} / ${record.model}. ${record.calls} attempt; ${record.usage?.total_tokens ?? "unknown"} tokens. ${record.output?.explanation ?? (record.output?.thoughts ? `${record.output.thoughts.length} candidate interpretations returned.` : record.output?.scores ? `${record.output.scores.length} candidate scores returned.` : record.reason)}`,
  ]), "No model calls recorded for this run.");
  const retrieval = records.filter(record => record.kind === "retrieval");
  byId("run-memory-results").textContent = JSON.stringify(retrieval, null, 2);
  inspectList("run-memory-summary", retrieval.flatMap(record => (record.candidates ?? []).map(item => [
    `${item.source_id}: ${item.selection_reason}`, `Similarity ${item.score.toFixed(3)} (not probability). ${item.content}`,
  ])), retrieval.length ? `Retrieval ${retrieval[0].status}; no eligible records.` : "This run did not retrieve memory.");
  const assessment = records.find(record => record.kind === "assessment");
  const search = records.find(record => record.kind === "search");
  byId("reasoning-summary").textContent = [assessment?.reason, search ? `Search stopped: ${search.stop_reason}.` : "", search?.guidance?.summary].filter(Boolean).join(" ") || "The workflow stopped before reasoning was needed.";
}

action("compare-agents", async () => {
  byId("compare-agents").disabled = byId("run-workflow").disabled = true;
  appendMessage("Comparison", "Running the same evidence with interpretation off, then on.");
  const response = await readApi("/api/v1/pap/compare", {scenario: currentScenario});
  if (response.status === 200) {
    const episode = response.body.runs[1].episode;
    await renderSelectedRun(episode);
    byId("agent-comparison").textContent = JSON.stringify(response.body, null, 2);
    byId("comparison-summary").textContent = `${response.body.provider} / ${response.body.model}. ${response.body.runs.map(run => `Interpretation ${run.interpretation_enabled ? "on" : "off"}: ${run.model_calls} calls, ${(run.elapsed_ms / 1000).toFixed(1)} seconds, ${run.episode.status}`).join(". ")}. Same calculated power: ${response.body.same_available_power}. Selected run is interpretation on.`;
    appendMessage("Comparison", `Same available power: ${response.body.same_available_power}. ${response.body.runs.map(run => `${run.interpretation_enabled ? "On" : "Off"}: ${run.model_calls} calls, ${run.elapsed_ms} ms`).join(" · ")}`);
    selectTab(byId("tab-context"));
  } else appendMessage("Comparison", "Unavailable; inspect Trace.");
  byId("compare-agents").disabled = byId("run-workflow").disabled = false;
});

async function restoreRun() {
  beginAction("Loading saved run");
  try {
    const selected = new URLSearchParams(location.search).get("episode");
    if (selected) {
      const response = await readApi(`/api/v1/episodes/${encodeURIComponent(selected)}`);
      if (response.status === 200) await renderSelectedRun(response.body);
      else clearSelection("Saved run was not found. Run PAP to begin.");
    } else {
      const response = await readApi("/api/v1/pap/latest");
      if (response.status === 200 && response.body) {
        const episode = await readApi(`/api/v1/episodes/${response.body.episode_id}`);
        if (episode.status === 200) await renderSelectedRun(episode.body, response.body);
      }
    }
  } catch { appendMessage("Service", "The saved run could not be loaded. Inspect Trace or start a new run."); }
  finally { endAction(); }
}
restoreRun();

action("evaluate-outcome", async () => {
  if (!currentPublication) return;
  byId("evaluate-outcome").disabled = true;
  const response = await readApi(`/api/v1/pap/${currentPublication.id}/evaluate`, {});
  byId("outcome-feedback").textContent = JSON.stringify(response.body, null, 2);
  appendMessage("Outcome evaluation", response.status === 200
    ? `${response.body.calibration.guidance}. Point power comparison; ${response.body.calibration.samples} samples. Future confidence only.`
    : response.body.detail ?? "Evaluation unavailable.");
  selectTab(byId("tab-memory"));
  byId("evaluate-outcome").disabled = false;
});

action("index-memory", async () => {
  byId("index-memory").disabled = true;
  const result = await readApi("/api/v1/memory/index", {});
  byId("memory-results").textContent = JSON.stringify(result.body, null, 2);
  byId("memory-search-summary").textContent = result.status === 200
    ? `${result.body.indexed} new records indexed. The selected run's memory is unchanged.`
    : "Memory indexing unavailable; inspect Trace.";
  byId("index-memory").disabled = false;
});
action("search-memory", async () => {
  byId("search-memory").disabled = true;
  const source = currentScenario === "sunny" ? "synthetic" : "live";
  const result = await readApi(`/api/v1/memory/search?source_kind=${source}&query=${encodeURIComponent(byId("memory-query").value)}`);
  byId("memory-results").textContent = JSON.stringify(result.body, null, 2);
  byId("memory-search-summary").textContent = result.status === 200
    ? `${result.body.candidates.length} manual search results. Similarity ranks relevance; it is not a probability.`
    : "Memory search unavailable; inspect Trace.";
  byId("search-memory").disabled = false;
});
