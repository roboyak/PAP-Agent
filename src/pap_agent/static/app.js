const byId = (id) => document.getElementById(id);
const tabs = [...document.querySelectorAll('[role="tab"]')];
let currentScenario = "mysolark";

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
  let result;
  try {
    const response = await fetch(path, { signal: AbortSignal.timeout(15000), cache: "no-store",
      method: body ? "POST" : "GET", headers: body ? {"Content-Type": "application/json"} : {},
      body: body ? JSON.stringify(body) : undefined });
    result = { status: response.status, body: await response.json() };
  } catch {
    result = { status: "network error", body: { status: "unavailable", error: "Local service did not respond." } };
  }
  const event = document.createElement("li");
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = `${body ? "POST" : "GET"} ${path} · ${result.status} · ${Math.round(performance.now() - started)} ms`;
  const output = document.createElement("pre");
  output.textContent = JSON.stringify(result.body, null, 2);
  details.append(summary, output);
  event.append(details);
  byId("trace-events").append(event);
  if (byId("trace-events").children.length > 20) byId("trace-events").firstElementChild.remove();
  byId("empty-trace").hidden = true;
  return result;
}

byId("check-service").addEventListener("click", async () => {
  byId("check-service").disabled = byId("reset-view").disabled = true;
  appendMessage("You", "Check service", true);
  const [health, version] = await Promise.all([readApi("/health"), readApi("/api/v1/version")]);
  const healthy = health.status === 200 && health.body.status === "ok";
  byId("service-status").textContent = healthy ? "Service healthy" : "Service unavailable";
  byId("service-status").dataset.status = healthy ? "ok" : "error";
  byId("database-status").textContent = health.body.database ?? "unavailable";
  byId("pgvector-status").textContent = health.body.pgvector ?? "unavailable";
  byId("app-version").textContent = version.body.version ?? "unavailable";
  const note = healthy ? "PostgreSQL responded and pgvector is enabled." : "Check the local database. Health and Trace contain the result.";
  byId("health-note").textContent = note;
  appendMessage("Service", note);
  byId("check-service").disabled = byId("reset-view").disabled = false;
});

byId("reset-view").addEventListener("click", () => {
  currentScenario = "mysolark";
  byId("calculation-result").textContent = "No calculation yet.";
  byId("tool-calls").textContent = "No MCP tool calls have run.";
  byId("evidence-context").textContent = "No evidence loaded.";
  byId("evidence-note").textContent = "No telemetry loaded. Load a fixture to inspect stored evidence.";
  byId("messages").replaceChildren();
  byId("trace-events").replaceChildren();
  byId("empty-session").hidden = byId("empty-trace").hidden = false;
  byId("service-status").textContent = "Service not checked";
  delete byId("service-status").dataset.status;
  for (const id of ["database-status", "pgvector-status", "app-version"]) byId(id).textContent = "Not checked";
  byId("health-note").textContent = "Use Check service to refresh.";
});

byId("load-mysolark").addEventListener("click", async () => {
  currentScenario = "mysolark";
  byId("load-mysolark").disabled = true;
  const result = await readApi("/api/v1/evidence/current?scenario=mysolark");
  const evidence = result.body;
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

byId("load-fixture").addEventListener("click", async () => {
  currentScenario = "sunny";
  byId("load-fixture").disabled = true;
  const result = await readApi("/api/v1/scenarios/sunny");
  if (result.status === 200) {
    currentScenario = result.body.name;
    const { telemetry, policy, weather } = result.body;
    byId("evidence-context").textContent = JSON.stringify({ telemetry, policy, weather_intervals: weather.length }, null, 2);
    byId("evidence-note").textContent = `${result.body.label} loaded from PostgreSQL.`;
    appendMessage("Evidence", `${telemetry.battery_voltage_v} V battery · ${telemetry.solar_power_kw} kW solar · ${telemetry.load_power_kw} kW load. ${weather.length} hourly forecast inputs.`);
    selectTab(byId("tab-context"));
  } else {
    appendMessage("Service", "Fixture unavailable. Run make seed, then load it again.");
  }
  byId("load-fixture").disabled = false;
});

byId("calculate-pap").addEventListener("click", async () => {
  byId("calculate-pap").disabled = true;
  const response = await readApi("/api/v1/pap/calculate", { scenario: currentScenario });
  const result = response.body;
  if (response.status === 200) {
    byId("calculation-result").textContent = JSON.stringify(result, null, 2);
    const evidence = (await readApi(`/api/v1/evidence/${result.evidence_id}`)).body;
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
