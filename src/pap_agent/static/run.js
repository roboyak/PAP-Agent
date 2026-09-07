const byId = id => document.getElementById(id);
const source = byId("source"), runButton = byId("run-workflow");
let selectedPublication = null;
source.value = document.body.dataset.defaultSource;
const utc = value => new Date(value).toISOString().replace("T", " ").slice(0, 16) + " UTC";
const number = value => Number(value).toFixed(3).replace(/\.?0+$/, "");

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
  const age = Math.max(0, Math.round((Date.now() - Date.parse(telemetry.observed_at)) / 1000));
  byId("source-age").textContent = telemetry.data_mode === "live"
    ? `Recorded scrape: ${age < 60 ? `${age} seconds` : `${Math.floor(age / 60)} minutes`} old.${age > 300 ? " Stale now; run again for a fresh check." : ""}`
    : "Synthetic replay clock; not a live measurement.";
}

function chart(intervals) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 940 280");
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
    const y = 224 - step * 46;
    add("line", {x1:50, x2:916, y1:y, y2:y, stroke:"#b3ab8b", "stroke-width":1});
    add("text", {x:38, y:y+4, "text-anchor":"end", class:"axis-label"}, number(maximum * step / 4));
  }
  intervals.forEach((row, i) => {
    const x = 66 + i * 71, height = row.available_kw / maximum * 184, y = 224 - height;
    if (height > 0) {
      add("rect", {x, y, width:40, height, fill:"#7f9b85", stroke:"#403e2e"});
      add("polygon", {points:`${x},${y} ${x+7},${y-5} ${x+47},${y-5} ${x+40},${y}`, fill:"#b7c8a3", stroke:"#403e2e"});
      add("polygon", {points:`${x+40},${y} ${x+47},${y-5} ${x+47},219 ${x+40},224`, fill:"#657e6b", stroke:"#403e2e"});
    } else add("line", {x1:x,x2:x+40,y1:224,y2:224,stroke:"#403e2e","stroke-width":3});
    add("text", {x:x+20, y:y-13, "text-anchor":"middle", class:"bar-label"}, number(row.available_kw));
    add("text", {x:x+20, y:250, "text-anchor":"middle", class:"axis-label"}, row.starts_at.slice(11,16));
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
  byId("publication-status").textContent = valid ? "Published evaluation" : "Withheld";
  byId("publication-status").dataset.status = valid ? "valid" : "withheld";
  byId("run-status").textContent = `Saved ${utc(publication.generated_at)}. ${publication.reason}`;
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
    byId("source-state").textContent = telemetry.data_mode === "live" ? "MySolArk / persisted scrape" : "Sunny demo / synthetic replay";
    byId("solar-value").textContent = `${number(telemetry.solar_power_kw)} kW`;
    byId("load-value").textContent = `${number(telemetry.load_power_kw)} kW`;
    byId("voltage-value").textContent = `${telemetry.battery_voltage_v} V`;
    byId("floor-value").textContent = `${evidence.policy.min_battery_voltage_v} V`;
    byId("source-time").textContent = utc(telemetry.observed_at);
    sourceAge();
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
  runButton.disabled = source.disabled = true;
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
    runButton.disabled = source.disabled = false;
    byId("run-progress").hidden = true;
  }
}

runButton.addEventListener("click", () => action("Running PAP", async () => {
  clearResult();
  history.replaceState(null, "", "/");
  const episode = await request("/api/v1/pap/run", {scenario:source.value});
  const query = `?episode=${encodeURIComponent(episode.episode_id)}`;
  history.replaceState(null, "", "/" + query);
  byId("inspector-link").href = "/inspector" + query;
  render(await request(`/api/v1/pap/${episode.publication_id}`));
}));

source.addEventListener("change", () => {
  clearResult();
  history.replaceState(null, "", "/");
});

action("Loading saved result", async () => {
  const episodeId = new URLSearchParams(location.search).get("episode");
  if (episodeId) {
    byId("inspector-link").href = `/inspector?episode=${encodeURIComponent(episodeId)}`;
    const episode = await request(`/api/v1/episodes/${encodeURIComponent(episodeId)}`);
    source.value = episode.scenario;
    render(await request(`/api/v1/pap/${episode.publication_id}`));
  } else {
    const latest = await request("/api/v1/pap/latest");
    if (latest) {
      const episode = await request(`/api/v1/episodes/${encodeURIComponent(latest.episode_id)}`);
      source.value = episode.scenario;
      render(latest);
    }
  }
});
setInterval(sourceAge, 30000);
