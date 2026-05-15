import pytest
from playwright.sync_api import Page, expect

def test_home_page_loads(page: Page, live_server):
    """Vérifie que la page d'accueil charge bien."""
    page.goto(f"{live_server.url}/")
    expect(page).to_have_title("Animetix")

def test_start_game_flow(page: Page, live_server):
    """Vérifie le flux de lancement d'une partie classique."""
    page.goto(f"{live_server.url}/")

    # Cliquer sur le bouton de lancement (supposé lien "start_game")
    page.click("a[href='/game/start/']")

    # Attendre que la page de jeu charge
    expect(page).to_have_url(f"{live_server.url}/game/")
    expect(page.locator("h1")).to_contain_text("Animetix")

