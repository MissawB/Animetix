import unittest
from unittest.mock import MagicMock
from src.core.domain.services.creative.visual_novel_service import VisualNovelService
from src.core.domain.entities.ai_schemas import VNScript, VNScene

class TestVisualNovelService(unittest.TestCase):
    def setUp(self):
        self.mock_llm_service = MagicMock()
        self.mock_repository = MagicMock()
        self.service = VisualNovelService(self.mock_llm_service, self.mock_repository)

    def test_generate_script_success(self):
        # Setup mock data
        fusion_id = 1
        self.mock_repository.get_creative_fusion.return_value = {
            'title_a': 'Naruto',
            'title_b': 'One Piece',
            'scenario_text': 'A battle between ninjas and pirates.',
            'art_style': 'Anime'
        }
        
        self.mock_llm_service.prompt_manager.get_prompt.return_value = ("prompt", "system")
        
        expected_script = VNScript(
            title="Ninja Pirate Alliance",
            scenes=[
                VNScene(character="Naruto", text="I will be Hokage!", mood="Happy", bg_prompt="Konoha village")
            ]
        )
        self.mock_llm_service.generate_structured.return_value = expected_script

        # Execute
        result = self.service.generate_script(fusion_id)

        # Verify
        self.assertEqual(result, expected_script)
        self.mock_repository.get_creative_fusion.assert_called_once_with(fusion_id)
        self.mock_llm_service.generate_structured.assert_called_once()

    def test_generate_script_fusion_not_found(self):
        # Setup
        self.mock_repository.get_creative_fusion.return_value = None

        # Execute
        result = self.service.generate_script(999)

        # Verify
        self.assertIsNone(result)
        self.mock_llm_service.generate_structured.assert_not_called()

if __name__ == '__main__':
    unittest.main()
