import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("campaign, menu and department handoff", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "THE NEW PERSPECTIVE" }),
  ).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  expect(
    await page
      .locator(".hero h1")
      .evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
  ).toBeGreaterThan(56);
  expect(
    await page
      .locator(".campaign-wordmark")
      .evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
  ).toBeGreaterThan(80);
  await page.screenshot({
    path: "test-results/home-desktop.png",
    fullPage: false,
  });
  const mark = page.locator(".campaign-wordmark");
  const before = await mark.boundingBox();
  await page.locator(".campaign-block.video").scrollIntoViewIfNeeded();
  await expect
    .poll(
      async () =>
        await mark.evaluate((el) => Math.round(el.getBoundingClientRect().top)),
    )
    .toBe(Math.round(before!.y));
  await page.getByRole("button", { name: "Open menu" }).click();
  await expect(page.getByRole("dialog", { name: "Navigation" })).toBeVisible();
  await page.screenshot({ path: "test-results/menu-desktop.png" });
  await page.getByRole("button", { name: "Close Navigation" }).click();
  await page.evaluate(() => scrollTo(0, 0));
  await page
    .getByRole("button", { name: "Home department", exact: true })
    .click();
  await expect(page.locator("[data-testid=campaign-sequence]")).toHaveAttribute(
    "data-department",
    "home",
  );
  await page.getByRole("link", { name: "SCROLL DOWN", exact: true }).click();
  await expect(page).toHaveURL(/collections\/home-new-in/);
  await expect(
    page.locator("#new-collection .product-card").first(),
  ).toBeVisible();
});

test("three views, exact SKU bag, development order", async ({ page }) => {
  await page.goto("/women");
  await page.getByRole("button", { name: "View 2: Gallery" }).click();
  await expect(page.locator(".product-grid")).toHaveClass(/view-2/);
  await page.screenshot({ path: "test-results/catalogue-desktop.png" });
  await page.getByRole("button", { name: "View 3: Compact" }).click();
  await expect(page.locator(".product-grid")).toHaveClass(/view-3/);
  await page.locator(".product-card .product-image").first().click();
  await expect(page.locator(".continuation-gallery img")).toHaveCount(4);
  await page.screenshot({ path: "test-results/product-desktop.png" });
  await page.getByRole("button", { name: "ADD", exact: true }).first().click();
  const dialog = page.getByRole("dialog", { name: "Choose your options" });
  await dialog.getByRole("button", { name: "M", exact: true }).click();
  await dialog.getByRole("button", { name: "ADD TO BAG", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await page.goto("/cart");
  await expect(page.locator(".bag-item")).toHaveCount(1);
  await page.screenshot({ path: "test-results/bag-desktop.png" });
  await page.getByRole("link", { name: /CONTINUE \(/ }).click();
  for (const [label, value] of Object.entries({
    "Full name": "Development Shopper",
    "Email address": "shopper@example.test",
    "Mobile number": "9876543210",
    Address: "12 Development Road",
    City: "Mumbai",
    State: "Maharashtra",
    "PIN code": "400001",
  }))
    await page.getByLabel(label, { exact: true }).fill(value);
  await page.getByRole("button", { name: "CONTINUE TO REVIEW" }).click();
  await page.getByRole("button", { name: "PLACE DEVELOPMENT ORDER" }).click();
  await expect(
    page.getByRole("heading", { name: "Thank you. It’s yours." }),
  ).toBeVisible();
});

test("mobile navigation and accessibility", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.screenshot({ path: "test-results/home-mobile.png" });
  await page.getByRole("button", { name: "Open menu" }).click();
  await expect(page.getByRole("dialog", { name: "Navigation" })).toBeVisible();
  await page.getByRole("link", { name: "VIEW ALL", exact: true }).click();
  await expect(page).toHaveURL(/women/);
  await page.getByRole("button", { name: "View 2: Gallery" }).click();
  await page.screenshot({ path: "test-results/catalogue-mobile.png" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    results.violations.filter((v) =>
      ["serious", "critical"].includes(v.impact || ""),
    ),
  ).toEqual([]);
});

test("owner can open product editor and campaign history", async ({ page }) => {
  await page.goto("/account");
  await page.getByText("Development accounts", { exact: true }).click();
  await page
    .getByRole("button", { name: "CONTINUE AS OWNER", exact: true })
    .click();
  await page.getByRole("link", { name: "OPEN BOUTIQUE ADMIN" }).click();
  await expect(
    page.getByRole("heading", { name: "Overview", exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/admin-overview.png" });
  await page.getByRole("link", { name: "PRODUCTS & INVENTORY" }).click();
  await page.getByRole("link", { name: "EDIT →" }).first().click();
  await expect(
    page.getByRole("heading", { name: "Edit product" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "CAMPAIGNS", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Revision history" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "OPEN SAVED DRAFT PREVIEW" }).click();
  await expect(
    page
      .frameLocator(".campaign-preview")
      .getByText("SAVED DRAFT / NOT PUBLISHED"),
  ).toBeVisible();
  await expect(
    page
      .frameLocator(".campaign-preview")
      .locator(".campaign-block.video video"),
  ).toHaveCount(1);
});
