import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Audit', () => {
  
  test('La page d\'accueil doit être accessible', async ({ page }) => {
    await page.goto('/');
    
    // Scan d'accessibilité
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('La page Akinetix doit être accessible', async ({ page }) => {
    await page.goto('/akinetix/');
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

});
