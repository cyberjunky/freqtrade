import { test, expect } from '@playwright/test';

import { setLoginInfo, defaultMocks, tradeMocks } from './helpers';

test.describe('Bot page', () => {
  test.beforeEach(async ({ page }) => {
    await defaultMocks(page);
    await setLoginInfo(page);

    await tradeMocks(page);
  });
  test('Bot page sections and controls', async ({ page }) => {
    await Promise.all([
      // legacy path - forwards to the bot summary
      page.goto('/trade'),
      page.waitForResponse('**/status'),
      page.waitForResponse('**/profit'),
      page.waitForResponse('**/balance'),
      page.waitForResponse('**/whitelist'),
      page.waitForResponse('**/blacklist'),
      page.waitForResponse('**/locks'),
    ]);
    await expect(page).toHaveURL(/\/bot\/ftbot\.0\/summary/);
    const panel = (title: string) => page.locator('.ft-panel-title', { hasText: title });
    const section = (name: string) =>
      page.getByRole('tablist', { name: 'Bot sections' }).getByRole('tab', { name });

    // Header: name, state and mode as text
    await expect(page.getByRole('heading', { name: 'TestBot' })).toBeInViewport();
    await expect(page.locator('.ft-bothead')).toContainText('Running');
    await expect(page.locator('.ft-bothead')).toContainText('DRY-RUN');

    // Summary
    await expect(panel('Cumulative profit')).toBeInViewport();
    await expect(panel('Open trades')).toBeVisible();

    // Chart section shows the pairs of the whitelist
    await section('Chart').click();
    await expect(page.getByRole('listitem', { name: 'BTC/USDT' })).toBeInViewport();
    await expect(page.getByRole('listitem', { name: 'ETH/USDT' })).toBeInViewport();

    // Performance
    await Promise.all([page.waitForResponse('**/performance'), section('Performance').click()]);
    // Per-pair table comes first; entry tags / exit reasons tables share the column.
    await expect(page.locator('th:has-text("Profit USDT")').first()).toBeInViewport();
    const performancePair = page.locator('td:has-text("XRP/USDT")');
    await expect(performancePair).toBeInViewport();

    // Confirmation before stopping the bot
    const dialogModal = page.getByRole('dialog');
    const modalCancelButton = dialogModal.getByRole('button', { name: 'Cancel' });

    await expect(dialogModal).not.toBeVisible();
    await expect(modalCancelButton).not.toBeVisible();

    await page.getByRole('button', { name: 'Stop', exact: true }).click();

    await expect(dialogModal).toBeVisible();
    await expect(dialogModal).toBeInViewport();
    await expect(dialogModal.getByRole('button', { name: 'Stop bot' })).toBeVisible();
    await expect(modalCancelButton).toBeInViewport();
    await modalCancelButton.click();
    await expect(modalCancelButton).not.toBeVisible();

    // Trades section
    await section('Trades').click();
    await expect(performancePair).not.toBeInViewport();
    await expect(panel('Closed trades')).toBeInViewport();
    await expect(page.getByRole('cell', { name: 'TRX/USDT' })).toBeInViewport();
    // Amounts follow the system number format ("8070.5" or "8070,5").
    await expect(page.getByRole('cell', { name: /^8070[.,]5$/ })).toBeInViewport();

    // Search closed trades
    await page.getByRole('textbox', { name: 'Search trades' }).fill('TRX');
    await expect(page.getByRole('cell', { name: 'TRX/USDT' })).toBeInViewport();
    await expect(page.locator('.trade-history td:has-text("BTC/USDT")')).toHaveCount(0);
    await page.getByRole('textbox', { name: 'Search trades' }).fill('');

    // Trade detail opens on row click
    await page.getByRole('cell', { name: 'TRX/USDT' }).click();
    await expect(page.locator('.ft-panel-title', { hasText: 'Trade #' })).toBeVisible();

    // Reload config asks for confirmation, then reports the result
    await page.getByRole('button', { name: 'Reload config' }).click();
    await expect(dialogModal).toBeVisible();
    await expect(dialogModal).toBeInViewport();

    const modalOkButton = dialogModal.getByRole('button', { name: 'Reload config' });
    await expect(modalOkButton).toBeVisible();
    await modalOkButton.click();

    await expect(page.getByText('Config reloaded successfully.')).toBeInViewport();
  });

  test('Bot section - status, pairlist and log', async ({ page }) => {
    await page.goto('/pairlist');
    await expect(page).toHaveURL(/\/bot\/ftbot\.0\/bot/);
    const panel = (title: string) => page.locator('.ft-panel-title', { hasText: title });
    await expect(panel('Status and config')).toBeVisible();
    await expect(panel('Trading rules')).toBeVisible();
    await expect(panel('Pair locks')).toBeVisible();
    await expect(panel('Pairlist')).toBeVisible();
    await expect(page.getByRole('listitem', { name: 'BTC/USDT' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add pair' })).toBeVisible();
  });

  test('Legacy paths forward to bot sections', async ({ page }) => {
    await page.goto('/balance');
    await expect(page).toHaveURL(/\/bot\/ftbot\.0\/balance/);
    await page.goto('/trade_history');
    await expect(page).toHaveURL(/\/bot\/ftbot\.0\/trades/);
    await page.goto('/open_trades');
    await expect(page).toHaveURL(/\/bot\/ftbot\.0\/summary/);
  });
});
