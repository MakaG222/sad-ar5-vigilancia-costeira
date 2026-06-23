import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:8080",
    headless: true,
  },
  webServer: process.env.CI
    ? undefined
    : {
        command: "cd ../api && python -m uvicorn main:app --host 127.0.0.1 --port 8080",
        url: "http://127.0.0.1:8080/api/health",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
