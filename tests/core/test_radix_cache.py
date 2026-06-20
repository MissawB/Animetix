import torch
from core.utils.radix_cache import RadixCacheManager, clone_past_key_values


def test_clone_past_key_values():
    t = torch.randn(1, 2, 3)
    pkv = ((t,),)
    cloned = clone_past_key_values(pkv)
    assert cloned is not pkv
    assert torch.equal(cloned[0][0], t)


def test_radix_cache_hit_and_eviction():
    manager = RadixCacheManager(max_nodes=2, min_prefix_len=3)
    pkv1 = ((torch.randn(1, 2, 3),),)

    # Test insert and query
    manager.insert([1, 2, 3, 4], pkv1)
    hit_pkv, L = manager.query([1, 2, 3, 4, 5])
    assert L == 4
    assert hit_pkv is not None

    # Test minimum prefix length restriction
    pkv2 = ((torch.randn(1, 2, 3),),)
    manager.insert([1, 2], pkv2)
    hit_pkv2, L2 = manager.query([1, 2, 5])
    assert L2 == 0
    assert hit_pkv2 is None

    # Test LRU eviction
    pkv3 = ((torch.randn(1, 2, 3),),)
    pkv4 = ((torch.randn(1, 2, 3),),)
    manager.insert([1, 2, 3, 5], pkv3)
    # Now nodes: root -> [1,2,3,4] and [1,2,3,5]. Limit is 2.
    manager.insert([1, 2, 3, 6], pkv4)  # Should evict the oldest node

    # Querying the evicted node should miss
    hit_pkv_evicted, L_evicted = manager.query([1, 2, 3, 4])
    assert L_evicted == 0
