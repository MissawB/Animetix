from unittest.mock import MagicMock, patch

from scripts.deploy.deploy_brain import main


@patch("subprocess.run")
def test_deploy_brain_calls_gcloud(mock_run):
    # Mock de subprocess.run pour renvoyer des retours réussis
    mock_run.return_value = MagicMock(
        returncode=0, stdout="https://brain-url.run.app\n"
    )

    # Exécute sans crash
    main()

    # Récupère toutes les commandes appelées
    calls = [call[0][0] for call in mock_run.call_args_list]

    # On aplatit les listes de commandes passées pour la vérification
    flat_calls = [" ".join(cmd) for cmd in calls]

    # Vérifie qu'on a appelé gcloud builds submit
    assert any("builds submit" in c for c in flat_calls)

    # Vérifie qu'on a appelé gcloud run deploy
    assert any("run deploy" in c for c in flat_calls)

    # Vérifie qu'on a décrit le service pour obtenir l'URL
    assert any("run services describe" in c for c in flat_calls)

    # Vérifie qu'on a mis à jour le service web
    assert any("run services update" in c for c in flat_calls)
