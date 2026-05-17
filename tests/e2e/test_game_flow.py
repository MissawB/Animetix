import pytest
import re
from playwright.sync_api import Page, expect

def test_home_page_loads(page: Page, live_server):
    """Vérifie que la page d'accueil charge bien."""
    page.goto(f"{live_server.url}/")
    expect(page).to_have_title("Animetix - Accueil")

def test_start_game_flow(page: Page, live_server):
    """Vérifie le flux de lancement d'une partie classique."""
    # Navigation directe car le lien sur la page d'accueil est un formulaire HTMX complexe
    page.goto(f"{live_server.url}/game/start/")

    # Attendre que la page de jeu charge
    expect(page).to_have_url(re.compile(r".*/game/"))
    expect(page.locator("h1")).to_contain_text("Animetix")

