import json
import os

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILTERED_CHARS_PATH = os.path.join(
    BASE_DIR, "data", "processed", "filtered_characters.json"
)
COMBAT_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "combat_data.json")
FAILED_ATTEMPTS_PATH = os.path.join(
    BASE_DIR, "data", "processed", "failed_attempts.json"
)


def analyze_completion():
    with open(FILTERED_CHARS_PATH, "r", encoding="utf-8") as f:
        filtered = json.load(f)
        filtered_names = {c["name"] for c in filtered}

    combat_names = set()
    if os.path.exists(COMBAT_DATA_PATH):
        with open(COMBAT_DATA_PATH, "r", encoding="utf-8") as f:
            combat = json.load(f)
            # Some versions might have different names, but they came from a root name
            # For simplicity, let's look at the successfully ingested list
            # Actually, the ingestion logic works by iterating through filtered_characters
            # Let's see which names from 'filtered' are represented in 'combat'
            for c in combat:
                # We need to find which original name this version belongs to
                # The version name often contains the original name
                for orig in filtered_names:
                    if orig.split()[0].upper() in c["name"].upper():
                        combat_names.add(orig)

    failed_names = set()
    if os.path.exists(FAILED_ATTEMPTS_PATH):
        with open(FAILED_ATTEMPTS_PATH, "r", encoding="utf-8") as f:
            failed_names = set(json.load(f))

    remaining = filtered_names - combat_names - failed_names

    print(f"Total characters in DB: {len(filtered_names)}")
    print(f"Successfully processed (at least 1 version): {len(combat_names)}")
    print(f"Marked as Failed (no wiki page found): {len(failed_names)}")
    print(f"Remaining to process: {len(remaining)}")

    if remaining:
        print("\nNext 10 characters to process:")
        for name in list(remaining)[:10]:
            print(f"- {name}")


if __name__ == "__main__":
    analyze_completion()
