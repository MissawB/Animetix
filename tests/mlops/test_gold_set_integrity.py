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

        # Validations for evolved schema fields
        assert 'expected_entities' in entry, f"Missing 'expected_entities' in entry: {entry}"
        assert isinstance(entry['expected_entities'], list), f"'expected_entities' must be a list: {entry}"
        assert all(isinstance(x, str) for x in entry['expected_entities']), f"'expected_entities' must contain only strings: {entry}"

        assert 'expected_contexts' in entry, f"Missing 'expected_contexts' in entry: {entry}"
        assert isinstance(entry['expected_contexts'], list), f"'expected_contexts' must be a list: {entry}"
        assert all(isinstance(x, str) for x in entry['expected_contexts']), f"'expected_contexts' must contain only strings: {entry}"

        assert 'expected_chunks' in entry, f"Missing 'expected_chunks' in entry: {entry}"
        assert isinstance(entry['expected_chunks'], list), f"'expected_chunks' must be a list: {entry}"
        assert all(isinstance(x, str) for x in entry['expected_chunks']), f"'expected_chunks' must contain only strings: {entry}"

        assert 'multi_turn_history' in entry, f"Missing 'multi_turn_history' in entry: {entry}"
        assert isinstance(entry['multi_turn_history'], list), f"'multi_turn_history' must be a list: {entry}"
        for turn in entry['multi_turn_history']:
            assert isinstance(turn, dict), f"Each turn in 'multi_turn_history' must be a dict: {entry}"
            assert 'role' in turn and 'content' in turn, f"Each turn must have 'role' and 'content' keys: {turn}"
            assert isinstance(turn['role'], str) and isinstance(turn['content'], str), f"Role and content must be strings: {turn}"
