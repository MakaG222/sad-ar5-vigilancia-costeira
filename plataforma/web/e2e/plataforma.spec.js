import { test, expect } from "@playwright/test";

test("interface arranca com título SAD AR5", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /SAD AR5/i })).toBeVisible({ timeout: 30_000 });
});

test("separador Ciência mostra baseline patrulha", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Ciência" }).click();
  await expect(page.getByText(/Baseline patrulha/i)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(/Ganho SAD vs aleatório/i)).toBeVisible();
});

test("health da API responde", async ({ request }) => {
  const r = await request.get("/api/health");
  expect(r.ok()).toBeTruthy();
  const j = await r.json();
  expect(j.status).toBe("ok");
});
