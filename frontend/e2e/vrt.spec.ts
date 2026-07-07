import { test, expect } from '@playwright/test';

test.describe('Visual Regression Testing - Design System @vrt', () => {
  
  // On teste les composants de base sur une page neutre ou via Storybook si disponible
  // Pour rester simple et efficace sans lancer Storybook en arrière-plan, 
  // nous allons créer des tests sur les pages clés qui utilisent le Design System.

  test('Page Akinetix - Intégrité Visuelle', async ({ page }) => {
    // Mocker l'état pour avoir un rendu constant (déterminisme visuel)
    await page.route('**/api/v1/game/akinetix/state/', async route => {
      await route.fulfill({ json: {
        history: [{q: 'Question Test', a: 'OUI'}],
        currentQuestion: 'Est-ce un personnage iconique ?',
        gameOver: false,
      }});
    });

    await page.goto('/static/akinetix/');
    
    // Attendre que les polices et images soient chargées
    await page.waitForLoadState('networkidle');

    // Capture d'écran comparée à la référence (baseline)
    // Playwright créera la référence automatiquement lors du premier lancement avec --update-snapshots
    await expect(page).toHaveScreenshot('akinetix-game-page.png', {
        maxDiffPixelRatio: 0.01, // Autorise 1% de différence (anti-aliasing, etc.)
        fullPage: true
    });
  });

  test('Page Vision Quest - Intégrité Visuelle', async ({ page }) => {
    await page.route('**/api/v1/game/vision/state/', async route => {
      await route.fulfill({ json: {
        image_url: 'https://via.placeholder.com/800x600', // Image constante pour le test
        guesses: [{text: 'Guerrier', score: 85}],
        best_score: 85,
        gameOver: false,
      }});
    });

    await page.goto('/static/vision/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('vision-quest-page.png', {
        maxDiffPixelRatio: 0.01,
        fullPage: true
    });
  });

});
