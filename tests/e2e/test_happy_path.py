import pytest
import re
from playwright.sync_api import Page, expect
from animetix.models import MediaItem


@pytest.mark.django_db(transaction=True)
def test_happy_path(page: Page, live_server):
    """
    Test End-to-End : Connexion -> Choix du mode -> Guess -> Victoire.
    """
    # 0. Initialisation des données de test
    MediaItem.objects.create(
        external_id="456",
        media_type="Anime",
        title="Naruto",
        description="Naruto Uzumaki is a young ninja who seeks recognition from his peers and dreams of becoming the Hokage.",
        release_year=2002,
        metadata={"origin": "Japan"},
    )

    # 1. Accès à l'accueil
    page.goto(live_server.url)
    expect(page).to_have_title(re.compile("Animetix"))

    # 2. Choix d'un mode de jeu (ex: Classic) via navigation directe
    page.goto(f"{live_server.url}/game/classic/")

    # 3. Faire une devinette
    # Attendre que la page de jeu soit chargée
    expect(page).to_have_url(re.compile(r".*/game/"))

    # Wait for the input field to be ready
    page.wait_for_selector("form input")
    page.fill("form input", "Naruto")
    page.press("form input", "Enter")

    # 4. Vérifier le feedback de victoire
    expect(page.locator("text=VICTOIRE")).to_be_visible()
    expect(page.locator("text=Naruto").first).to_be_visible()
