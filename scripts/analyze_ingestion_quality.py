import json
import os
from collections import defaultdict

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMBAT_DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'combat_data.json')

def analyze_ingestion_quality():
    if not os.path.exists(COMBAT_DATA_PATH):
        print(f"❌ {COMBAT_DATA_PATH} not found.")
        return

    with open(COMBAT_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📊 Analyzing {len(data)} ingested combat profiles...\n")
    
    franchise_stats = defaultdict(list)
    duplicates_by_url = defaultdict(list)
    ai_generated = []
    suspicious_matches = []

    for char in data:
        name = char.get('name', 'Unknown')
        franchise = char.get('franchise') or "Unknown"
        url = char.get('wiki_url', 'No URL')
        
        franchise_stats[franchise].append(name)
        duplicates_by_url[url].append(name)
        
        if "(AI Generated)" in name:
            ai_generated.append(name)
        else:
            # Identity Check
            summary = char.get('summary', '').lower()
            f_lower = franchise.lower()
            if franchise != "Unknown":
                # Is the franchise mentioned in the summary or name?
                if f_lower not in name.lower() and f_lower not in summary:
                    suspicious_matches.append(f"{name} (Franchise expected: {franchise})")

    print(f"✅ Total Versions in JSON: {len(data)}")
    print(f"🤖 AI Generated Profiles: {len(ai_generated)}")
    print(f"🏢 Total Unique Franchises: {len(franchise_stats)}")
    
    print("\n--- 🧩 Multi-Version Coverage ---")
    for f, names in franchise_stats.items():
        if len(names) > 1:
            print(f"- {f}: {len(names)} versions ({', '.join(names)})")

    print("\n--- 🚨 Possible Identity Mismatches ---")
    if suspicious_matches:
        for match in suspicious_matches:
            print(f"- ⚠️ {match}")
    else:
        print("✅ No obvious character/franchise mismatches detected.")

    print("\n--- 🔄 True Duplicates (Same Wiki URL) ---")
    dups = {url: names for url, names in duplicates_by_url.items() if len(names) > 1}
    if dups:
        for url, names in dups.items():
            print(f"- {url} linked to: {', '.join(names)}")
    else:
        print("✅ No duplicate URLs found.")

if __name__ == "__main__":
    analyze_ingestion_quality()
