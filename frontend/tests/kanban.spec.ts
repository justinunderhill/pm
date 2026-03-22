import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

const defaultBoard = {
  version: 1,
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    {
      id: "col-progress",
      title: "In Progress",
      cardIds: ["card-4", "card-5"],
    },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
};

const resetBoard = async (page: Page) => {
  await page.evaluate(async (board) => {
    const response = await fetch("/api/board", {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(board),
    });
    if (!response.ok) {
      throw new Error(`Board reset failed with status ${response.status}`);
    }
  }, defaultBoard);
};

const signIn = async (page: Page, options?: { resetBoard?: boolean }) => {
  const resetBoardState = options?.resetBoard ?? true;

  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /^sign in$/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();

  if (resetBoardState) {
    await resetBoard(page);
    await page.reload();
    await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  }
};

const waitForBoardSave = (page: Page) =>
  page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/board") &&
      response.request().method() === "PUT" &&
      response.status() === 200
  );

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const saveResponse = waitForBoardSave(page);
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await saveResponse;
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  const saveResponse = waitForBoardSave(page);
  await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(columnBox.x + columnBox.width / 2, columnBox.y + 120, {
    steps: 12,
  });
  await page.mouse.up();
  await saveResponse;
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("edits a card and persists after refresh", async ({ page }) => {
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  await card.getByRole("button", { name: /edit align roadmap themes/i }).click();
  await card.getByLabel("Card title").fill("Roadmap alignment updated");
  await card.getByLabel("Card details").fill("Edited in e2e and should persist.");
  const saveResponse = waitForBoardSave(page);
  await card.getByRole("button", { name: /save/i }).click();
  await saveResponse;

  await expect(card.getByText("Roadmap alignment updated")).toBeVisible();
  await page.reload();
  await expect(
    page.getByTestId("card-card-1").getByText("Roadmap alignment updated")
  ).toBeVisible();
});

test("deletes a card and persists after refresh", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const targetCard = firstColumn.getByTestId("card-card-2");
  await expect(targetCard).toBeVisible();
  const saveResponse = waitForBoardSave(page);
  await targetCard
    .getByRole("button", { name: /delete gather customer signals/i })
    .evaluate((button) => (button as HTMLButtonElement).click());
  await expect(firstColumn.getByTestId("card-card-2")).toHaveCount(0);
  await saveResponse;

  await page.reload();
  await expect(page.locator('[data-testid="card-card-2"]')).toHaveCount(0);
});

test("rejects invalid credentials and supports logout", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /^sign in$/i }).click();
  await expect(page.getByText(/invalid credentials/i)).toBeVisible();

  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /^sign in$/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
});

test("persists board changes across logout and login", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const saveResponse = waitForBoardSave(page);
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Persisted logout card");
  await firstColumn.getByPlaceholder("Details").fill("Should survive relogin.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await saveResponse;
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();

  await signIn(page, { resetBoard: false });
  await expect(page.getByText("Persisted logout card")).toBeVisible();
});

test("sends AI message and refreshes board when AI returns updates", async ({
  page,
}) => {
  await page.route("**/api/ai/history", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ messages: [] }),
    });
  });

  await page.route("**/api/ai/chat", async (route) => {
    const updatedBoard = JSON.parse(JSON.stringify(defaultBoard));
    updatedBoard.columns[0].title = "AI Prioritized";

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistantMessage: "Done. I prioritized the first column.",
        boardUpdated: true,
        board: updatedBoard,
      }),
    });
  });

  await signIn(page);
  await page.getByLabel("Message AI").fill("Prioritize this board.");
  await page.getByRole("button", { name: /^send$/i }).click();

  await expect(
    page.getByText("Done. I prioritized the first column.")
  ).toBeVisible();
  await expect(page.getByLabel("Column title").first()).toHaveValue("AI Prioritized");
});
