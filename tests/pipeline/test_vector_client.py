import pytest
from pipeline.chroma_client import chroma_manager


@pytest.mark.django_db
def test_compatibility_vector_client():
    collection_name = "test_coll_client"

    # 1. Clean collection
    chroma_manager.delete_collection(collection_name)

    # 2. Get collection
    coll = chroma_manager.get_collection(collection_name)
    assert coll.count() == 0

    # 3. Add items
    ids = ["1", "2"]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]
    metadatas = [{"tag": "action"}, {"tag": "comedy"}]
    coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    assert coll.count() == 2

    # 4. Get items
    res_get = coll.get(ids=["1"], include=["embeddings", "metadatas"])
    assert "1" in res_get["ids"]
    assert res_get["embeddings"][0] == [1.0, 0.0]

    # 5. Query items
    res_query = coll.query(query_embeddings=[[1.0, 0.1]], n_results=1)
    assert res_query["ids"][0][0] == "1"
