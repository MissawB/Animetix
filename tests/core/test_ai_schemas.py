import pytest
from core.domain.entities.ai_schemas import GraphEntity, GraphExtraction, GraphRelation
from pydantic import ValidationError


def test_graph_entity_validation():
    entity = GraphEntity(
        name="Naruto Uzumaki", type="Personnage", description="Ninja de Konoha"
    )
    assert entity.name == "Naruto Uzumaki"
    assert entity.type == "Personnage"
    assert entity.description == "Ninja de Konoha"


def test_graph_relation_validation():
    relation = GraphRelation(
        source="Naruto",
        target="Sasuke",
        relation="RIVAL_DE",
        description="Rivalité historique",
    )
    assert relation.source == "Naruto"
    assert relation.target == "Sasuke"
    assert relation.relation == "RIVAL_DE"
    assert relation.description == "Rivalité historique"


def test_graph_extraction_validation():
    extraction = GraphExtraction(
        entities=[GraphEntity(name="Naruto", type="Personnage", description="Héros")],
        relations=[
            GraphRelation(
                source="Naruto",
                target="Sasuke",
                relation="RIVAL_DE",
                description="Rivalité",
            )
        ],
    )
    assert len(extraction.entities) == 1
    assert len(extraction.relations) == 1
    assert extraction.entities[0].name == "Naruto"
    assert extraction.relations[0].relation == "RIVAL_DE"


def test_graph_extraction_empty_default():
    extraction = GraphExtraction()
    assert extraction.entities == []
    assert extraction.relations == []


def test_graph_entity_missing_fields():
    with pytest.raises(ValidationError):
        GraphEntity(name="Only Name")  # Missing type


def test_graph_relation_missing_fields():
    with pytest.raises(ValidationError):
        GraphRelation(source="Only Source")  # Missing target and relation
