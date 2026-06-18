from backend.api.animetix.forms import (
    AgenticRagForm,
    AniminatorForm,
    EmojiStreamForm,
    ParadoxStreamForm,
)


def test_emoji_stream_form_valid():
    # Frontend sends 'secret', mapped to 'target_secret'
    form = EmojiStreamForm({"secret": "item_123"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["target_secret"] == "item_123"


def test_paradox_stream_form_valid():
    # Frontend sends 't1', 't2', 'intruder'
    form = ParadoxStreamForm({"t1": "item_a", "t2": "item_b", "intruder": "intruder_x"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["item_a"] == "item_a"
    assert form.cleaned_data["item_b"] == "item_b"
    assert form.cleaned_data["intruder"] == "intruder_x"


def test_agentic_rag_form_valid():
    # Frontend sends 'q', mapped to 'query'
    form = AgenticRagForm({"q": "tell me about naruto"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["query"] == "tell me about naruto"


def test_animinator_form_legacy_mapping():
    # Frontend sends 'q', mapped to 'question'
    form = AniminatorForm({"q": "Is it a human?"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["question"] == "Is it a human?"


def test_animinator_form_direct():
    # Direct field also works
    form = AniminatorForm({"question": "Is it a human?"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["question"] == "Is it a human?"
