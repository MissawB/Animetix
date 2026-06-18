import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.diffusers_adapter import DiffusersAdapter
from core.domain.services.creative.visual_novel_service import VisualNovelService
from core.domain.entities.ai_schemas import VNScene


@pytest.fixture
def diffusers_adapter():
    return DiffusersAdapter()


def test_generate_sprite_calls_generate_image_with_correct_prompt(diffusers_adapter):
    """Vérifie que generate_sprite appelle generate_image avec les bons paramètres."""
    with patch.object(
        diffusers_adapter, "generate_image", return_value="data:image/png;base64,fake"
    ) as mock_gen:
        res = diffusers_adapter.generate_sprite("Naruto", style="manga")
        assert res == "data:image/png;base64,fake"
        mock_gen.assert_called_once()
        args, _ = mock_gen.call_args
        assert (
            "full body portrait on pure white background, anime character sheet style"
            in args[0]
        )
        assert "Naruto" in args[0]
        assert "manga" in args[1]


def test_generate_scene_assets():
    """Vérifie que generate_scene_assets coordonne bien la génération du sprite et du fond."""
    mock_llm = MagicMock()
    mock_engine = MagicMock()
    mock_llm.vision_engine = mock_engine

    service = VisualNovelService(llm_service=mock_llm, repository=MagicMock())
    scene = VNScene(
        character="Goku", text="Hello", mood="Happy", bg_prompt="a sunny forest"
    )

    mock_engine.generate_sprite.return_value = "url_sprite"
    mock_engine.generate_image.return_value = "url_bg"

    assets = service.generate_scene_assets(scene, session_seed=42)

    assert assets["sprite_url"] == "url_sprite"
    assert assets["background_url"] == "url_bg"
    mock_engine.generate_sprite.assert_called_once()
    mock_engine.generate_image.assert_called_with("a sunny forest")
