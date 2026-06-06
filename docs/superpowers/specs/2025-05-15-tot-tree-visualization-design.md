# Design Spec: ToT Exploration Tree Capture

## Overview
Enrich the `TreeOfThoughtsSearchService` to capture and return the full exploration tree (nodes and links) to enable visualization in the frontend using `react-force-graph-2d`.

## Architecture
- **Nodes**: Each thought generated (including pruned ones) will be a node.
- **Links**: Parent-child relationships will be captured as links.
- **Service**: `TreeOfThoughtsSearchService` will be updated to manage these lists during the `solve_with_tree_of_thoughts` execution.

## Data Structures
The returned dictionary from `solve_with_tree_of_thoughts` will include:
```json
"full_tree": {
  "nodes": [
    {
      "id": "node_0_0",
      "label": "Start",
      "full_text": "Start",
      "score": 1.0,
      "status": "root"
    },
    ...
  ],
  "links": [
    {
      "source": "node_0_0",
      "target": "node_1_0"
    },
    ...
  ]
}
```

## Logic Changes
1.  Initialize `nodes` with the root "Start" node.
2.  Initialize `links` as an empty list.
3.  Each node in `current_paths` will now track its `id`.
4.  In the generation loop:
    - Generate a unique `child_id` using `node_{step}_{parent_idx}_{branch_idx}`.
    - Create a new node object.
    - Determine `status`:
        - `pruned` if score < 0.5.
        - `selected` if it's among the top `breadth` after sorting.
        - `final` if it's part of the `best_thought_path`.
    - Add to `nodes` and `links`.

## Testing Strategy
- Create `tests/core/test_tot_service_tree.py`.
- Mock `InferencePort` to return predictable thoughts and scores.
- Verify `full_tree` structure and content.
- Ensure pruned nodes are present as requested.
