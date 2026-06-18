import os
import json


def migrate_gold_set():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_path = os.path.join(base_dir, "data", "mlops", "gold_dataset.json")

    if not os.path.exists(gold_path):
        print(f"Error: {gold_path} does not exist.")
        return

    with open(gold_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} existing queries.")

    # Specific entities mapping for existing queries to ensure high quality
    entity_mappings = {
        "Hunter x Hunter (2011)": ["Hunter x Hunter", "Gon Freecss", "Ging Freecss"],
        "Attack on Titan": [
            "Attack on Titan",
            "Wit Studio",
            "Shingeki no Kyojin",
            "Linked Horizon",
            "NHK",
        ],
        "Ghost in the Shell": ["Ghost in the Shell", "Motoko Kusanagi", "cyberpunk"],
        "Monster": [
            "Monster",
            "Naoki Urasawa",
            "Kana",
            "Big Comic Original",
            "Shōgakukan",
        ],
        "Naruto": ["Naruto", "Kakashi Hatake", "TV Tokyo"],
        "Death Note": [
            "Death Note",
            "Ryuk",
            "Yann Pichon",
            "Weekly Shōnen Jump",
            "Shūeisha",
        ],
        "One Piece": [
            "One Piece",
            "Eiichiro Oda",
            "Luffy",
            "Stéphane Excoffier",
            "Trafalgar Law",
        ],
        "Berserk": ["Berserk", "Guts", "Dragon Slayer", "Hakusensha", "Glénat Manga"],
        "Metal Gear": ["Metal Gear", "Hideo Kojima"],
        "Gainax": ["Gainax", "Neon Genesis Evangelion"],
        "MAPPA": ["MAPPA", "Jujutsu Kaisen"],
        "The Dark Knight": ["The Dark Knight", "Heath Ledger", "Joker"],
        "Demon Slayer": ["Demon Slayer", "Kimetsu no Yaiba"],
        "Hiroshi Kamiya": ["Hiroshi Kamiya", "Levi Ackerman", "Trafalgar Law"],
    }

    migrated_count = 0
    for entry in data:
        # 1. expected_entities
        if "expected_entities" not in entry:
            title = entry.get("expected_title", "")
            entities = []
            if title in entity_mappings:
                entities = list(entity_mappings[title])
            elif title and title not in ["None", "Multiple", "0"]:
                entities = [title]

            # Extract additional key entities from query or ground_truth if empty
            if not entities:
                for key in entity_mappings:
                    if (
                        key.lower() in entry["query"].lower()
                        or key.lower() in entry["ground_truth"].lower()
                    ):
                        entities.extend(entity_mappings[key])

            # Dedup and clean
            entry["expected_entities"] = list(dict.fromkeys(entities))
            migrated_count += 1

        # 2. expected_contexts
        if "expected_contexts" not in entry:
            entry["expected_contexts"] = list(entry.get("contexts", []))

        # 3. expected_chunks
        if "expected_chunks" not in entry:
            expected_id = entry.get("expected_id", "0")
            if expected_id and expected_id != "0":
                entry["expected_chunks"] = [expected_id]
            else:
                entry["expected_chunks"] = []

        # 4. multi_turn_history
        if "multi_turn_history" not in entry:
            entry["multi_turn_history"] = []

    # Add new multi-turn entries if not already present
    has_multi_turn_19 = any(
        e["query"] == "Dans quel magazine a-t-il été prépublié ?" for e in data
    )
    if not has_multi_turn_19:
        data.append(
            {
                "query": "Dans quel magazine a-t-il été prépublié ?",
                "expected_id": "19",
                "expected_title": "Monster",
                "is_architectural": True,
                "query_type": "cross-media",
                "ground_truth": "Monster de Naoki Urasawa a été prépublié dans le magazine Big Comic Original.",
                "domain": "publishers_fr",
                "difficulty": "hard",
                "contexts": [
                    "Naoki Urasawa prépublie Monster dans Big Comic Original et Pluto dans Big Comic Spirits."
                ],
                "expected_entities": ["Monster", "Naoki Urasawa", "Big Comic Original"],
                "expected_contexts": [
                    "Naoki Urasawa prépublie Monster dans Big Comic Original et Pluto dans Big Comic Spirits."
                ],
                "expected_chunks": ["19"],
                "multi_turn_history": [
                    {"role": "user", "content": "Qui a écrit le manga Monster ?"},
                    {"role": "assistant", "content": "Naoki Urasawa."},
                ],
            }
        )

    has_multi_turn_16498 = any(
        e["query"] == "Qui anime cette adaptation et a aussi produit Vinland Saga ?"
        for e in data
    )
    if not has_multi_turn_16498:
        data.append(
            {
                "query": "Qui anime cette adaptation et a aussi produit Vinland Saga ?",
                "expected_id": "16498",
                "expected_title": "Attack on Titan",
                "is_architectural": True,
                "query_type": "graph",
                "ground_truth": "Wit Studio a animé les premières saisons de L'Attaque des Titans ainsi que la première saison de Vinland Saga.",
                "domain": "episodes_stats",
                "difficulty": "hard",
                "contexts": [
                    "Le studio Wit Studio a produit Vinland Saga et L'Attaque des Titans."
                ],
                "expected_entities": [
                    "Wit Studio",
                    "L'Attaque des Titans",
                    "Vinland Saga",
                ],
                "expected_contexts": [
                    "Le studio Wit Studio a produit Vinland Saga et L'Attaque des Titans."
                ],
                "expected_chunks": ["16498"],
                "multi_turn_history": [
                    {
                        "role": "user",
                        "content": "Quel studio a animé Shingeki no Kyojin au début ?",
                    },
                    {"role": "assistant", "content": "Wit Studio."},
                ],
            }
        )

    with open(gold_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(
        f"Successfully migrated {migrated_count} queries and saved {len(data)} total queries to {gold_path}."
    )


if __name__ == "__main__":
    migrate_gold_set()
