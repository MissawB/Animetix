import json
import sys

def get_keys(d, prefix=''):
    keys = set()
    for k, v in d.items():
        if isinstance(v, dict):
            keys.update(get_keys(v, f"{prefix}{k}."))
        else:
            keys.add(f"{prefix}{k}")
    return keys

try:
    with open(r'C:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/public/locales/en/translation.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open(r'C:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/public/locales/fr/translation.json', 'r', encoding='utf-8') as f:
        fr = json.load(f)
    
    en_keys = get_keys(en)
    fr_keys = get_keys(fr)
    
    en_only = en_keys - fr_keys
    fr_only = fr_keys - en_keys
    
    if en_only:
        print(f"Keys only in EN: {en_only}")
    if fr_only:
        print(f"Keys only in FR: {fr_only}")
    
    if not en_only and not fr_only:
        print("All keys are consistent between EN and FR.")
    else:
        sys.exit(1)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
