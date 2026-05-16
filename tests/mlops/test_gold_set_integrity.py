import json
import os
import pytest

def test_gold_set_schema_integrity():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    gold_path = os.path.join(base_dir, 'data', 'mlops', 'gold_dataset.json')
    
    with open(gold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for entry in data:
        if entry.get('is_architectural'):
            assert 'query_type' in entry, f"Missing 'query_type' in architectural entry: {entry}"
            assert 'ground_truth' in entry, f"Missing 'ground_truth' in architectural entry: {entry}"
            assert entry['query_type'] in ['graph', 'visual', 'thematic', 'cross-media', 'negative'], f"Invalid query_type: {entry['query_type']}"
