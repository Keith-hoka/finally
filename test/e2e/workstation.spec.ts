import { expect, type Page, test } from "@playwright/test";

const DEFAULT_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"];

const watchlistRow = (page: Page, ticker: string) =>
  page.locator("section", { has: page.getByRole("heading", { name: "Watchlist" }) })
    .locator("div", { hasText: new RegExp(`^${ticker}`) })
    .first();

test.describe.configure({ mode: "serial" });

test("fresh start: default watchlist, balance, and streaming prices", async ({ page }) => {
  await page.goto("/");

  for (const ticker of DEFAULT_TICKERS) {
    await expect(page.getByText(ticker, { exact: true }).first()).toBeVisible();
  }
  await expect(page.getByText("CASH")).toBeVisible();

  // Prices stream in within a couple of ticks
  await expect(watchlistRow(page, "AAPL").getByText(/\d+\.\d\d/).first()).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByText("LIVE")).toBeVisible();
});

test("watchlist: add and remove a ticker", async ({ page }) => {
  await page.goto("/");

  await page.getByPlaceholder("ADD TICKER").fill("PYPL");
  await page.getByRole("button", { name: "+" }).click();
  await expect(page.getByText("PYPL", { exact: true })).toBeVisible();

  await watchlistRow(page, "PYPL").hover();
  await watchlistRow(page, "PYPL").getByRole("button", { name: "×" }).click();
  await expect(page.getByText("PYPL", { exact: true })).not.toBeVisible();
});

test("trading: buy then sell updates cash and positions", async ({ page }) => {
  await page.goto("/");
  await expect(watchlistRow(page, "AAPL").getByText(/\d+\.\d\d/).first()).toBeVisible({
    timeout: 10_000,
  });

  await page.getByRole("textbox", { name: "Quantity" }).fill("5");
  await page.getByRole("button", { name: "BUY" }).click();
  await expect(page.getByText(/BUY 5 AAPL @/)).toBeVisible();

  // Position row appears, heatmap cell renders
  await expect(page.getByRole("cell", { name: "AAPL" })).toBeVisible();
  await expect(page.locator('[title^="AAPL:"]')).toBeVisible();

  await page.getByRole("textbox", { name: "Quantity" }).fill("5");
  await page.getByRole("button", { name: "SELL" }).click();
  await expect(page.getByText(/SELL 5 AAPL @/)).toBeVisible();
  await expect(page.getByText("NO OPEN POSITIONS")).toBeVisible();
});

test("trade validation: insufficient cash is rejected with a message", async ({ page }) => {
  await page.goto("/");
  await expect(watchlistRow(page, "AAPL").getByText(/\d+\.\d\d/).first()).toBeVisible({
    timeout: 10_000,
  });

  await page.getByRole("textbox", { name: "Quantity" }).fill("99999");
  await page.getByRole("button", { name: "BUY" }).click();
  await expect(page.getByText(/Insufficient cash/)).toBeVisible();
});

test("AI chat (mock): response and trade execution appear inline", async ({ page }) => {
  await page.goto("/");
  await expect(watchlistRow(page, "AAPL").getByText(/\d+\.\d\d/).first()).toBeVisible({
    timeout: 10_000,
  });

  await page.getByPlaceholder("Message FinAlly…").fill("please buy a share");
  await page.getByRole("button", { name: "SEND" }).click();

  await expect(page.getByText("Mock: buying 1 share of AAPL.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText(/EXECUTED: BUY 1 AAPL @/)).toBeVisible();
});

test("P&L chart renders data after trades", async ({ page }) => {
  await page.goto("/");
  const pnlPanel = page.locator("section", {
    has: page.getByRole("heading", { name: "P&L — Total Value" }),
  });
  // Snapshots exist from the trades above; the chart canvas should be drawn
  await expect(pnlPanel.locator("canvas").first()).toBeVisible();
  await expect(page.getByText("AWAITING SNAPSHOTS")).not.toBeVisible();
});

test("SSE resilience: recovers once the stream becomes reachable", async ({ page }) => {
  // Note: network-level offline emulation cannot sever an already-established
  // localhost SSE connection, so we block the endpoint itself instead.
  let blocked = true;
  await page.route("**/api/stream/prices", (route) =>
    blocked ? route.abort() : route.continue(),
  );

  await page.goto("/");
  await expect(page.getByText(/RECONNECTING|OFFLINE/)).toBeVisible({ timeout: 10_000 });

  blocked = false;
  await expect(page.getByText("LIVE")).toBeVisible({ timeout: 15_000 });
});
