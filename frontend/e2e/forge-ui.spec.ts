import { test, expect } from '@playwright/test';

test('Forge UI cyberpunk styling @vrt', async ({ page }) => {
  await page.goto('/static/forge/');
  await expect(page).toHaveScreenshot('forge-ui-idle.png');
});
