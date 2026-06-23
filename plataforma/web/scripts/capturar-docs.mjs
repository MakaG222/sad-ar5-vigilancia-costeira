/**
 * Gera capturas para plataforma/docs/ (README GitHub).
 * Uso: cd plataforma/web && node scripts/capturar-docs.mjs
 * Requer API em http://127.0.0.1:8080 (uvicorn ou Docker).
 */
import { chromium } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs");
const BASE = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:8080";

async function waitReady(page) {
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: /SAD AR5/i }).waitFor({ timeout: 60_000 });
  await page.waitForTimeout(2500);
}

async function shot(page, name) {
  const file = path.join(OUT, name);
  await page.screenshot({ path: file, fullPage: false });
  console.log("  ->", file);
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });

  console.log("Capturas SAD AR5 →", OUT);
  await waitReady(page);
  await shot(page, "screenshot.png");

  await page.getByRole("button", { name: /Modo completo/i }).click();
  await page.waitForTimeout(1500);
  await shot(page, "mapa-risco.png");

  await page.getByRole("button", { name: "Operação" }).click();
  await page.waitForTimeout(500);

  const modoRota = page.locator('select:has(option[value="plano24h"])');
  await modoRota.selectOption("plano24h");
  await page.getByRole("button", { name: /Calcular rota/i }).click();
  await page.waitForTimeout(3000);
  await shot(page, "plano-24h.png");

  await page.getByRole("button", { name: "Mais" }).click();
  await page.waitForTimeout(800);
  await shot(page, "alertas.png");

  await page.getByRole("button", { name: "Ciência" }).click();
  await page.getByText(/Baseline patrulha/i).waitFor({ timeout: 30_000 });
  await page.waitForTimeout(500);
  await shot(page, "validacao-ciencia.png");

  await page.getByRole("button", { name: "Operação" }).click();
  await page.locator(".sidebar").evaluate((el) => { el.scrollTop = 0; });
  await page.waitForTimeout(800);
  await shot(page, "dimensionamento-frota.png");

  await browser.close();
  console.log("Concluído.");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
