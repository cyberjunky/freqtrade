import { test, expect } from '@playwright/test';
import { setLoginInfo, defaultMocks, tradeMocks } from './helpers';

test.describe('Overview', () => {
  test.beforeEach(async ({ page }) => {
    await defaultMocks(page);
    await tradeMocks(page);
    await setLoginInfo(page);
  });
  test('Overview page', async ({ page }) => {
    await Promise.all([
      page.goto('/'),
      page.waitForResponse('**/status'),
      page.waitForResponse('**/profit'),
      page.waitForResponse('**/balance'),
      page.waitForResponse('**/whitelist'),
      page.waitForResponse('**/blacklist'),
      page.waitForResponse('**/locks'),
    ]);
    const panel = (title: string) => page.locator('.ft-panel-title', { hasText: title });
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeInViewport();
    // KPI tiles
    for (const label of ['Open trades', 'Open P&L', 'Closed P&L', 'Win rate', 'Balance']) {
      await expect(page.locator('.ft-tile-label', { hasText: label }).first()).toBeVisible();
    }
    await expect(panel('Bots')).toBeInViewport();
    await expect(panel('Profit per day')).toBeVisible();
    await expect(panel('Open trades')).toBeVisible();
    await expect(panel('Cumulative profit')).toBeVisible();
    await expect(panel('Recent activity')).toBeVisible();

    // Bots table: state and mode are shown as text, the row opens the bot
    const row = page.locator('tr.ft-bot-row', { hasText: 'TestBot' });
    await expect(row).toBeVisible();
    await expect(row).toContainText('Running');
    await expect(row).toContainText('DRY-RUN');
    await expect(row).toContainText('NoActionStrategy');

    // Search filters the table
    await page.getByRole('textbox', { name: 'Search bots' }).fill('doesnotexist');
    await expect(row).not.toBeVisible();
    await page.getByRole('textbox', { name: 'Search bots' }).fill('test');
    await expect(row).toBeVisible();

    await row.click();
    await expect(page).toHaveURL(/\/bot\/ftbot\.0/);
    await expect(page.getByRole('heading', { name: 'TestBot' })).toBeVisible();
  });

  test('Legacy /dashboard path redirects to the overview', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
    await expect(page).toHaveURL('http://localhost:3000/');
  });
});
