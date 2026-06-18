from unittest.mock import MagicMock
from core.domain.services.graph_construction_service import (
    KnowledgeGraphConstructionService,
)
from core.domain.entities.ai_schemas import GraphExtraction, GraphEntity, GraphRelation


def test_graph_extraction_instructor():
    """
    Vérifie que le service de construction de graphe utilise correctement l'InferencePort
    pour extraire des données structurées via le mécanisme (instructor).
    """
    # 1. Setup mocks
    mock_inference = MagicMock()
    mock_prompt_manager = MagicMock()

    # Mock du prompt manager
    mock_prompt_manager.get_prompt.return_value = (
        "Extract info from Naruto",
        "You are a graph expert.",
    )

    # Initialisation du service avec les mocks
    service = KnowledgeGraphConstructionService(
        inference_engine=mock_inference, prompt_manager=mock_prompt_manager
    )

    # 2. Définition de la réponse structurée attendue (simulant Instructor)
    expected_extraction = GraphExtraction(
        entities=[
            GraphEntity(
                name="Naruto Uzumaki",
                type="Personnage",
                description="Protagoniste et ninja de Konoha",
            ),
            GraphEntity(
                name="Konoha", type="Lieu", description="Le village caché des feuilles"
            ),
        ],
        relations=[
            GraphRelation(
                source="Naruto Uzumaki",
                target="Konoha",
                relation="HABITE_A",
                description="Naruto réside dans le village",
            )
        ],
    )

    mock_inference.generate_structured.return_value = expected_extraction

    # 3. Exécution de l'extraction
    result = service.extract_entities_and_relations(
        title="Naruto",
        description="Naruto est un jeune ninja qui vit à Konoha et rêve de devenir Hokage.",
        media_type="Anime",
    )

    # 4. Vérifications
    assert isinstance(result, dict)
    assert "entities" in result
    assert "relations" in result
    assert len(result["entities"]) == 2
    assert result["entities"][0]["name"] == "Naruto Uzumaki"
    assert result["entities"][1]["name"] == "Konoha"
    assert len(result["relations"]) == 1
    assert result["relations"][0]["source"] == "Naruto Uzumaki"
    assert result["relations"][0]["target"] == "Konoha"
    assert result["relations"][0]["relation"] == "HABITE_A"

    # Vérifier que l'inference engine a été appelé avec le bon modèle pydantic
    mock_inference.generate_structured.assert_called_once()
    _, kwargs = mock_inference.generate_structured.call_args
    assert kwargs["response_model"] == GraphExtraction
    assert kwargs["prompt"] == "Extract info from Naruto"
    assert kwargs["system_prompt"] == "You are a graph expert."
