# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService


def test_tot_returns_full_tree_structure():
    """Vérifie que le service ToT retourne maintenant une structure d'arbre complète."""
    mock_engine = MagicMock()
    # Simuler un score de 0.8
    mock_engine.generate.return_value = "0.8"

    service = TreeOfThoughtsSearchService(
        inference_engine=mock_engine, prompt_manager=MagicMock()
    )
    result = service.solve_with_tree_of_thoughts(query="Test query", breadth=1, depth=1)

    assert "full_tree" in result, "Le résultat ToT doit inclure la clé 'full_tree'"
    assert (
        "nodes" in result["full_tree"]
    ), "L'arbre complet doit contenir une liste de nœuds"
    assert (
        "links" in result["full_tree"]
    ), "L'arbre complet doit contenir une liste de liens"

    # Vérification du nœud racine
    nodes = result["full_tree"]["nodes"]
    assert len(nodes) >= 1
    root = nodes[0]
    assert root["id"] == "node_0_0"
    assert root["status"] == "root"
    assert root["label"] == "Start"


def test_tot_captures_generated_nodes():
    """Vérifie que les pensées générées sont ajoutées comme nœuds et liées correctement."""
    from unittest.mock import MagicMock  # noqa: E402

    from core.domain.services.tree_of_thoughts_service import (  # noqa: E402
        TreeOfThoughtsSearchService,
    )

    mock_engine = MagicMock()
    # Scénario : 1 étape, 2 branches
    # 1. Thought 1 (branch 0)
    # 2. Score 0.9 (branch 0)
    # 3. Thought 2 (branch 1)
    # 4. Score 0.3 (branch 1) -> pruned
    # 5. Synthesis
    mock_engine.generate.side_effect = [
        "Thought 1",
        "0.9",
        "Thought 2",
        "0.3",
        "Final synthesis",
    ]

    service = TreeOfThoughtsSearchService(
        inference_engine=mock_engine, prompt_manager=MagicMock()
    )
    result = service.solve_with_tree_of_thoughts(query="Test", breadth=2, depth=1)

    nodes = result["full_tree"]["nodes"]
    links = result["full_tree"]["links"]

    # On attend 4 nœuds : Start, Thought 1, Thought 2, CONCLUSION
    assert len(nodes) == 4
    assert any(n["id"] == "node_1_0_0" and n["full_text"] == "Thought 1" for n in nodes)
    assert any(n["id"] == "node_1_0_1" and n["full_text"] == "Thought 2" for n in nodes)
    assert any(n["id"] == "node_final" and n["status"] == "final" for n in nodes)

    # On attend 3 liens : 2 depuis node_0_0, 1 vers node_final
    assert len(links) == 3
    assert any(
        _l["source"] == "node_0_0" and _l["target"] == "node_1_0_0" for _l in links
    )
    assert any(
        _l["source"] == "node_0_0" and _l["target"] == "node_1_0_1" for _l in links
    )
