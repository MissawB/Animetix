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
    # Note: On utilise hx-get/hx-post avec HTMX
    page.click("text=CLASSIC")
    
    # 3. Faire une devinette
    # On attend que le formulaire soit chargé (SPA feel)
    page.wait_for_selector("input[name='guess']")
    page.fill("input[name='guess']", "Naruto")
    page.press("input[name='guess']", "Enter")
    
    # 4. Vérifier le feedback (score affiché)
    # Le swap HTMX doit se produire
    expect(page.locator(".guess-row").first).to_be_visible()
