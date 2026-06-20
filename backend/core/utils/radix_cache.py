import time
from typing import Any, Dict, List, Optional, Tuple


def clone_past_key_values(past_key_values: Any) -> Any:
    if past_key_values is None:
        return None
    from transformers.cache_utils import DynamicCache

    if isinstance(past_key_values, DynamicCache):
        cloned = DynamicCache()
        cloned.key_cache = [k.clone() for k in past_key_values.key_cache]
        cloned.value_cache = [v.clone() for v in past_key_values.value_cache]
        return cloned
    return tuple(tuple(t.clone() for t in layer) for layer in past_key_values)


class RadixNode:
    def __init__(self, token_id: Optional[int] = None):
        self.token_id = token_id
        self.children: Dict[int, "RadixNode"] = {}
        self.past_key_values: Optional[Any] = None
        self.last_accessed: float = time.time()


class RadixCacheManager:
    def __init__(self, max_nodes: int = 16, min_prefix_len: int = 10):
        self.root = RadixNode()
        self.max_nodes = max_nodes
        self.min_prefix_len = min_prefix_len
        self.node_list: List[RadixNode] = []

    def query(self, token_ids: List[int]) -> Tuple[Optional[Any], int]:
        current = self.root
        last_pkv_node = None
        match_len = 0
        current_depth = 0

        for token_id in token_ids:
            if token_id in current.children:
                current = current.children[token_id]
                current_depth += 1
                if current.past_key_values is not None:
                    last_pkv_node = current
                    match_len = current_depth
            else:
                break

        if last_pkv_node and match_len >= self.min_prefix_len:
            last_pkv_node.last_accessed = time.time()
            return clone_past_key_values(last_pkv_node.past_key_values), match_len
        return None, 0

    def insert(self, token_ids: List[int], past_key_values: Any):
        if len(token_ids) < self.min_prefix_len or past_key_values is None:
            return

        current = self.root
        for token_id in token_ids:
            if token_id not in current.children:
                node = RadixNode(token_id)
                current.children[token_id] = node
                self.node_list.append(node)
            current = current.children[token_id]

        current.past_key_values = past_key_values
        current.last_accessed = time.time()
        self._evict_if_needed()

    def _evict_if_needed(self):
        nodes_with_cache = [n for n in self.node_list if n.past_key_values is not None]
        if len(nodes_with_cache) > self.max_nodes:
            nodes_with_cache.sort(key=lambda n: n.last_accessed)
            evicted = nodes_with_cache[0]
            evicted.past_key_values = None
