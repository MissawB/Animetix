import { test, expect } from '@playwright/test';

test.describe('Akinetix Game @e2e', () => {
  
  test('Le jeu se charge et permet de répondre à une question', async ({ page }) => {
    // 1. Intercepter l'appel API pour mocker la réponse (évite de dépendre du backend Python pendant les tests front)
    await page.route('**/api/v1/game/akinetix/state/', async route => {
      const mockState = {
        history: [],
        current_question: 'Est-ce que votre personnage utilise une épée ?',
        game_over: false,
      };
      await route.fulfill({ json: mockState });
    });

    // Mocker la réponse "OUI"
    await page.route('**/api/v1/game/akinetix/answer/', async route => {
      const newState = {
        history: [{ q: 'Est-ce que votre personnage utilise une épée ?', a: 'OUI' }],
        current_question: 'Porte-t-il des vêtements oranges ?',
        game_over: false,
      };
      await route.fulfill({ json: newState });
    });

    // 2. Naviguer vers la page du jeu
    await page.goto('/static/akinetix/play/');

    // 3. Vérifications (Assertions)
    await expect(page.getByRole('heading', { name: /akinetix/i })).toBeVisible();
    await expect(page.getByText('Est-ce que votre personnage utilise une épée ?')).toBeVisible();

    // 4. Action utilisateur
    await page.getByRole('button', { name: 'OUI' }).click();

    // 5. Vérification du nouvel état
    await expect(page.getByText('Porte-t-il des vêtements oranges ?')).toBeVisible();
    await expect(page.locator('span').filter({ hasText: 'OUI' })).toBeVisible();
  });

});
