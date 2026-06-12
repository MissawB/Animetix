# Design Spec - Multi-Turn Dialogues for Animetix SFT Dataset

This spec outlines the design for incorporating 15-20% multi-turn dialogue scenarios into the SFT training dataset of Animetix, ensuring the expert model can sustain context across consecutive turns in both French and English.

## 1. Objectives & Requirements
* **Context Preservation**: Teach the model to follow conversation context (referencing previous turns) across multiple consecutive exchanges.
* **Proportion Target**: Integrate multi-turn dialogue scenarios representing ~15-20% of the total dataset.
* **Bilingual Parity**: Ensure a balanced representation of French and English multi-turn conversations.
* **Compatibility**: Maintain backward compatibility with the existing single-turn formatting.

## 2. Architecture & Data Structures
Multi-turn examples will be represented using a retrocompatible `turns` list inside the JSONL structure.

### Single-Turn Format (Existing)
```json
{
  "instruction": "Qui est Luffy ?",
  "input": "One Piece",
  "output": "Luffy est le protagoniste...",
  "language": "Français"
}
```

### Multi-Turn Format (New)
```json
{
  "turns": [
    {"user": "Salut ! Tu as un bon anime d'action à me conseiller ?", "assistant": "Bonjour ! Oui, je te recommande absolument 'Naruto'..."},
    {"user": "Ah super. Et c'est quel studio qui l'a produit, et en quelle année ?", "assistant": "Cet anime a été produit par le studio Pierrot et est sorti en 2002."},
    {"user": "Génial, merci. Et quelles sont les thématiques principales abordées ?", "assistant": "Dans 'Naruto', on retrouve principalement les thèmes suivants : Combats au sabre, Démons, Orphelin."}
  ],
  "language": "Français"
}
```

## 3. Dynamic Dialogue Generation (Approach 1)
We will implement procedural dialogue generators in `finetuning_dataset.py` drawing from local databases:

1. **Scenario A: Recommendation & Exploration of Anime/Manga**
   * **Turn 1**: Recommendation based on a random genre.
   * **Turn 2**: Asking for studio/author and release year.
   * **Turn 3**: Asking for primary tags.

2. **Scenario B: Character Investigation**
   * **Turn 1**: Who is `{character}`?
   * **Turn 2**: What group or faction are they affiliated with?
   * **Turn 3**: What are their height and global popularity metrics?

3. **Scenario C: Otaku Concept Exploration**
   * **Turn 1**: Define `{concept}` (e.g. Tsundere).
   * **Turn 2**: Give famous examples of characters embodying this concept.
   * **Turn 3**: Explain the origin or writing impact of the concept.

## 4. Integration into Dataset Compiler Loop
* A new function `generate_multiturn_dialogues(...)` will compile these dialogues.
* The `deduplicate_dataset` function will be updated to compute signature keys for multi-turn examples by hashing their text turns.
* Ratios will be maintained so that multi-turn examples comprise ~15-20% of the output JSONL.

## 5. Training Pipeline Updates
We will update `format_chatml_messages` in `train_expert_model.py` to serialize multi-turn turns natively into ChatML format:
* If the item contains `turns`, we iterate and append each turn sequentially as `user` and `assistant` roles after the system prompt.
* Otherwise, we fallback to the single-turn serialization.
