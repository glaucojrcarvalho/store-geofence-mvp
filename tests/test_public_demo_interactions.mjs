import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import test from "node:test";

// Dependency-free DOM harness for the standalone no-network demo.
class FakeClassList {
  constructor() { this.values = new Set(); }
  add(value) { this.values.add(value); }
  remove(value) { this.values.delete(value); }
  contains(value) { return this.values.has(value); }
  toggle(value, enabled) {
    if (enabled === undefined ? !this.contains(value) : enabled) this.add(value);
    else this.remove(value);
  }
}
class FakeElement {
  constructor(id) {
    this.id = id;
    this.value = "";
    this.textContent = "";
    this.disabled = false;
    this.attributes = {};
    this.style = {};
    this.listeners = {};
    this.classList = new FakeClassList();
    this.children = [];
    this.clientWidth = 420;
    this.clientHeight = 320;
  }
  get valueAsNumber() {
    return this.value.trim() === "" ? NaN : Number(this.value);
  }
  checkValidity() {
    const n = this.valueAsNumber;
    if (!Number.isFinite(n)) return false;
    if (this.id === "lat") return n >= -90 && n <= 90;
    if (this.id === "lng") return n >= -180 && n <= 180;
    return true;
  }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  setAttribute(name, value) { this.attributes[name] = value; }
  replaceChildren(...children) { this.children = [...children]; }
  appendChild(child) { this.children.push(child); }
  getBoundingClientRect() {
    return {left: 0, top: 0, width: this.clientWidth, height: this.clientHeight};
  }
  fire(name, values = {}) {
    const event = {preventDefault() { this.prevented = true; }, ...values};
    assert.equal(typeof this.listeners[name], "function", "Missing listener " + this.id + "." + name);
    this.listeners[name](event);
    return event;
  }
}
function newLab() {
  const ids = [
    "lat", "lng", "radius", "radius-value", "inside", "edge", "outside",
    "store-select", "store-meta", "task-name", "task-description", "task-note",
    "complete-task", "viz", "ring", "point", "viz-distance", "result",
    "result-status", "distance", "result-text", "sim-form", "activity-log", "reset-demo"
  ];
  const elements = Object.fromEntries(ids.map(id => [id, new FakeElement(id)]));
  elements.lat.value = "50.4501";
  elements.lng.value = "30.5234";
  elements.radius.value = "100";
  elements["store-select"].value = "kyiv";
  const document = {
    getElementById(id) {
      assert.ok(elements[id], "Missing expected DOM id: " + id);
      return elements[id];
    },
    createTextNode(text) { return {textContent: text}; },
    createElement(name) { return new FakeElement(name); }
  };
  const window = {addEventListener() {}};
  const source = fs.readFileSync(new URL("../public-demo/app.js", import.meta.url), "utf8");
  vm.runInNewContext(source, {document, window, Math, Number, Object, Intl}, {timeout: 2000});
  return elements;
}
test("inside/outside/edge scenarios update eligibility and ring diameter", () => {
  const e = newLab();
  assert.equal(e["result-status"].textContent, "INSIDE GEOFENCE");
  assert.equal(e["complete-task"].disabled, false);
  const initialWidth = parseFloat(e.ring.style.width);
  assert.ok(initialWidth > 0);
  e.outside.fire("click");
  assert.equal(e["result-status"].textContent, "OUTSIDE GEOFENCE");
  assert.equal(e["complete-task"].disabled, true);
  e.edge.fire("click");
  assert.equal(e["result-status"].textContent, "INSIDE GEOFENCE");
  e.radius.value = "250";
  e.radius.fire("input");
  assert.ok(parseFloat(e.ring.style.width) > initialWidth * 2);
  assert.equal(e.edge.attributes["aria-pressed"], "false");
});
test("task completion is gated and subsequent store selection resets it", () => {
  const e = newLab();
  e.outside.fire("click");
  e["complete-task"].fire("click");
  assert.equal(e["complete-task"].disabled, true);
  assert.notEqual(e["complete-task"].textContent, "Task completed ✓");
  e.inside.fire("click");
  e["complete-task"].fire("click");
  assert.equal(e["complete-task"].textContent, "Task completed ✓");
  assert.equal(e["complete-task"].disabled, true);
  assert.ok(e["activity-log"].children[0].textContent.includes("Synthetic task completed"));
  e["store-select"].value = "lviv";
  e["store-select"].fire("change");
  assert.equal(e["task-name"].textContent, "Confirm stock delivery");
  assert.equal(e["complete-task"].disabled, false);
  e["reset-demo"].fire("click");
  assert.equal(e["store-select"].value, "kyiv");
  assert.equal(e["complete-task"].disabled, false);
  assert.equal(e["activity-log"].children.length, 1);
});
test("diagram pointer and keyboard arrows alter synthetic position", () => {
  const e = newLab();
  const latBefore = e.lat.valueAsNumber;
  e.viz.fire("keydown", {key: "ArrowUp"});
  assert.ok(e.lat.valueAsNumber > latBefore);
  const left = e.lat.valueAsNumber;
  e.viz.fire("click", {clientX: 330, clientY: 160});
  assert.ok(e.lng.valueAsNumber > 30.5234);
  assert.equal(e["result-status"].textContent, "OUTSIDE GEOFENCE");
  assert.notEqual(e.lat.valueAsNumber, left);
  assert.ok(e["activity-log"].children[0].textContent.includes("Diagram position"));
});
test("invalid coordinates disable execution and never create an eligible decision", () => {
  const e = newLab();
  e.lat.value = "91";
  e.lat.fire("input");
  assert.equal(e["result-status"].textContent, "INVALID COORDINATES");
  assert.equal(e["complete-task"].disabled, true);
  assert.equal(e.distance.textContent, "—");
  assert.ok(e.point.classList.contains("is-invalid"));
});
test("only six synthetic activity entries remain in page memory", () => {
  const e = newLab();
  for (let n = 0; n < 12; n++) e.outside.fire("click");
  assert.equal(e["activity-log"].children.length, 6);
  assert.ok(e["activity-log"].children[0].textContent.startsWith("#13 "));
  assert.ok(e["activity-log"].children[0].textContent.includes("blocked"));
});
