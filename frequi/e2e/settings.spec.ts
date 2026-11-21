import { test, expect } from '@playwright/test';
import { setLoginInfo, defaultMocks } from './helpers';

test.describe('Settings', () => {
  test('Settings stores', async ({ page }) => {
    await setLoginInfo(page);
    await defaultMocks(page);
    await Promise.all([
      page.goto('/'),
      // page.waitForResponse('**/Ping'),
      // page.waitForResponse('**/ShowConf'),
    ]);
    // await expect(page.locator('li', { hasText: 'Online' })).toBeInViewport();
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeInViewport({
      timeout: 5000,
    });
    // Settings is reachable through the Tools menu
    await page.getByRole('button', { name: 'Tools' }).click();
    await page.getByRole('menuitem', { name: 'Settings' }).click();

    await expect(page.getByText('FreqUI Settings')).toBeVisible();
    await expect(page.url()).toBe('http://localhost:3000/settings');

    // Switch option in the settings.
    await page.getByRole('combobox', { name: 'Show pill in icon' }).click();
    await page.getByRole('option', { name: 'Show in title' }).click();

    const settings = await page.evaluate(() =>
      JSON.parse(window.localStorage.getItem('ftUISettings') || '{}'),
    );
    await expect(settings['openTradesInTitle']).toBe('asTitle');

    // Theme: auto / light / dark, persisted
    await page.getByRole('tablist', { name: 'Theme' }).getByRole('tab', { name: 'Light' }).click();
    await expect(page.locator('html')).toHaveClass(/ft-light-theme/);
    await page.getByRole('tablist', { name: 'Theme' }).getByRole('tab', { name: 'Dark' }).click();
    await expect(page.locator('html')).toHaveClass(/ft-dark-theme/);
    const settings2 = await page.evaluate(() =>
      JSON.parse(window.localStorage.getItem('ftUISettings') || '{}'),
    );
    await expect(settings2['themeMode']).toBe('dark');
  });
});
