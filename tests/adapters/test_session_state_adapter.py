from adapters.persistence.session_state_adapter import DjangoSessionStateAdapter


def test_session_state_adapter_get_set():
    class MockSession(dict):
        def __init__(self):
            super().__init__()
            self.modified = False

    mock_session = MockSession()
    adapter = DjangoSessionStateAdapter(mock_session)

    # Test Set
    adapter.set("test_key", "test_value")
    assert mock_session["test_key"] == "test_value"
    assert mock_session.modified is True

    # Test Get
    mock_session.modified = False
    assert adapter.get("test_key") == "test_value"
    assert adapter.get("non_existent", "default") == "default"

    # Test Update
    adapter.update({"k1": "v1", "k2": "v2"})
    assert mock_session["k1"] == "v1"
    assert mock_session["k2"] == "v2"
    assert mock_session.modified is True

    # Test Delete
    mock_session.modified = False
    adapter.delete("k1")
    assert "k1" not in mock_session
    assert mock_session.modified is True
