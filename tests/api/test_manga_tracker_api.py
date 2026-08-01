from unittest.mock import MagicMock

import pytest
from animetix.containers import get_container
from animetix.models import MangaTrackerLink, MediaItem, TrackerConnection
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def linked(db):
    client = APIClient()
    user = User.objects.create_user(username="linker", password="pw")
    client.force_authenticate(user=user)
    manga = MediaItem.objects.create(
        external_id="suwayomi:1:809", media_type="Manga", title="One Punch-Man"
    )
    TrackerConnection.objects.create(user=user, tracker="anilist", token="tok")

    adapter = MagicMock()
    adapter.search.return_value = [
        {"remote_id": "30013", "title": "One Punch-Man", "chapters": 200}
    ]
    adapter.read_progress.return_value = 164
    adapter.write_progress.return_value = True
    container = get_container()
    container.persistence.anilist_adapter.override(adapter)
    yield client, user, manga, adapter
    container.persistence.anilist_adapter.reset_last_overriding()


@pytest.fixture
def other_user(db):
    """Second compte authentifié, sans aucune liaison ni connexion tracker."""
    client = APIClient()
    user = User.objects.create_user(username="stranger", password="pw")
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
def test_trackers_endpoint_requires_authentication(api_client):
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"})
    assert api_client.get(url).status_code == 403


@pytest.mark.django_db
def test_get_returns_204_for_a_manga_absent_from_the_catalog(linked):
    client, *_ = linked
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:nope"})
    assert client.get(url).status_code == 204


@pytest.mark.django_db
def test_get_suggests_and_persists_the_link(linked):
    client, user, manga, adapter = linked
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"})

    payload = client.get(url).data

    assert payload["links"][0]["tracker"] == "anilist"
    assert payload["links"][0]["status"] == "suggested"
    assert payload["links"][0]["remote_title"] == "One Punch-Man"
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 1

    # Deuxième appel : la proposition est servie depuis la base, pas re-cherchée.
    adapter.search.reset_mock()
    client.get(url)
    adapter.search.assert_not_called()


@pytest.mark.django_db
def test_link_confirms_and_reads_remote_progress(linked):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    url = reverse("api_manga_trackers_link", kwargs={"media_id": "suwayomi:1:809"})
    res = client.post(
        url,
        {"tracker": "anilist", "remote_id": "30013", "remote_title": "One Punch-Man"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["status"] == "confirmed"
    assert res.data["remote_progress"] == 164
    # Le titre distant est ce qui permet de vérifier d'un coup d'œil qu'on a
    # lié la bonne œuvre : une liaison confirmée sans nom est invérifiable.
    assert res.data["remote_title"] == "One Punch-Man"


@pytest.mark.django_db
def test_link_keeps_the_title_of_a_manually_corrected_candidate(linked):
    """« Chercher autre chose » : le `remote_id` choisi n'est pas celui de la
    proposition, donc aucune liaison en base ne porte son titre. Sans le titre
    transmis par le client, la liaison corrigée s'afficherait sans nom d'œuvre
    — précisément dans le cas où l'utilisateur vient de corriger."""
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    url = reverse("api_manga_trackers_link", kwargs={"media_id": "suwayomi:1:809"})
    res = client.post(
        url,
        {
            "tracker": "anilist",
            "remote_id": "99999",
            "remote_title": "One Punch-Man (Remake)",
        },
        format="json",
    )

    assert res.status_code == 200
    assert res.data["remote_id"] == "99999"
    assert res.data["remote_title"] == "One Punch-Man (Remake)"
    link = MangaTrackerLink.objects.get(user=user, manga=manga, tracker="anilist")
    assert link.remote_title == "One Punch-Man (Remake)"


@pytest.mark.django_db
def test_link_refuses_a_remote_id_longer_than_the_column(linked):
    """Au-delà de la borne de `remote_id`, l'ORM lèverait (500) sur une valeur
    qui ne peut de toute façon désigner aucune œuvre chez le tracker."""
    client, user, manga, _adapter = linked
    url = reverse("api_manga_trackers_link", kwargs={"media_id": "suwayomi:1:809"})

    res = client.post(
        url, {"tracker": "anilist", "remote_id": "9" * 200}, format="json"
    )

    assert res.status_code == 400
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 0


@pytest.mark.django_db
def test_search_returns_candidates(linked):
    client, *_ = linked
    url = reverse("api_manga_trackers_search", kwargs={"media_id": "suwayomi:1:809"})

    res = client.post(url, {"tracker": "anilist", "query": "one punch"}, format="json")

    assert res.status_code == 200
    assert res.data["results"][0]["remote_id"] == "30013"


@pytest.mark.django_db
def test_unlink_removes_the_link(linked):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    url = reverse(
        "api_manga_trackers_unlink",
        kwargs={"media_id": "suwayomi:1:809", "tracker": "anilist"},
    )
    assert client.delete(url).status_code == 200
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 0


@pytest.mark.django_db
def test_profile_links_lists_every_link(linked):
    client, *_ = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    res = client.get(reverse("api_tracker_links"))

    assert res.status_code == 200
    assert res.data[0]["manga_title"] == "One Punch-Man"
    assert res.data[0]["tracker"] == "anilist"


# --- Isolation par utilisateur -----------------------------------------------
#
# Le point le plus grave possible pour une liaison de compte tiers : un
# utilisateur qui verrait, modifierait ou supprimerait la liaison d'un autre.
# Ces trois tests échoueraient si un futur changement retirait le filtre
# `user=` d'une méthode du repository (get_links / upsert_link / delete_link) ;
# c'est leur unique raison d'être — ne pas les affaiblir pour les faire passer.


@pytest.mark.django_db
def test_get_does_not_leak_another_users_link(linked, other_user):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    other_client, _other = other_user
    url = reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"})
    payload = other_client.get(url).data

    # Aucune connexion tracker pour ce second utilisateur : rien à suggérer,
    # et surtout pas la liaison suggérée/persistée du premier utilisateur.
    assert payload["links"] == []
    assert payload["connected"] == []
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 1


@pytest.mark.django_db
def test_link_does_not_overwrite_another_users_link(linked, other_user):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))
    link_url = reverse("api_manga_trackers_link", kwargs={"media_id": "suwayomi:1:809"})
    client.post(link_url, {"tracker": "anilist", "remote_id": "30013"}, format="json")

    other_client, _other = other_user
    res = other_client.post(
        link_url, {"tracker": "anilist", "remote_id": "99999"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["remote_id"] == "99999"

    # La liaison du premier utilisateur n'a pas bougé : même remote_id, même
    # progression distante lue via son propre token.
    original = MangaTrackerLink.objects.get(user=user, manga=manga, tracker="anilist")
    assert original.remote_id == "30013"
    assert original.status == "confirmed"
    assert original.remote_progress == 164
    # Une ligne par utilisateur : pas de collision sur (manga, tracker).
    assert MangaTrackerLink.objects.filter(manga=manga, tracker="anilist").count() == 2


@pytest.mark.django_db
def test_unlink_does_not_delete_another_users_link(linked, other_user):
    client, user, manga, _adapter = linked
    client.get(reverse("api_manga_trackers", kwargs={"media_id": "suwayomi:1:809"}))

    other_client, _other = other_user
    url = reverse(
        "api_manga_trackers_unlink",
        kwargs={"media_id": "suwayomi:1:809", "tracker": "anilist"},
    )
    res = other_client.delete(url)

    # Rien à supprimer pour ce second utilisateur : la vue le dit, et la
    # liaison du premier utilisateur doit rester intacte.
    assert res.status_code == 200
    assert res.data["success"] is False
    assert MangaTrackerLink.objects.filter(user=user, manga=manga).count() == 1
