from unittest.mock import MagicMock, patch

from core.domain.services.companion_service import CompanionService


def _svc(memory_service=None):
    pm = MagicMock()
    pm.get_prompt.return_value = ("p", "s")
    llm = MagicMock()
    llm.generate.return_value = "resp"
    return CompanionService(llm, pm, memory_service=memory_service), pm


def test_generate_injects_retrieved_memories():
    mem = MagicMock()
    mem.retrieve_relevant_memories.return_value = "past: likes Naruto"
    svc, pm = _svc(mem)
    svc.generate_response("sensei", "hi", user_id="u1")
    mem.retrieve_relevant_memories.assert_called_once_with("u1", "hi")
    assert pm.get_prompt.call_args.kwargs["memories"] == "past: likes Naruto"


def test_generate_no_memories_without_user_id():
    mem = MagicMock()
    svc, pm = _svc(mem)
    svc.generate_response("sensei", "hi")
    mem.retrieve_relevant_memories.assert_not_called()
    assert pm.get_prompt.call_args.kwargs["memories"] == ""


def test_generate_no_memories_without_memory_service():
    svc, pm = _svc(None)
    svc.generate_response("sensei", "hi", user_id="u1")
    assert pm.get_prompt.call_args.kwargs["memories"] == ""


def test_remember_stores_evicted_turns():
    mem = MagicMock()
    svc, _ = _svc(mem)
    turns = [{"role": "user", "content": "old"}]

    def run_sync(target, args, daemon):
        target(*args)
        return MagicMock()

    with patch(
        "core.domain.services.companion_service.threading.Thread",
        side_effect=run_sync,
    ):
        svc.remember("u1", turns)
    mem.store_memory.assert_called_once_with("u1", turns)


def test_remember_is_noop_without_turns_user_or_service():
    mem = MagicMock()
    svc, _ = _svc(mem)
    svc.remember("u1", [])  # no turns
    svc.remember(None, [{"x": 1}])  # no user
    CompanionService(MagicMock(), MagicMock(), None).remember(
        "u1", [{"x": 1}]
    )  # no service
    mem.store_memory.assert_not_called()
