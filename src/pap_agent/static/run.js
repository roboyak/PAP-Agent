const byId = id => document.getElementById(id);
const source = byId("source"), runButton = byId("run-workflow");
let selectedPublication = null;
let simulation = null, polling = false;
let outputView = "forecast";
let chartDay = "follow";
let stepMinutes = sessionStorage.getItem("pap-replay-step") === "15" ? 15 : 60, busy = false;
const replayStart = Date.parse("2026-08-30T00:00:00-07:00"), replayEnd = Date.parse("2026-09-06T00:00:00-07:00");
source.value = document.body.dataset.defaultSource;
byId("playback-speed").value = sessionStorage.getItem("pap-playback-delay") ?? "1";
const number = value => Number(value).toFixed(3).replace(/\.?0+$/, "");

// This fixed week is entirely PDT; stored/API timestamps remain UTC.
const replayTime = () => Date.parse(byId("replay-day").value + "T" + byId("replay-time").value + "-07:00");
const inputTime = ms => new Date(ms - 7 * 3600000).toISOString().slice(0, 16);
const setReplayTime = ms => {
  const [day, time] = inputTime(ms).split("T");
  byId("replay-day").value = day;
  byId("replay-time").value = time;
};
const pacific = value => new Date(value).toLocaleString("en-US", {timeZone:"America/Los_Angeles", month:"short", day:"numeric", hour:"numeric", minute:"2-digit"});
const forecastTime = value => pacific(value) + " Pacific";
const playbackEnd = () => Date.parse(byId("replay-end-day").value + "T00:00:00-07:00") + 86400000;
const activeSimulation = () => ["running", "pausing"].includes(simulation?.status);
const simulationQuery = () => simulation ? `simulation=${encodeURIComponent(simulation.id)}` : "";
function selection() {
  return {scenario:source.value, wing:byId("wing").value,
    replay_at:source.value === "mysolark" && byId("time-window").value === "week"
      ? new Date(replayTime()).toISOString() : null};
}
function syncControls() {
  const real = source.value === "mysolark", replay = real && byId("time-window").value === "week";
  const locked = busy || activeSimulation();
  document.querySelectorAll(".run-controls button, .run-controls select, .run-controls input").forEach(control => { control.disabled = locked; });
  byId("wing-control").hidden = byId("window-control").hidden = !real;
  byId("replay-controls").hidden = !replay;
  byId("replay-time").step = stepMinutes * 60;
  byId("replay-time").max = stepMinutes === 15 ? "23:45" : "23:00";
  if (byId("replay-end-day").value < byId("replay-day").value) byId("replay-end-day").value = byId("replay-day").value;
  for (const option of byId("replay-end-day").options) option.disabled = option.value < byId("replay-day").value;
  byId("step-hour").setAttribute("aria-pressed", String(stepMinutes === 60));
  byId("step-quarter").setAttribute("aria-pressed", String(stepMinutes === 15));
  byId("previous-time").disabled = locked || replayTime() <= replayStart;
  byId("next-time").disabled = locked || replayTime() >= replayEnd - stepMinutes * 60000;
  byId("start-simulation").hidden = !replay;
  byId("start-simulation").textContent = simulation ? "Start new" : "Start simulation";
  runButton.textContent = replay ? "Run once" : "Run PAP";
  runButton.classList.toggle("primary", !replay);
  byId("simulator").hidden = !replay;
  byId("pause-simulation").hidden = !activeSimulation();
  byId("pause-simulation").disabled = busy || simulation?.status === "pausing";
  byId("resume-simulation").hidden = !["paused", "failed"].includes(simulation?.status);
  byId("resume-simulation").disabled = busy;
  byId("simulation-history").disabled = !simulation?.completed_steps;
  byId("playback-speed").disabled = busy;
  byId("selection-note").textContent = replay
    ? `DW ${byId("wing").value} · Real MySolArk recordings, Aug 30–Sep 6 · ${stepMinutes}-minute steps · All display times are Pacific.`
    : real ? `DW ${byId("wing").value} · Reads the latest persisted scrape. Stale data is withheld.` : "Synthetic sunny fixture; not measured telemetry.";
  if (!simulation && replay) {
    byId("simulation-status").textContent = "Ready";
    byId("simulation-time").textContent = pacific(replayTime());
    byId("simulation-count").textContent = "0 steps";
    byId("simulation-summary").textContent = "Read data → forecast → advance clock";
    byId("simulation-explanation").textContent = `Plays until ${pacific(playbackEnd())}. Start at 12:00 AM to watch the whole day.`;
    byId("simulation-progress").value = 0;
  }
}
function restoreSelection(episode) {
  source.value = episode.scenario;
  const selected = episode.selection ?? {};
  byId("wing").value = selected.wing ?? "1.24";
  byId("time-window").value = selected.replay_at ? "week" : "live";
  if (selected.replay_at) {
    setReplayTime(Date.parse(selected.replay_at));
    if (new Date(selected.replay_at).getUTCMinutes() % 60) stepMinutes = 15;
  }
  syncControls();
}

async function request(path, body) {
  const response = await fetch(path, {
    cache: "no-store", signal: AbortSignal.timeout(600000),
    method: body ? "POST" : "GET",
    headers: body ? {"Content-Type": "application/json"} : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error("Request failed");
  return response.json();
}

function sourceAge() {
  const telemetry = selectedPublication?.evidence?.telemetry;
  if (!telemetry) return;
  if (selectedPublication.selection?.replay_at) {
    byId("source-age").textContent = `Historical scrape · ${selectedPublication.observed_age_seconds} sec old at replay time.`;
    return;
  }
  const age = Math.max(0, Math.round((Date.now() - Date.parse(telemetry.observed_at)) / 1000));
  byId("source-age").textContent = telemetry.data_mode === "live"
    ? `Scrape: ${age < 60 ? `${age} sec` : `${Math.floor(age / 60)} min`} old.${age > 300 ? " Stale; run again." : ""}`
    : "Synthetic replay clock; not a live measurement.";
}

function chart(intervals) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 940 200");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Twelve hourly additional-power values in kilowatts. Exact values are in the hourly numbers table.");
  const add = (tag, attrs, text) => {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([name, value]) => el.setAttribute(name, value));
    if (text !== undefined) el.textContent = text;
    svg.append(el);
    return el;
  };
  const maximum = Math.max(...intervals.map(row => row.available_kw), 0.1);
  for (let step = 0; step <= 4; step++) {
    const y = 156 - step * 30;
    add("line", {x1:50, x2:916, y1:y, y2:y, stroke:"#b3ab8b", "stroke-width":1});
    add("text", {x:38, y:y+4, "text-anchor":"end", class:"axis-label"}, number(maximum * step / 4));
  }
  intervals.forEach((row, i) => {
    const x = 66 + i * 71, height = row.available_kw / maximum * 120, y = 156 - height;
    if (height > 0) {
      add("rect", {x, y, width:40, height, fill:"#7f9b85", stroke:"#403e2e"});
      add("polygon", {points:`${x},${y} ${x+7},${y-5} ${x+47},${y-5} ${x+40},${y}`, fill:"#b7c8a3", stroke:"#403e2e"});
      add("polygon", {points:`${x+40},${y} ${x+47},${y-5} ${x+47},151 ${x+40},156`, fill:"#657e6b", stroke:"#403e2e"});
    } else add("line", {x1:x,x2:x+40,y1:156,y2:156,stroke:"#403e2e","stroke-width":3});
    add("text", {x:x+20, y:y-13, "text-anchor":"middle", class:"bar-label"}, number(row.available_kw));
    const hour = new Date(row.starts_at).toLocaleTimeString("en-US", {timeZone:"America/Los_Angeles", hour:"numeric", minute:"2-digit"});
    add("text", {x:x+20, y:184, "text-anchor":"middle", class:"axis-label"}, hour);
  });
  byId("forecast-chart").replaceChildren(svg);
}

const usableReading = row => row.solar_kw != null && row.load_kw != null && row.observed_at
  && (row.observed_age_seconds == null || row.observed_age_seconds >= 0 && row.observed_age_seconds <= 300);

function recordedChart() {
  const publication = selectedPublication, telemetry = publication.evidence?.telemetry;
  const at = publication.selection?.replay_at ?? telemetry?.observed_at ?? publication.generated_at;
  const localDay = value => new Date(value).toLocaleDateString("en-CA", {timeZone:"America/Los_Angeles"});
  const day = localDay(at);
  const rows = (simulation?.results ?? [{replay_at:at, observed_at:telemetry?.observed_at,
    solar_kw:telemetry?.solar_power_kw, load_kw:telemetry?.load_power_kw,
    observed_age_seconds:publication.observed_age_seconds}])
    .filter(row => localDay(row.replay_at) === day);
  const readable = row => usableReading(row) && localDay(row.observed_at) === day;
  const points = rows.filter(readable), maximum = Math.ceil(Math.max(1, ...points.flatMap(row => [row.solar_kw, row.load_kw])));
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 940 220");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Recorded solar generation, site usage and solar left over across one Pacific day. Gaps mean missing readings. Future hours are blank.");
  const add = (tag, attrs, text) => {
    const element = document.createElementNS(svg.namespaceURI, tag);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    svg.append(element);
    return element;
  };
  const x = time => {
    const parts = new Intl.DateTimeFormat("en-US", {timeZone:"America/Los_Angeles", hourCycle:"h23", hour:"2-digit", minute:"2-digit", second:"2-digit"}).formatToParts(new Date(time));
    const part = type => Number(parts.find(item => item.type === type).value);
    return 52 + (part("hour") + part("minute")/60 + part("second")/3600) / 24 * 850;
  };
  const y = value => 173 - value / maximum * 142;
  for (let tick = 0; tick <= 4; tick++) {
    add("line", {x1:52, x2:902, y1:y(maximum*tick/4), y2:y(maximum*tick/4), stroke:"#b3ab8b"});
    add("text", {x:42, y:y(maximum*tick/4)+4, "text-anchor":"end", class:"axis-label"}, number(maximum*tick/4));
  }
  ["12 AM", "6 AM", "12 PM", "6 PM", "12 AM"].forEach((label, i) => {
    add("text", {x:52+i*212.5, y:207, "text-anchor":"middle", class:"axis-label"}, label);
  });
  // Only canonical readings already processed by playback; never invent night values or fill gaps.
  for (const [key, color, dash] of [["surplus_kw", "#38694d", "3 5"], ["load_kw", "#45473f", "9 5"], ["solar_kw", "#946617", ""]]) {
    let path = "", connected = false;
    for (const row of rows) {
      if (!readable(row)) { connected = false; continue; }
      const value = key === "surplus_kw" ? Math.max(0, row.solar_kw - row.load_kw) : row[key];
      path += `${connected ? "L" : "M"}${x(row.observed_at)},${y(value)} `;
      connected = true;
      const dot = add("circle", {cx:x(row.observed_at), cy:y(value), r:2.5, fill:color, "data-series":key});
      const title = document.createElementNS(svg.namespaceURI, "title");
      title.textContent = `${forecastTime(row.observed_at)}: ${number(value)} kW`;
      dot.append(title);
    }
    add("path", {d:path, fill:"none", stroke:color, "stroke-width":3, "stroke-dasharray":dash, "data-series":key});
  }
  const playX = x(at);
  add("line", {x1:playX, x2:playX, y1:22, y2:180, stroke:"#77745c", "stroke-dasharray":"2 4"});
  if (!points.length) add("text", {x:475, y:93, "text-anchor":"middle", class:"axis-label"}, "No usable readings yet for this day");
  byId("recorded-chart").replaceChildren(svg);
  byId("recorded-day-heading").textContent = new Date(at).toLocaleDateString("en-US", {timeZone:"America/Los_Angeles", month:"short", day:"numeric"}) + " / recorded day";
  byId("recorded-period").textContent = `${points.length} recorded step readings · Pacific time · Playback through ${pacific(at)}`;
}

function showOutputView() {
  if (!selectedPublication) return;
  const recorded = outputView === "recorded", publication = selectedPublication;
  byId("chart-day").disabled = !simulation?.results.length;
  if (!simulation) {
    byId("chart-day").replaceChildren(new Option("Selected reading", "follow"));
    delete byId("chart-day").dataset.days;
  }
  byId("view-recorded").setAttribute("aria-pressed", String(recorded));
  byId("view-forecast").setAttribute("aria-pressed", String(!recorded));
  byId("recorded-output").hidden = !recorded;
  byId("valid-output").hidden = recorded || publication.status !== "valid";
  byId("output-heading").textContent = recorded ? "The recorded power story" : "Power forecast";
  byId("power-definition").hidden = !recorded;
  const telemetry = publication.evidence?.telemetry;
  const usable = telemetry && usableReading({solar_kw:telemetry.solar_power_kw, load_kw:telemetry.load_power_kw,
    observed_at:telemetry.observed_at, observed_age_seconds:publication.observed_age_seconds});
  if (recorded) {
    byId("guidance-heading").textContent = "What’s happening";
    for (const [id, value] of [["solar-current", telemetry?.solar_power_kw], ["load-current", telemetry?.load_power_kw],
      ["surplus-current", usable ? Math.max(0, telemetry.solar_power_kw - telemetry.load_power_kw) : null]]) {
      byId(id).textContent = usable ? `${Number(value).toFixed(1)} kW` : "—";
    }
    byId("agent-guidance").textContent = !usable
      ? "No usable reading at this step. A gap does not mean the solar panels produced zero."
      : telemetry.solar_power_kw <= 0.001
        ? "No solar was recorded at this moment. The site was still using power."
        : telemetry.solar_power_kw <= telemetry.load_power_kw
          ? "Solar is being generated, but the site is using all of it. There is no solar left over."
          : `Solar covers the site’s use, leaving ${(telemetry.solar_power_kw - telemetry.load_power_kw).toFixed(1)} kW before battery charging or other limits.`;
    recordedChart();
  } else {
    byId("guidance-heading").textContent = publication.status === "valid" ? "What the agent says" : "Why the result was withheld";
    byId("agent-guidance").textContent = byId("agent-guidance").dataset.forecast;
  }
}
for (const view of ["recorded", "forecast"]) byId(`view-${view}`).addEventListener("click", () => {
  outputView = view;
  showOutputView();
});

function render(publication) {
  selectedPublication = publication;
  const valid = publication.status === "valid", profile = publication.profile;
  const evidence = publication.evidence, telemetry = evidence?.telemetry;
  const weather = [...new Set((evidence?.weather ?? []).map(row => row.source))].join(" + ");
  byId("forecast-limit").textContent = weather
    ? `${weather}. No morning boost; cannot predict sunrise from zero.`
    : "Weather unavailable; inspect this run for the reason.";
  const query = `?episode=${encodeURIComponent(publication.episode_id)}${simulation ? "&" + simulationQuery() : ""}`;
  history.replaceState(null, "", "/" + query);
  byId("inspector-link").href = byId("view-inspector").href = "/inspector" + query;
  byId("empty-result").hidden = true;
  byId("published-profile").hidden = false;
  byId("valid-output").hidden = !valid;
  const replay = publication.selection?.replay_at;
  byId("publication-status").textContent = valid ? replay ? "Historical replay" : "Published evaluation" : "Withheld";
  byId("publication-status").dataset.status = valid ? "valid" : "withheld";
  byId("run-status").textContent = `${replay ? `Shown: ${forecastTime(replay)}. ` : `Saved ${forecastTime(publication.generated_at)}. `}${valid ? "Read-only evaluation; no equipment commands." : publication.reason}`;
  byId("run-meta").textContent = `Run ${publication.episode_id}`;
  byId("guidance-heading").textContent = valid ? "What the agent says" : "Why the result was withheld";
  const advice = [publication.search?.guidance?.summary, publication.interpretation?.advice?.explanation].filter(Boolean);
  if (publication.interpretation && !publication.interpretation.accepted) advice.push("Optional model advice was unavailable or rejected. Inspect Subagent for the recorded attempt.");
  byId("agent-guidance").textContent = valid
    ? advice.join(" ") || "PAP subtracts the existing load from solar generation, checks the battery voltage floor, and estimates the extra power. This step did not need model advice."
    : [publication.reason, ...advice].join(" ");
  byId("agent-guidance").dataset.forecast = byId("agent-guidance").textContent;
  byId("profile-explanation").textContent = (profile?.explanation || "No validated profile was published.") + " Publication checks do not establish forecast accuracy or permission to operate equipment.";
  if (telemetry) {
    source.value = telemetry.data_mode === "live" ? "mysolark" : "sunny";
    byId("source-state").textContent = telemetry.data_mode === "live" ? `DW ${publication.selection?.wing ?? "1.24"} / ${replay ? "historical scrape" : "latest scrape"}` : "Sunny demo / synthetic replay";
    byId("solar-value").textContent = `${number(telemetry.solar_power_kw)} kW`;
    byId("load-value").textContent = `${number(telemetry.load_power_kw)} kW`;
    byId("voltage-value").textContent = `${telemetry.battery_voltage_v} V`;
    byId("floor-value").textContent = `${evidence.policy.min_battery_voltage_v} V`;
    byId("source-time").textContent = forecastTime(telemetry.observed_at);
    sourceAge();
  } else {
    byId("source-state").textContent = source.value === "mysolark" ? `DW ${publication.selection?.wing ?? "1.24"} / source withheld` : "Source withheld";
    byId("source-age").textContent = publication.observed_age_seconds === null ? "" : `Age at run: ${publication.observed_age_seconds} sec.`;
  }
  showOutputView();
  if (!valid) return;
  const rows = profile.intervals;
  byId("power-value").textContent = number(rows[0].available_kw);
  byId("energy-value").textContent = rows.reduce((total, row) => total + row.energy_kwh, 0).toFixed(3);
  byId("confidence-value").textContent = profile.confidence;
  byId("chart-period").textContent = `${forecastTime(rows[0].starts_at)} to ${forecastTime(rows.at(-1).ends_at)}`;
  byId("profile-intervals").replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of [forecastTime(row.starts_at), number(row.available_kw), number(row.energy_kwh)]) {
      const td = document.createElement("td"); td.textContent = value; tr.append(td);
    }
    byId("profile-intervals").append(tr);
  }
  chart(rows);
}

function clearResult() {
  selectedPublication = null;
  byId("published-profile").hidden = true;
  byId("empty-result").hidden = false;
  byId("request-error").hidden = true;
  byId("inspector-link").href = "/inspector" + (simulation ? "?" + simulationQuery() : "");
  byId("source-state").textContent = "Awaiting a new source snapshot.";
  for (const id of ["solar-value", "load-value", "voltage-value", "floor-value"]) byId(id).textContent = "—";
  byId("source-time").textContent = byId("source-age").textContent = "";
}

async function action(label, callback) {
  busy = true;
  document.querySelectorAll(".run-controls button, .run-controls select, .run-controls input").forEach(control => { control.disabled = true; });
  const started = performance.now();
  byId("run-progress").hidden = false;
  const update = () => { byId("run-progress").textContent = `${label}… ${Math.floor((performance.now() - started) / 1000)} seconds elapsed.`; };
  update();
  const timer = setInterval(update, 1000);
  try { await callback(); }
  catch {
    byId("request-error").hidden = false;
    byId("request-error").textContent = "The result could not be loaded. Try again, or open Inspector to check service health.";
  } finally {
    clearInterval(timer);
    busy = false;
    document.querySelectorAll(".run-controls button, .run-controls select, .run-controls input").forEach(control => { control.disabled = false; });
    syncControls();
    byId("run-progress").hidden = true;
  }
}

runButton.addEventListener("click", () => {
  if (source.value === "mysolark" && byId("time-window").value === "week" && !byId("replay-time").reportValidity()) return;
  action("Running PAP", async () => {
  simulation = null;
  outputView = "forecast";
  clearResult();
  history.replaceState(null, "", "/");
  const episode = await request("/api/v1/pap/run", selection());
  const query = `?episode=${encodeURIComponent(episode.episode_id)}`;
  history.replaceState(null, "", "/" + query);
  byId("inspector-link").href = "/inspector" + query;
  render(await request(`/api/v1/pap/${episode.publication_id}`));
  });
});

function changeSelection() {
  simulation = null;
  clearResult();
  history.replaceState(null, "", "/");
  syncControls();
}
for (const id of ["source", "wing", "time-window", "replay-day", "replay-end-day", "replay-time"]) byId(id).addEventListener("change", changeSelection);
for (const [id, minutes] of [["step-hour", 60], ["step-quarter", 15]]) byId(id).addEventListener("click", () => {
  stepMinutes = minutes;
  sessionStorage.setItem("pap-replay-step", String(minutes));
  // Snap to the chosen grid, anchored to Sunday midnight.
  setReplayTime(replayStart + Math.floor((replayTime() - replayStart) / (minutes * 60000)) * minutes * 60000);
  changeSelection();
});
for (const [id, direction] of [["previous-time", -1], ["next-time", 1]]) byId(id).addEventListener("click", () => {
  setReplayTime(Math.max(replayStart, Math.min(replayEnd - stepMinutes * 60000, replayTime() + direction * stepMinutes * 60000)));
  changeSelection();
});
syncControls();

function renderHistory() {
  byId("simulation-results").replaceChildren();
  for (const result of simulation.results) {
    const tr = document.createElement("tr");
    for (const value of [pacific(result.replay_at), result.status === "valid" ? "Forecast ready" : "Withheld", result.available_kw === null ? "—" : number(result.available_kw), result.confidence ?? "—"]) {
      const td = document.createElement("td"); td.textContent = value; tr.append(td);
    }
    tr.title = result.reason;
    const td = document.createElement("td"), link = document.createElement("a");
    link.textContent = "Inspect";
    link.href = `/inspector?episode=${encodeURIComponent(result.episode_id)}&${simulationQuery()}`;
    td.append(link); tr.append(td); byId("simulation-results").append(tr);
  }
}

async function showSimulation(run) {
  if (simulation?.id !== run.id) { outputView = "recorded"; chartDay = "follow"; }
  simulation = run;
  source.value = "mysolark";
  byId("wing").value = run.wing;
  byId("time-window").value = "week";
  setReplayTime(Date.parse(run.starts_at));
  stepMinutes = run.step_minutes;
  byId("playback-speed").value = String(run.delay_seconds ?? 1);
  byId("replay-end-day").value = inputTime(Date.parse(run.ends_at) - 1).slice(0, 10);
  const last = run.results.at(-1), valid = run.results.filter(result => result.status === "valid").length;
  const days = [...new Set(run.results.map(result => inputTime(Date.parse(result.replay_at)).slice(0, 10)))];
  if (byId("chart-day").dataset.days !== days.join(",")) {
    byId("chart-day").replaceChildren(new Option("Follow playback", "follow"), ...days.map(day => new Option(day, day)));
    byId("chart-day").dataset.days = days.join(",");
  }
  byId("chart-day").value = chartDay;
  byId("chart-day").disabled = !days.length;
  const shown = chartDay === "follow" ? last : run.results.filter(result => inputTime(Date.parse(result.replay_at)).startsWith(chartDay)).at(-1);
  byId("simulation-status").textContent = {running:"Running", pausing:"Finishing step", paused:"Paused", completed:"Finished", failed:"Stopped"}[run.status];
  byId("simulation-status").dataset.status = run.status === "failed" ? "withheld" : "valid";
  byId("simulation-time").textContent = pacific(last?.replay_at ?? run.starts_at);
  byId("simulation-count").textContent = `${run.completed_steps} / ${run.total_steps} steps`;
  byId("simulation-summary").textContent = `${valid} forecasts · ${run.completed_steps - valid} withheld`;
  byId("simulation-progress").max = run.total_steps;
  byId("simulation-progress").value = run.completed_steps;
  byId("simulation-explanation").textContent = run.message || {
    running:`Next: ${pacific(run.next_at)}. Reading data → forecasting → advancing automatically.`,
    pausing:"Finishing the current PAP step before pausing.",
    paused:"Progress saved. Resume continues with the next unfinished step.",
    completed:"Replay complete. Open Results to inspect any step.",
    failed:"PAP stopped. Check Inspector, then resume.",
  }[run.status];
  if (shown && selectedPublication?.id !== shown.publication_id) {
    const publication = await request(`/api/v1/pap/${shown.publication_id}`);
    if (simulation?.id !== run.id) return;
    clearResult();
    render(publication);
  } else if (!shown) {
    history.replaceState(null, "", "/?" + simulationQuery());
    byId("inspector-link").href = "/inspector?" + simulationQuery();
  }
  if (byId("results-dialog").open) renderHistory();
  syncControls();
}
byId("chart-day").addEventListener("change", () => {
  if (!simulation) return;
  chartDay = byId("chart-day").value;
  action("Loading recorded day", () => showSimulation(simulation));
});
byId("playback-speed").addEventListener("change", () => {
  const delay_seconds = Number(byId("playback-speed").value);
  sessionStorage.setItem("pap-playback-delay", String(delay_seconds));
  if (simulation) action("Changing playback speed", async () => {
    await showSimulation(await request(`/api/v1/simulations/${simulation.id}/speed`, {delay_seconds}));
  });
});

byId("start-simulation").addEventListener("click", () => {
  if (!byId("replay-time").reportValidity()) return;
  action("Starting simulation", async () => {
    const run = await request("/api/v1/simulations", {wing:byId("wing").value, starts_at:new Date(replayTime()).toISOString(), ends_at:new Date(playbackEnd()).toISOString(), step_minutes:stepMinutes, delay_seconds:Number(byId("playback-speed").value)});
    clearResult();
    await showSimulation(run);
  });
});
for (const command of ["pause", "resume"]) byId(`${command}-simulation`).addEventListener("click", () => {
  action(command === "pause" ? "Pausing" : "Resuming", async () => {
    await showSimulation(await request(`/api/v1/simulations/${simulation.id}/${command}`, {}));
  });
});
byId("simulation-history").addEventListener("click", () => { renderHistory(); byId("results-dialog").showModal(); });
byId("close-results").addEventListener("click", () => byId("results-dialog").close());

setInterval(async () => {
  if (!simulation || busy || polling) return;
  const id = simulation.id;
  polling = true;
  try {
    const run = await request(`/api/v1/simulations/${id}`);
    if (simulation?.id === id) await showSimulation(run);
  } catch {
    if (simulation?.id === id) {
      byId("simulation-status").textContent = "Connection lost";
      byId("simulation-explanation").textContent = "Progress unavailable; the simulation may still be running. Reconnecting…";
    }
  } finally { polling = false; }
}, 500);

action("Loading saved result", async () => {
  const params = new URLSearchParams(location.search), episodeId = params.get("episode"), simulationId = params.get("simulation");
  if (simulationId) {
    await showSimulation(await request(`/api/v1/simulations/${encodeURIComponent(simulationId)}`));
    return;
  }
  if (episodeId) {
    byId("inspector-link").href = `/inspector?episode=${encodeURIComponent(episodeId)}`;
    const episode = await request(`/api/v1/episodes/${encodeURIComponent(episodeId)}`);
    restoreSelection(episode);
    render(await request(`/api/v1/pap/${episode.publication_id}`));
  } else {
    const latestSimulation = await request("/api/v1/simulations/latest");
    if (latestSimulation) {
      await showSimulation(latestSimulation);
      return;
    }
    const latest = await request("/api/v1/pap/latest");
    if (latest) {
      const episode = await request(`/api/v1/episodes/${encodeURIComponent(latest.episode_id)}`);
      restoreSelection(episode);
      render(latest);
    }
  }
});
setInterval(sourceAge, 30000);
