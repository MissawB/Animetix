import json
import os

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMBAT_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "combat_data.json")


def audit_combat_data():
    if not os.path.exists(COMBAT_DATA_PATH):
        print(f"❌ {COMBAT_DATA_PATH} not found.")
        return

    with open(COMBAT_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"🔍 Auditing {len(data)} combat profiles...")

    issues = []

    for char in data:
        char_issues = []
        name = char.get("name", "Unknown")
        stats = char.get("stats", {})

        # 1. Check for missing/default stats (signs of extraction failure)
        if stats.get("tier") == "Unknown":
            char_issues.append("Tier is Unknown")

        # 2. Check for suspicious summary length (too short = likely placeholder)
        summary = char.get("summary", "")
        if len(summary) < 20 or "No summary available" in summary:
            char_issues.append("Summary is too short or generic")

        # 3. Check for obvious hallucination artifacts (e.g. {{...}} in tier)
        tier = stats.get("tier", "")
        if "{{" in tier or "}}" in tier:
            char_issues.append(f"Suspicious tier formatting: {tier}")

        # 4. Check for length of tier string (if it's a paragraph, it's a hallucination)
        if len(tier) > 50:
            char_issues.append(f"Tier string is suspiciously long: {len(tier)} chars")

        if char_issues:
            issues.append({"name": name, "issues": char_issues})

    # Report
    if issues:
        print(f"\n⚠️ Found {len(issues)} profiles with potential issues:")
        for issue in issues:
            print(f"- {issue['name']}: {', '.join(issue['issues'])}")
    else:
        print("\n✅ All profiles appear clean and structured!")


if __name__ == "__main__":
    audit_combat_data()
