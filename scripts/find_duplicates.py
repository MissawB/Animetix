import json
import os
from collections import Counter

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMBAT_DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'combat_data.json')

def find_duplicates():
    if not os.path.exists(COMBAT_DATA_PATH):
        print(f"❌ {COMBAT_DATA_PATH} not found.")
        return

    with open(COMBAT_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"🔍 Analyzing {len(data)} combat profiles for duplicates...")
    
    # 1. Check by Name
    names = [c.get('name') for c in data]
    name_counts = Counter(names)
    dup_names = {name: count for name, count in name_counts.items() if count > 1}
    
    # 2. Check by Wiki URL (more reliable for "true" duplicates)
    urls = [c.get('wiki_url') for c in data if c.get('wiki_url')]
    url_counts = Counter(urls)
    dup_urls = {url: count for url, count in url_counts.items() if count > 1}

    if not dup_names and not dup_urls:
        print("✅ No duplicates found! All versions are unique.")
    else:
        if dup_names:
            print(f"\n⚠️ Found {len(dup_names)} names with multiple entries:")
            for name, count in dup_names.items():
                print(f"- {name}: {count} times")
        
        if dup_urls:
            print(f"\n⚠️ Found {len(dup_urls)} Wiki URLs with multiple entries (True duplicates):")
            for url, count in dup_urls.items():
                print(f"- {url}: {count} times")

if __name__ == "__main__":
    find_duplicates()
