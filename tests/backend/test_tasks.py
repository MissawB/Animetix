from unittest.mock import MagicMock

from animetix.tasks import generate_fusion_image_task, generate_fusion_scenario_task


def test_generate_fusion_scenario_task(mocker):
    # Mock le conteneur et son llm_service
    mock_container = MagicMock()
    mock_llm_service = MagicMock()
    mock_container.agentic.llm_service.return_value = mock_llm_service
    mock_llm_service.generate_fusion_scenario.return_value = {
        "scenario": "A fusion story"
    }

    mocker.patch("animetix.tasks.get_container", return_value=mock_container)

    res = generate_fusion_scenario_task("Anime", "N1", "N2", "Français")
    assert res["scenario"] == "A fusion story"


def test_generate_fusion_image_task(mocker):
    # Patch de la fonction dans le module animetix.tasks où elle est importée
    mocker.patch(
        "animetix.tasks.generate_fusion_image", return_value="http://image.jpg"
    )

    fusion_data = {"scenario": "A fusion story"}
    item1 = {"title": "Naruto"}
    item2 = {"title": "Sasuke"}

    res = generate_fusion_image_task(fusion_data, item1, item2)
    assert res["fusion_image"] == "http://image.jpg"
