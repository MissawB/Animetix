import pytest
from animetix.tasks import generate_fusion_scenario_task, generate_fusion_image_task
from unittest.mock import MagicMock

def test_generate_fusion_scenario_task(mocker):
    # Patch the class in services.py because it is instantiated in the task
    mock_llm_cls = mocker.patch('animetix.tasks.LangChainService')
    mock_instance = mock_llm_cls.return_value
    mock_instance.generate_scenario_advanced.return_value = {"scenario": "A fusion story"}
    
    res = generate_fusion_scenario_task('Anime', 'N1', 'N2', 'Français')
    assert res['scenario'] == "A fusion story"

def test_generate_fusion_image_task(mocker):
    mock_llm_cls = mocker.patch('animetix.tasks.LangChainService')
    mock_instance = mock_llm_cls.return_value
    mock_instance.generate_fusion_image.return_value = "http://image.jpg"
    
    # Fusion data is now a dict
    fusion_data = {"scenario": "A fusion story"}
    item1 = {'title': 'Naruto'}
    item2 = {'title': 'Sasuke'}
    
    res = generate_fusion_image_task(fusion_data, item1, item2)
    assert res['fusion_image'] == "http://image.jpg"
