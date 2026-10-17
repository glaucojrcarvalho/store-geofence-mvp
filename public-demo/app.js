"use strict";

// A standalone synthetic simulation. No accounts, persisted activity, GPS,
// browser storage, customer records, or network requests are used.
const STORES = Object.freeze({
  kyiv: Object.freeze({
    name: "Central Kyiv · Retail",
    lat: 50.4501, lng: 30.5234,
    task: "Verify retail display",
    description: "Simulate a field worker confirming the store's display after arriving inside its configured perimeter."
  }),
  lviv: Object.freeze({
    name: "Lviv · Distribution",
    lat: 49.8397, lng: 24.0297,
    task: "Confirm stock delivery",
    description: "Simulate a warehouse worker confirming a delivery after reaching the distribution site."
  }),
  warsaw: Object.freeze({
    name: "Warsaw · Service hub",
    lat: 52.2297, lng: 21.0122,
    task: "Complete service visit",
    description: "Simulate a technician closing a service visit when the reported position meets the radial rule."
  })
});
const EARTH_RADIUS_M = 6371008.8;
const METRES_PER_DEGREE = 111195;
const MAX_PLOT_DISTANCE_M = 500;
const $ = id => document.getElementById(id);

const latInput = $("lat");
const lngInput = $("lng");
const radiusInput = $("radius");
const storeSelect = $("store-select");
const presets = {
  inside: $("inside"),
  edge: $("edge"),
  outside: $("outside")
};
const taskButton = $("complete-task");
const viz = $("viz");
let STORE = STORES.kyiv;
let taskDone = false;
let currentDecision = null;
let eventNumber = 0;
const activity = [];

function toRadians(degrees) { return degrees * Math.PI / 180; }
function haversine(lat, lng) {
  const lat1 = toRadians(STORE.lat);
  const lat2 = toRadians(lat);
  const deltaLat = lat2 - lat1;
  const deltaLng = toRadians(lng - STORE.lng);
  const a = Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(Math.max(0, a))));
}
function formatMetres(distance) {
  return distance.toLocaleString("en-US", {maximumFractionDigits: 1});
}
function validateValues() {
  const lat = latInput.valueAsNumber;
  const lng = lngInput.valueAsNumber;
  const radius = radiusInput.valueAsNumber;
  if (!latInput.checkValidity() || !lngInput.checkValidity() ||
      !Number.isFinite(lat) || !Number.isFinite(lng) ||
      lat < -90 || lat > 90 || lng < -180 || lng > 180 ||
      !Number.isFinite(radius) || radius < 25 || radius > 500) {
    return null;
  }
  return {lat, lng, radius};
}
function clearPreset() {
  Object.values(presets).forEach(button => {
    button.classList.remove("active");
    button.setAttribute("aria-pressed", "false");
  });
}
function plotScale() {
  // Both the marker and the ring share one fixed 500 m scale. Previously the
  // ring never changed as the user moved the radius slider.
  return Math.min(142, Math.max(50, Math.min(viz.clientWidth, viz.clientHeight) / 2 - 21));
}
function drawMarker(lat, lng, distance, radius, allowed) {
  const maxPixels = plotScale();
  const ringDiameter = radius / MAX_PLOT_DISTANCE_M * maxPixels * 2;
  $("ring").style.width = ringDiameter.toFixed(2) + "px";
  $("ring").style.height = ringDiameter.toFixed(2) + "px";

  const east = (lng - STORE.lng) * METRES_PER_DEGREE * Math.cos(toRadians(STORE.lat));
  const north = (lat - STORE.lat) * METRES_PER_DEGREE;
  const vectorLength = Math.hypot(east, north);
  const distancePixels = Math.min(maxPixels, distance / MAX_PLOT_DISTANCE_M * maxPixels);
  const x = vectorLength ? east / vectorLength * distancePixels : 0;
  const y = vectorLength ? -north / vectorLength * distancePixels : 0;
  $("point").style.left = "calc(50% + " + x.toFixed(2) + "px)";
  $("point").style.top = "calc(50% + " + y.toFixed(2) + "px)";
  $("point").classList.toggle("is-outside", !allowed);
  $("viz-distance").textContent = formatMetres(distance) + " m from center · limit " + radius + " m";
}
function updateTaskState() {
  taskButton.disabled = taskDone || !currentDecision || !currentDecision.allowed;
  taskButton.textContent = taskDone ? "Task completed ✓" : "Complete simulated task →";
  $("task-note").textContent = taskDone
    ? "Synthetic task completed. Reset the lab or select another store to try again."
    : !currentDecision
      ? "Enter valid coordinates to evaluate this task."
      : currentDecision.allowed
        ? "Eligible: reported position is inside the sample geofence. No real presence is verified."
        : "Blocked: move the synthetic worker inside the perimeter to complete this task.";
}
function evaluate() {
  const values = validateValues();
  $("radius-value").textContent = radiusInput.value + " m";
  if (!values) {
    currentDecision = null;
    $("result-status").textContent = "INVALID COORDINATES";
    $("result-status").classList.remove("outside");
    $("distance").textContent = "—";
    $("result-text").textContent = "Enter a valid latitude (−90 to 90) and longitude (−180 to 180).";
    $("point").classList.add("is-invalid");
    updateTaskState();
    return null;
  }
  const {lat, lng, radius} = values;
  const distance = haversine(lat, lng);
  const allowed = distance <= radius;
  currentDecision = {lat, lng, radius, distance, allowed};
  $("point").classList.remove("is-invalid");
  $("result-status").textContent = allowed ? "INSIDE GEOFENCE" : "OUTSIDE GEOFENCE";
  $("result-status").classList.toggle("outside", !allowed);
  $("distance").replaceChildren(
    document.createTextNode(formatMetres(distance) + " "),
    Object.assign(document.createElement("small"), {textContent: "metres"})
  );
  const delta = Math.abs(radius - distance);
  $("result-text").textContent = allowed
    ? "Eligible: within the configured radius, with " + formatMetres(delta) + " m to spare."
    : "Blocked: " + formatMetres(delta) + " m beyond the configured radius.";
  drawMarker(lat, lng, distance, radius, allowed);
  updateTaskState();
  return currentDecision;
}
function renderActivity() {
  const list = $("activity-log");
  list.replaceChildren();
  activity.forEach(message => {
    const item = document.createElement("li");
    item.textContent = message;
    list.appendChild(item);
  });
}
function logDecision(action) {
  const decision = currentDecision;
  const verdict = !decision ? "invalid inputs" : decision.allowed ? "eligible" : "blocked";
  const detail = decision ? " · " + formatMetres(decision.distance) + " m / " + decision.radius + " m" : "";
  activity.unshift("#" + (++eventNumber) + " " + action + " — " + verdict + detail);
  if (activity.length > 6) activity.pop();
  renderActivity();
}
function setSyntheticPosition(lat, lng, description) {
  latInput.value = lat.toFixed(7);
  lngInput.value = lng.toFixed(7);
  clearPreset();
  evaluate();
  logDecision(description);
}
function setScenario(name) {
  const factor = name === "inside" ? 0.35 : name === "edge" ? 0.98 : 1.6;
  const sampleDistance = factor * radiusInput.valueAsNumber;
  latInput.value = (STORE.lat + sampleDistance / METRES_PER_DEGREE).toFixed(7);
  lngInput.value = STORE.lng.toFixed(7);
  clearPreset();
  presets[name].classList.add("active");
  presets[name].setAttribute("aria-pressed", "true");
  evaluate();
  logDecision(STORE.name + " · " + (name === "edge" ? "near boundary" : name));
}
function chooseStore() {
  STORE = STORES[storeSelect.value] || STORES.kyiv;
  taskDone = false;
  $("store-meta").textContent = "Illustrative center: " + STORE.lat.toFixed(4) +
    "° N, " + STORE.lng.toFixed(4) + "° E. No real store records.";
  $("task-name").textContent = STORE.task;
  $("task-description").textContent = STORE.description;
  setScenario("inside");
}
function placeFromDiagram(clientX, clientY) {
  const rect = viz.getBoundingClientRect();
  const x = clientX - rect.left - rect.width / 2;
  const y = clientY - rect.top - rect.height / 2;
  const scale = MAX_PLOT_DISTANCE_M / plotScale();
  const lat = STORE.lat - y * scale / METRES_PER_DEGREE;
  const lng = STORE.lng + x * scale /
    (METRES_PER_DEGREE * Math.cos(toRadians(STORE.lat)));
  setSyntheticPosition(lat, lng, "Diagram position");
}

$("sim-form").addEventListener("submit", event => {
  event.preventDefault();
  evaluate();
  logDecision("Manual evaluation");
});
presets.inside.addEventListener("click", () => setScenario("inside"));
presets.edge.addEventListener("click", () => setScenario("edge"));
presets.outside.addEventListener("click", () => setScenario("outside"));
storeSelect.addEventListener("change", chooseStore);
radiusInput.addEventListener("input", () => { clearPreset(); evaluate(); });
latInput.addEventListener("input", () => { clearPreset(); evaluate(); });
lngInput.addEventListener("input", () => { clearPreset(); evaluate(); });
viz.addEventListener("click", event => placeFromDiagram(event.clientX, event.clientY));
viz.addEventListener("keydown", event => {
  const step = 25 / METRES_PER_DEGREE;
  const currentLat = Number.isFinite(latInput.valueAsNumber) ? latInput.valueAsNumber : STORE.lat;
  const currentLng = Number.isFinite(lngInput.valueAsNumber) ? lngInput.valueAsNumber : STORE.lng;
  let lat = currentLat;
  let lng = currentLng;
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    setSyntheticPosition(STORE.lat, STORE.lng, "Keyboard center");
    return;
  }
  switch (event.key) {
    case "ArrowUp": lat += step; break;
    case "ArrowDown": lat -= step; break;
    case "ArrowRight": lng += step / Math.cos(toRadians(STORE.lat)); break;
    case "ArrowLeft": lng -= step / Math.cos(toRadians(STORE.lat)); break;
    default: return;
  }
  event.preventDefault();
  setSyntheticPosition(lat, lng, "Keyboard move · 25 m");
});
taskButton.addEventListener("click", () => {
  if (!currentDecision || !currentDecision.allowed || taskDone) return;
  taskDone = true;
  updateTaskState();
  logDecision("Synthetic task completed");
});
$("reset-demo").addEventListener("click", () => {
  activity.length = 0;
  eventNumber = 0;
  storeSelect.value = "kyiv";
  radiusInput.value = "100";
  taskDone = false;
  chooseStore();
});
window.addEventListener("resize", () => {
  if (currentDecision) drawMarker(
    currentDecision.lat, currentDecision.lng,
    currentDecision.distance, currentDecision.radius,
    currentDecision.allowed
  );
});
chooseStore();
