import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Audit d\'Accessibilité (a11y)', () => {
  // Liste des pages critiques à auditer
  const pagesToTest = [
    '/static/',
    '/static/lab/hub/',
    '/static/explore/',
    '/static/admin/dashboard/',
    '/static/leaderboard/'
  ];

  for (const route of pagesToTest) {
    test(`Vérification WCAG sur la route : ${route}`, async ({ page }) => {
      // Naviguer vers la page
      await page.goto(route);
      
      // Attendre que la page soit complètement chargée (requêtes réseau terminées)
      await page.waitForLoadState('networkidle');
      
      // Lancer l'analyse axe-core
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();
      
      // S'il y a des violations, les afficher dans les logs pour le debug
      if (accessibilityScanResults.violations.length > 0) {
        console.error(`Violations trouvées sur ${route}:`);
        accessibilityScanResults.violations.forEach(v => {
          console.error(`- Règle: ${v.id} | Impact: ${v.impact} | Description: ${v.description}`);
          v.nodes.forEach(node => console.error(`   Cible: ${node.target}`));
        });
      }
      
      // L'attente : aucune violation d'accessibilité ne doit être trouvée
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});
