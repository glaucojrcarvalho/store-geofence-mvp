import { test, expect } from "@playwright/test";

const URL = "http://127.0.0.1:4173";

test("store presets update gating, then worker can complete only an eligible task", async ({ page }) => {
  await page.goto(URL);
  await expect(page.locator("#result-status")).toHaveText("INSIDE GEOFENCE");
  await expect(page.locator("#complete-task")).toBeEnabled();

  await page.getByRole("button", { name: /Outside/ }).click();
  await expect(page.locator("#result-status")).toHaveText("OUTSIDE GEOFENCE");
  await expect(page.locator("#complete-task")).toBeDisabled();

  await page.getByRole("button", { name: /Near boundary/ }).click();
  await expect(page.locator("#result-status")).toHaveText("INSIDE GEOFENCE");
  await page.locator("#complete-task").click();
  await expect(page.locator("#complete-task")).toBeDisabled();
  await expect(page.locator("#activity-log li").first()).toContainText("Synthetic task completed");
});

test("radius and manual coordinates change the plotted eligibility", async ({ page }) => {
  await page.goto(URL);
  const ring = page.locator("#ring");
  const originalSize = await ring.evaluate(element => parseFloat(element.style.width));

  await page.locator("#radius").evaluate(element => { element.value = "250"; element.dispatchEvent(new Event("input", {bubbles: true})); });
  await expect(page.locator("#radius-value")).toHaveText("250 m");
  const nextSize = await ring.evaluate(element => parseFloat(element.style.width));
  expect(nextSize).toBeGreaterThan(originalSize * 2);

  await page.locator("#lat").fill("99");
  await expect(page.locator("#result-status")).toHaveText("INVALID COORDINATES");
  await expect(page.locator("#complete-task")).toBeDisabled();
});

test("changing synthetic stores resets task; diagram and keyboard move worker", async ({ page }) => {
  await page.goto(URL);
  await page.locator("#complete-task").click();
  await page.locator("#store-select").selectOption("lviv");
  await expect(page.locator("#task-name")).toHaveText("Confirm stock delivery");
  await expect(page.locator("#complete-task")).toBeEnabled();

  const before = Number(await page.locator("#lat").inputValue());
  await page.locator("#viz").focus();
  await page.keyboard.press("ArrowUp");
  expect(Number(await page.locator("#lat").inputValue())).toBeGreaterThan(before);

  await page.locator("#viz").click({ position: { x: 10, y: 15 } });
  await expect(page.locator("#result-status")).toHaveText("OUTSIDE GEOFENCE");
  await expect(page.locator("#complete-task")).toBeDisabled();
  await page.locator("#viz").focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#result-status")).toHaveText("INSIDE GEOFENCE");

  await page.locator("#reset-demo").click();
  await expect(page.locator("#store-select")).toHaveValue("kyiv");
  await expect(page.locator("#complete-task")).toBeEnabled();
});

test("mobile experience fits screen and requires no external network or GPS", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const external = [];
  page.on("request", request => {
    if (!request.url().startsWith(URL)) external.push(request.url());
  });
  await page.goto(URL);
  await expect(page.locator("#complete-task")).toBeEnabled();
  await page.locator("#outside").click();
  await expect(page.locator("#complete-task")).toBeDisabled();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  expect(external).toEqual([]);
});
