const byId = id => document.getElementById(id);
const source = byId("source"), runButton = byId("run-workflow");
let selectedPublication = null;
let stepMinutes = sessionStorage.getItem("pap-replay-step") === "15" ? 15 : 60, busy = false;
const replayStart = Date.parse("2026-08-30T00:00:00-07:00"), replayEnd = Date.parse("2026-09-06T00:00:00-07:00");
source.value = document.body.dataset.defaultSource;
const utc = value => new Date(value).toISOString().replace("T", " ").slice(0, 16) + " UTC";
const number = value => Number(value).toFixed(3).replace(/\.?0+$/, "");

// This fixed week is entirely PDT; stored/API timestamps remain UTC.
const replayTime = () => Date.parse(byId("replay-time").value + "-07:00");
const inputTime = ms => new Date(ms - 7 * 3600000).toISOString().slice(0, 16);
function selection() {
  return {scenario:source.value, wing:byId("wing").value,
    replay_at:source.value === "mysolark" && byId("time-window").value === "week"
      ? new Date(replayTime()).toISOString() : null};
}
function syncControls() {
  const real = source.value === "mysolark", replay = real && byId("time-window").value === "week";
  byId("wing-control").hidden = byId("window-control").hidden = !real;
  byId("replay-controls").hidden = !replay;
  byId("replay-time").step = stepMinutes * 60;
  byId("replay-time").max = inputTime(replayEnd - stepMinutes * 60000);
  byId("step-hour").setAttribute("aria-pressed", String(stepMinutes === 60));
  byId("step-quarter").setAttribute("aria-pressed", String(stepMinutes === 15));
  byId("previous-time").disabled = busy || replayTime() <= replayStart;
  byId("next-time").disabled = busy || replayTime() >= replayEnd - stepMinutes * 60000;
  byId("selection-note").textContent = replay
    ? `One snapshot per run · Sun Aug 30, 00:00 to Sun Sep 6, 00:00 Pacific (end excluded) · Step ${stepMinutes} min; forecast stays hourly.`
    : real ? `DW ${byId("wing").value} · Reads the latest persisted scrape. Stale data is withheld.` : "Synthetic sunny fixture; not measured telemetry.";
}
function restoreSelection(episode) {
  source.value = episode.scenario;
  const selected = episode.selection ?? {};
  byId("wing").value = selected.wing ?? "1.24";
  byId("time-window").value = selected.replay_at ? "week" : "live";
  if (selected.replay_at) {
    byId("replay-time").value = inputTime(Date.parse(selected.replay_at));
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
    add("text", {x:x+20, y:184, "text-anchor":"middle", class:"axis-label"}, row.starts_at.slice(11,16));
  });
  byId("forecast-chart").replaceChildren(svg);
}

function render(publication) {
  selectedPublication = publication;
  const valid = publication.status === "valid", profile = publication.profile;
  const evidence = publication.evidence, telemetry = evidence?.telemetry;
  const query = `?episode=${encodeURIComponent(publication.episode_id)}`;
  history.replaceState(null, "", "/" + query);
  byId("inspector-link").href = byId("view-inspector").href = "/inspector" + query;
  byId("empty-result").hidden = true;
  byId("published-profile").hidden = false;
  byId("valid-output").hidden = !valid;
  const replay = publication.selection?.replay_at;
  byId("publication-status").textContent = valid ? replay ? "Historical replay" : "Published evaluation" : "Withheld";
  byId("publication-status").dataset.status = valid ? "valid" : "withheld";
  byId("run-status").textContent = `${replay ? `Replay ${utc(replay)}. ` : ""}Saved ${utc(publication.generated_at)}. ${publication.reason}`;
  byId("run-meta").textContent = `Run ${publication.episode_id}`;
  byId("guidance-heading").textContent = valid ? "What the agent says" : "Why the result was withheld";
  const advice = [publication.search?.guidance?.summary, publication.interpretation?.advice?.explanation].filter(Boolean);
  if (publication.interpretation && !publication.interpretation.accepted) advice.push("Optional model advice was unavailable or rejected. Inspect Subagent for the recorded attempt.");
  byId("agent-guidance").textContent = valid
    ? advice.join(" ") || "The linear workflow published the calculated solar-surplus profile. No model advice was needed."
    : [publication.reason, ...advice].join(" ");
  byId("profile-explanation").textContent = (profile?.explanation || "No validated profile was published.") + " Publication checks do not establish forecast accuracy or permission to operate equipment.";
  if (telemetry) {
    source.value = telemetry.data_mode === "live" ? "mysolark" : "sunny";
    byId("source-state").textContent = telemetry.data_mode === "live" ? `DW ${publication.selection?.wing ?? "1.24"} / ${replay ? "historical scrape" : "latest scrape"}` : "Sunny demo / synthetic replay";
    byId("solar-value").textContent = `${number(telemetry.solar_power_kw)} kW`;
    byId("load-value").textContent = `${number(telemetry.load_power_kw)} kW`;
    byId("voltage-value").textContent = `${telemetry.battery_voltage_v} V`;
    byId("floor-value").textContent = `${evidence.policy.min_battery_voltage_v} V`;
    byId("source-time").textContent = utc(telemetry.observed_at);
    sourceAge();
  } else {
    byId("source-state").textContent = source.value === "mysolark" ? `DW ${publication.selection?.wing ?? "1.24"} / source withheld` : "Source withheld";
    byId("source-age").textContent = publication.observed_age_seconds === null ? "" : `Age at run: ${publication.observed_age_seconds} sec.`;
  }
  if (!valid) return;
  const rows = profile.intervals;
  byId("power-value").textContent = number(rows[0].available_kw);
  byId("energy-value").textContent = rows.reduce((total, row) => total + row.energy_kwh, 0).toFixed(3);
  byId("confidence-value").textContent = profile.confidence;
  byId("chart-period").textContent = `${utc(rows[0].starts_at)} to ${utc(rows.at(-1).ends_at)}`;
  byId("profile-intervals").replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of [utc(row.starts_at), number(row.available_kw), number(row.energy_kwh)]) {
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
  byId("inspector-link").href = "/inspector";
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
  clearResult();
  history.replaceState(null, "", "/");
  syncControls();
}
for (const id of ["source", "wing", "time-window", "replay-time"]) byId(id).addEventListener("change", changeSelection);
for (const [id, minutes] of [["step-hour", 60], ["step-quarter", 15]]) byId(id).addEventListener("click", () => {
  stepMinutes = minutes;
  sessionStorage.setItem("pap-replay-step", String(minutes));
  // Snap to the chosen grid, anchored to Sunday midnight.
  byId("replay-time").value = inputTime(replayStart + Math.floor((replayTime() - replayStart) / (minutes * 60000)) * minutes * 60000);
  changeSelection();
});
for (const [id, direction] of [["previous-time", -1], ["next-time", 1]]) byId(id).addEventListener("click", () => {
  byId("replay-time").value = inputTime(Math.max(replayStart, Math.min(replayEnd - stepMinutes * 60000, replayTime() + direction * stepMinutes * 60000)));
  changeSelection();
});
syncControls();

action("Loading saved result", async () => {
  const episodeId = new URLSearchParams(location.search).get("episode");
  if (episodeId) {
    byId("inspector-link").href = `/inspector?episode=${encodeURIComponent(episodeId)}`;
    const episode = await request(`/api/v1/episodes/${encodeURIComponent(episodeId)}`);
    restoreSelection(episode);
    render(await request(`/api/v1/pap/${episode.publication_id}`));
  } else {
    const latest = await request("/api/v1/pap/latest");
    if (latest) {
      const episode = await request(`/api/v1/episodes/${encodeURIComponent(latest.episode_id)}`);
      restoreSelection(episode);
      render(latest);
    }
  }
});
setInterval(sourceAge, 30000);
