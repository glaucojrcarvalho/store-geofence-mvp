"use strict";

// This demo intentionally makes no network requests and processes no real GPS.
const STORE = Object.freeze({lat: 50.4501, lng: 30.5234});
const EARTH_RADIUS_M = 6371008.8;
const $ = id => document.getElementById(id);
const latInput = $("lat");
const lngInput = $("lng");
const radiusInput = $("radius");
const insideButton = $("inside");
const outsideButton = $("outside");

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
  insideButton.classList.remove("active");
  outsideButton.classList.remove("active");
  insideButton.setAttribute("aria-pressed", "false");
  outsideButton.setAttribute("aria-pressed", "false");
}
function drawMarker(lat, lng, distance, radius, allowed) {
  const east = (lng - STORE.lng) * Math.cos(toRadians(STORE.lat));
  const north = lat - STORE.lat;
  const bearingLength = Math.hypot(east, north);
  const pixels = Math.min(148, distance / radius * 95);
  const x = bearingLength ? east / bearingLength * pixels : 0;
  const y = bearingLength ? -north / bearingLength * pixels : 0;
  $("point").style.left = "calc(50% + " + x.toFixed(2) + "px)";
  $("point").style.top = "calc(50% + " + y.toFixed(2) + "px)";
  $("point").classList.toggle("is-outside", !allowed);
  $("viz-distance").textContent = Math.round(distance).toLocaleString("en-US") + " m / " + radius + " m";
}
function evaluate() {
  const values = validateValues();
  if (!values) {
    $("result-status").textContent = "INVALID COORDINATES";
    $("distance").textContent = "—";
    $("result-text").textContent = "Enter valid latitude and longitude values to continue.";
    return;
  }
  const {lat, lng, radius} = values;
  const distance = haversine(lat, lng);
  const allowed = distance <= radius;
  $("radius-value").textContent = radius + " m";
  $("result-status").textContent = allowed ? "INSIDE GEOFENCE" : "OUTSIDE GEOFENCE";
  $("result-status").classList.toggle("outside", !allowed);
  $("distance").replaceChildren(
    document.createTextNode(distance.toLocaleString("en-US", {maximumFractionDigits: 1}) + " "),
    Object.assign(document.createElement("small"), {textContent: "metres"})
  );
  $("result-text").textContent = allowed
    ? "The reported location falls inside the sample store's permitted radius."
    : "The reported location is beyond the sample store's permitted radius.";
  drawMarker(lat, lng, distance, radius, allowed);
}
function setExample(lat, lng, chosenButton) {
  latInput.value = lat;
  lngInput.value = lng;
  clearPreset();
  chosenButton.classList.add("active");
  chosenButton.setAttribute("aria-pressed", "true");
  evaluate();
}
$("sim-form").addEventListener("submit", event => { event.preventDefault(); evaluate(); });
insideButton.addEventListener("click", () => setExample(50.4507, 30.5234, insideButton));
outsideButton.addEventListener("click", () => setExample(50.454, 30.5234, outsideButton));
radiusInput.addEventListener("input", evaluate);
latInput.addEventListener("input", () => { clearPreset(); evaluate(); });
lngInput.addEventListener("input", () => { clearPreset(); evaluate(); });
setExample(50.4507, 30.5234, insideButton);
