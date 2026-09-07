const byId = (id) => document.getElementById(id);
const tabs = [...document.querySelectorAll('[role="tab"]')];
let currentScenario = null;

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

async function readApi(path) {
  const started = performance.now();
  let result;
  try {
    const response = await fetch(path, { signal: AbortSignal.timeout(5000), cache: "no-store" });
    result = { status: response.status, body: await response.json() };
  } catch {
    result = { status: "network error", body: { status: "unavailable", error: "Local service did not respond." } };
  }
  const event = document.createElement("li");
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = `GET ${path} · ${result.status} · ${Math.round(performance.now() - started)} ms`;
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
  currentScenario = null;
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

byId("load-fixture").addEventListener("click", async () => {
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
