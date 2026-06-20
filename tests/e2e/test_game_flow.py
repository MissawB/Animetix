import re

import pytest
from playwright.sync_api import Page, expect

# Browser-driven E2E: needs a Playwright browser and a live server (absent from the unit job).
pytestmark = pytest.mark.integration


def test_home_page_loads(page: Page, live_server):
    """Vérifie que la page d'accueil charge bien."""
    page.goto(f"{live_server.url}/")
    expect(page).to_have_title(re.compile("Animetix"))


def test_start_game_flow(page: Page, live_server):
    """Vérifie le flux de lancement d'une partie classique."""
    # Navigation directe car le lien sur la page d'accueil est un formulaire HTMX complexe
    page.goto(f"{live_server.url}/game/start/")

    # Attendre que la page de jeu charge (SPA fallback)
    expect(page).to_have_url(re.compile(r".*/game/"))
    # The SPA has 'root' div
    expect(page.locator("#root")).to_be_visible()
