from core.domain.entities.ai_schemas import (
    CombatCharacter,
    CombatResult,
    CombatStats,
    DebateTurn,
)


def test_combat_stats_instantiation():
    stats = CombatStats(
        tier="9-B",
        speed="Superhuman",
        durability="Wall level",
        intelligence="Gifted",
        abilities=["Martial Arts", "Weaponry"],
    )
    assert stats.tier == "9-B"
    assert "Martial Arts" in stats.abilities


def test_combat_character_instantiation():
    stats = CombatStats(
        tier="9-B",
        speed="Superhuman",
        durability="Wall level",
        intelligence="Gifted",
        abilities=["Martial Arts"],
    )
    character = CombatCharacter(
        name="John Wick",
        wiki_url="https://vsbattles.fandom.com/wiki/John_Wick",
        stats=stats,
        summary="A legendary hitman.",
    )
    assert character.name == "John Wick"
    assert character.stats.tier == "9-B"


def test_debate_turn_instantiation():
    turn = DebateTurn(agent="Advocate_A", content="Character A wins because of speed.")
    assert turn.agent == "Advocate_A"
    assert "speed" in turn.content


def test_combat_result_instantiation():
    stats_a = CombatStats(
        tier="10-A",
        speed="Normal",
        durability="Normal",
        intelligence="Average",
        abilities=[],
    )
    char_a = CombatCharacter(
        name="A", wiki_url="url_a", stats=stats_a, summary="summary_a"
    )

    stats_b = CombatStats(
        tier="10-A",
        speed="Normal",
        durability="Normal",
        intelligence="Average",
        abilities=[],
    )
    char_b = CombatCharacter(
        name="B", wiki_url="url_b", stats=stats_b, summary="summary_b"
    )

    turn = DebateTurn(agent="Judge", content="A wins.")

    result = CombatResult(
        character_a=char_a,
        character_b=char_b,
        debate_history=[turn],
        winner="A",
        verdict_summary="A is better.",
    )
    assert result.winner == "A"
    assert len(result.debate_history) == 1
