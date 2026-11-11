import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("bespoke creation, private references, owner review, agreement and handoff", async ({
  page,
  browser,
}) => {
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/bespoke");
  await expect(page.locator(".material-card")).toHaveCount(10);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({
    path: "test-results/bespoke-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "View Mocha garden close-up" })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page
    .getByRole("button", { name: "Select Mocha garden", exact: true })
    .click();
  await page.getByRole("button", { name: "CHOOSE YOUR LACE" }).click();
  await expect(page.locator(".material-card")).toHaveCount(6);
  await page
    .getByRole("button", { name: "Select The scalloped edge", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Select A fine line", exact: true })
    .click();
  await expect(page.locator(".pairing-laces figure")).toHaveCount(2);
  await page
    .getByLabel("Lace placement", { exact: true })
    .fill("Sleeve cuffs and dupatta edge. Leave neckline plain.");
  await page.screenshot({
    path: "test-results/bespoke-lace.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "CREATE YOUR DESIGN" }).click();
  const name = `Studio review ${Date.now()}`;
  await page.getByLabel("Your name", { exact: false }).fill(name);
  await page.getByLabel("Occasion", { exact: true }).fill("Family lunch");
  await page
    .getByLabel("The idea, in your own words", { exact: false })
    .fill("An easy straight kurta with full sleeves and a fine lace edge.");
  await page
    .getByLabel("Silhouette", { exact: false })
    .selectOption("Straight kurta");
  await page.getByLabel("Neckline", { exact: true }).selectOption("Round");
  await page.getByLabel("Sleeves", { exact: true }).selectOption("Full length");
  await page
    .getByLabel("+ ADD PHOTOS", { exact: true })
    .setInputFiles("public/media/bespoke/design-reference-640.webp");
  await expect(page.locator(".reference-grid article")).toHaveCount(1);
  await page.getByRole("button", { name: "+ Add detail", exact: true }).click();
  await page
    .getByLabel("What should masterji know?")
    .fill("Keep this neckline but omit the embroidery.");
  await page.getByRole("button", { name: "ADD DETAIL", exact: true }).click();
  await page.getByRole("button", { name: "SAVE DRAFT", exact: true }).click();
  await expect(
    page.getByText("Draft saved to your MyShoppe session."),
  ).toBeVisible();
  const designURL = page.url();
  await page.reload();
  await expect(page.locator(".master-brief")).toContainText(
    "Keep this neckline",
  );
  await page.getByRole("button", { name: "SEND TO BOUTIQUE" }).click();
  await expect(
    page.getByRole("heading", { name: "With the boutique", exact: true }),
  ).toBeVisible();
  const ownerContext = await browser.newContext();
  const owner = await ownerContext.newPage();
  await owner.goto("/account");
  await owner.getByText("Development accounts", { exact: true }).click();
  await owner
    .getByRole("button", { name: "CONTINUE AS OWNER", exact: true })
    .click();
  await expect(
    owner.getByRole("link", { name: "OPEN BOUTIQUE ADMIN" }),
  ).toBeVisible();
  await owner.goto("/admin/bespoke");
  await owner
    .locator(".bespoke-queue button")
    .filter({ hasText: name })
    .click();
  await owner
    .getByLabel("Confirmed materials, quantity & colour")
    .fill(
      "Mocha fabric sample confirmed. 3 metres; scalloped lace 1 metre; gold trim 2 metres.",
    );
  await owner
    .getByLabel("Confirmed measurements / fitting plan")
    .fill(
      "Measure in cm at the boutique before cutting; relaxed waist fit confirmed.",
    );
  await owner
    .getByLabel("Stitching instructions", { exact: true })
    .fill(
      "Straight kurta. Round neckline, full sleeves. Scalloped cuffs and gold dupatta border. Enclosed seams.",
    );
  await owner.getByRole("button", { name: "SAVE REVIEW FOR CUSTOMER" }).click();
  await expect(
    owner.getByRole("heading", { name: "Review together", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Refresh status" }).click();
  await expect(page.locator(".master-brief")).toContainText("Enclosed seams.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "AGREE TO THIS BRIEF" }).click();
  await expect(
    page.getByRole("heading", { name: "Customer agreed", exact: true }),
  ).toBeVisible();
  await owner
    .getByRole("button", { name: "RELOAD BRIEF", exact: true })
    .click();
  await owner.getByRole("button", { name: "RELEASE TO MASTERJI" }).click();
  await expect(
    owner.getByRole("heading", { name: "Ready for masterji", exact: true }),
  ).toBeVisible();
  await page.goto(designURL);
  await expect(page.locator(".brief-warning")).toContainText(
    "Approved handoff",
  );
  await page.screenshot({
    path: "test-results/bespoke-brief.png",
    fullPage: true,
  });
  await page.emulateMedia({ media: "print" });
  const printReference = page
    .locator(".brief-references .pinned-image")
    .first();
  const printGeometry = await printReference.evaluate((el) => {
    const image = el.querySelector("img")!.getBoundingClientRect();
    const frame = el.getBoundingClientRect();
    return {
      imageWidth: image.width,
      imageHeight: image.height,
      frameWidth: frame.width,
      frameHeight: frame.height,
    };
  });
  expect(printGeometry.imageWidth).toBeCloseTo(printGeometry.imageHeight, 0);
  expect(printGeometry.frameWidth).toBeCloseTo(printGeometry.imageWidth, 0);
  expect(printGeometry.frameHeight).toBeCloseTo(printGeometry.imageHeight, 0);
  await page.screenshot({
    path: "test-results/bespoke-print-layout.png",
    fullPage: true,
  });
  await page.pdf({
    path: "test-results/bespoke-masterji.pdf",
    format: "A4",
    printBackground: true,
  });
  await page.emulateMedia({ media: "screen" });
  await page.getByRole("button", { name: "EDIT DESIGN", exact: true }).click();
  await page.getByLabel("Neckline", { exact: true }).selectOption("V-neck");
  await page.getByRole("button", { name: "SAVE DRAFT", exact: true }).click();
  await expect(
    page.getByText("Draft saved to your MyShoppe session."),
  ).toBeVisible();
  await page.getByRole("button", { name: "REVIEW YOUR BRIEF" }).click();
  await expect(page.locator(".brief-warning")).toContainText("Not released");
  expect(errors).toEqual([]);
  await ownerContext.close();
});

test("mobile material selection, recovery and accessibility", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/bespoke");
  await page
    .getByRole("button", { name: "Select Warm ivory", exact: true })
    .click();
  await page.screenshot({
    path: "test-results/bespoke-mobile.png",
    fullPage: true,
  });
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
  page.once("dialog", (d) => d.accept());
  await page.reload();
  await expect(
    page.getByRole("dialog", { name: "Recover unsaved changes" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "RESTORE CHANGES" }).click();
  await expect(
    page.getByRole("button", { name: "Select Warm ivory", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "CHOOSE YOUR LACE" }).click();
  await page
    .getByRole("button", { name: "Keep it without lace", exact: true })
    .click();
  await page.getByRole("button", { name: "CREATE YOUR DESIGN" }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("studio detail library and private voice note", async () => {
  const { chromium } = await import("@playwright/test");
  const browser = await chromium.launch({
    channel: "chrome",
    args: [
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
    ],
  });
  try {
    const page = await browser.newPage({
      baseURL: "http://localhost:3000",
      permissions: ["microphone"],
    });
    await page.goto("/bespoke");
    await page
      .getByRole("button", { name: "Select Sage bloom", exact: true })
      .click();
    await page.getByRole("button", { name: "CHOOSE YOUR LACE" }).click();
    await page
      .getByRole("button", { name: "Keep it without lace", exact: true })
      .click();
    await page.getByRole("button", { name: "CREATE YOUR DESIGN" }).click();
    await page.getByRole("button", { name: "Use studio reference" }).click();
    const library = page.getByRole("dialog", {
      name: "Studio reference library",
    });
    await expect(
      library.locator(".studio-reference-library button"),
    ).toHaveCount(5);
    await library
      .getByRole("button", { name: "A considered neckline" })
      .click();
    await expect(page.locator(".reference-grid article")).toHaveCount(1);
    await page
      .getByRole("button", { name: "RECORD A VOICE NOTE", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: /STOP · 0:01/ }),
    ).toBeVisible();
    await page.getByRole("button", { name: /STOP ·/ }).click();
    await expect(page.locator(".voice-box audio")).toHaveAttribute(
      "src",
      /\/api\/bespoke-assets\//,
    );
    await page.getByRole("button", { name: "SAVE DRAFT", exact: true }).click();
    await expect(
      page.getByText("Draft saved to your MyShoppe session."),
    ).toBeVisible();
    await page.reload();
    await expect(page.locator(".master-brief")).toContainText(
      "A considered neckline",
    );
    await expect(page.locator(".voice-reference audio")).toHaveAttribute(
      "src",
      /\/api\/bespoke-assets\//,
    );
  } finally {
    await browser.close();
  }
});
