import { defineConfig, devices } from '@playwright/test'

const backendPort = Number(process.env.STORYWORKS_E2E_BACKEND_PORT || 8011)
const frontendPort = Number(process.env.STORYWORKS_E2E_FRONTEND_PORT || 3010)
const backendUrl = `http://127.0.0.1:${backendPort}`
const frontendUrl = `http://127.0.0.1:${frontendPort}`
const e2eDatabasePath = 'apps/frontend/.e2e/storyworks-e2e.db'
const e2eConfigPath = 'apps/frontend/.e2e/config.json'

export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  expect: {
    timeout: 12_000,
  },
  fullyParallel: false,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: frontendUrl,
    acceptDownloads: true,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `cd ../.. && python -m uvicorn apps.backend.app.main:app --host 127.0.0.1 --port ${backendPort}`,
      url: `${backendUrl}/api/projects`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        STORYWORKS_CONFIG_PATH: e2eConfigPath,
        STORYWORKS_AI_PROVIDER: 'mock',
        STORYWORKS_DB_PATH: e2eDatabasePath,
        STORYWORKS_RESET_DB_ON_START: '1',
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      url: frontendUrl,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        STORYWORKS_API_TARGET: backendUrl,
      },
    },
  ],
})
