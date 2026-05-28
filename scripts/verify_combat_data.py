import json

try:
    with open('data/processed/combat_data.json', encoding='utf-8') as f:
        data = json.load(f)
        print(f"Total: {len(data)}")
        for c in data:
            name = c.get('name')
            franchise = c.get('franchise', 'N/A')
            stats = c.get('stats', {})
            tier = stats.get('tier')
            tier_val = stats.get('tier_value')
            speed = stats.get('speed', 'N/A')
            durability = stats.get('durability', 'N/A')
            intelligence = stats.get('intelligence', 'N/A')
            print(f"- {name} (Franchise: {franchise})")
            print(f"  Tier: {tier} (Value: {tier_val})")
            print(f"  Speed: {speed}")
            print(f"  Durability: {durability}")
            print(f"  Intelligence: {intelligence}")
            print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
