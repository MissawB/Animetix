import pytest
import re
from playwright.sync_api import Page, expect

@pytest.mark.django_db
def test_happy_path(page: Page, live_server):
    """
    Test End-to-End : Connexion -> Choix du mode -> Guess -> Victoire.
    """
    # 1. Accès à l'accueil
    page.goto(live_server.url)
    expect(page).to_have_title(re.compile("Animetix"))

    # 2. Choix d'un mode de jeu (ex: Classic)
    # On force le clic car les animations "animate-float" rendent l'élément instable pour Playwright
    page.click("text=CLASSIC", force=True)
    
    # 3. Faire une devinette
    # Attendre que la page de jeu soit chargée
    expect(page).to_have_url(re.compile(r".*/game/"))
    page.wait_for_selector("input[name='guess']")
    page.fill("input[name='guess']", "Naruto")
    page.press("input[name='guess']", "Enter")
    
    # 4. Vérifier le feedback (score affiché)
    # Le swap HTMX doit se produire
    expect(page.locator(".guess-row").first).to_be_visible()
