from animetix.forms import GameGuessForm, VisionQuestForm, AkinetixAnswerForm


def test_game_guess_form_valid():
    form = GameGuessForm({"guess": "Naruto"})
    assert form.is_valid()
    assert form.cleaned_data["guess"] == "Naruto"


def test_game_guess_form_empty():
    form = GameGuessForm({"guess": ""})
    assert not form.is_valid()
    assert "obligatoire" in form.errors["guess"][0]


def test_game_guess_form_invalid_chars():
    form = GameGuessForm({"guess": "<script>"})
    assert not form.is_valid()
    assert "non autorisés" in form.errors["guess"][0]


def test_vision_quest_form_too_long():
    form = VisionQuestForm({"description": "a" * 201})
    assert not form.is_valid()
    assert "au plus 200" in form.errors["description"][0]


def test_akinetix_form_valid():
    form = AkinetixAnswerForm({"answer": "OUI"})
    assert form.is_valid()


def test_akinetix_form_invalid():
    form = AkinetixAnswerForm({"answer": "BLABLA"})
    assert not form.is_valid()
