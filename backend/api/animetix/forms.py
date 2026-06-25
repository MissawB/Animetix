import re

from django import forms
from django.core.exceptions import ValidationError


class BaseGameForm(forms.Form):
    """Base class for all game-related forms with common validation."""

    def clean_text(self, field_name, max_len=150):
        text = self.cleaned_data.get(field_name, "").strip()
        if not text:
            raise ValidationError("Ce champ ne peut pas être vide.")
        if len(text) > max_len:
            raise ValidationError(f"Le texte est trop long (max {max_len} caractères).")
        # Anti-spam / Anti-injection basic
        if re.search(r"[<>{}[\]]", text):
            raise ValidationError("Caractères spéciaux non autorisés.")
        return text


class GameGuessForm(BaseGameForm):
    guess = forms.CharField(max_length=100, required=True, label="Votre proposition")

    def clean_guess(self):
        return self.clean_text("guess", 100)


class VisionQuestForm(BaseGameForm):
    description = forms.CharField(
        max_length=200, required=True, label="Description de l'image"
    )

    def clean_description(self):
        return self.clean_text("description", 200)


class EmojiStreamForm(BaseGameForm):
    target_secret = forms.CharField(max_length=150, required=True)

    def __init__(self, *args, **kwargs):
        if args and "secret" in args[0]:
            data = args[0].copy() if hasattr(args[0], "copy") else args[0]
            data["target_secret"] = data.pop("secret")
            args = (data,) + args[1:]
        super().__init__(*args, **kwargs)

    def clean_target_secret(self):
        return self.clean_text("target_secret", 150)


class ParadoxStreamForm(BaseGameForm):
    item_a = forms.CharField(max_length=150, required=True)
    item_b = forms.CharField(max_length=150, required=True)
    intruder = forms.CharField(max_length=150, required=True)

    def __init__(self, *args, **kwargs):
        if args:
            data = args[0].copy() if hasattr(args[0], "copy") else args[0]
            if "t1" in data:
                data["item_a"] = data.pop("t1")
            if "t2" in data:
                data["item_b"] = data.pop("t2")
            args = (data,) + args[1:]
        super().__init__(*args, **kwargs)

    def clean_item_a(self):
        return self.clean_text("item_a", 150)

    def clean_item_b(self):
        return self.clean_text("item_b", 150)

    def clean_intruder(self):
        return self.clean_text("intruder", 150)


class AgenticRagForm(BaseGameForm):
    query = forms.CharField(max_length=200, required=True)

    def __init__(self, *args, **kwargs):
        if args and "q" in args[0]:
            data = args[0].copy() if hasattr(args[0], "copy") else args[0]
            data["query"] = data.pop("q")
            args = (data,) + args[1:]
        super().__init__(*args, **kwargs)

    def clean_query(self):
        return self.clean_text("query", 200)


class AniminatorForm(BaseGameForm):
    question = forms.CharField(max_length=150, required=True, label="Votre question")

    def __init__(self, *args, **kwargs):
        if args and "q" in args[0]:
            data = args[0].copy() if hasattr(args[0], "copy") else args[0]
            data["question"] = data.pop("q")
            args = (data,) + args[1:]
        super().__init__(*args, **kwargs)

    def clean_question(self):
        return self.clean_text("question", 150)


class AkinetixAnswerForm(forms.Form):
    answer = forms.ChoiceField(
        choices=[("OUI", "Oui"), ("NON", "Non"), ("PEUT-ÊTRE", "Peut-être")],
        required=True,
    )


class CustomConfigForm(forms.Form):
    whitelist = forms.MultipleChoiceField(required=False)
    blacklist = forms.MultipleChoiceField(required=False)
    genres_white = forms.MultipleChoiceField(required=False)
    genres_black = forms.MultipleChoiceField(required=False)
    tags_white = forms.MultipleChoiceField(required=False)
    tags_black = forms.MultipleChoiceField(required=False)
    mode = forms.ChoiceField(
        choices=[("all", "All"), ("white", "Whitelist")], initial="all"
    )


# --- Vertex AI MLOps Pipelines + Feature Store forms (ported from feature/vertex-pipelines) ---
class VertexPipelineTriggerForm(forms.Form):
    pipeline_type = forms.ChoiceField(
        choices=[("dpo", "DPO"), ("rag", "RAG")], required=True
    )
    min_samples = forms.IntegerField(min_value=1, required=False, initial=100)


class VertexPipelineListForm(forms.Form):
    pipeline_name = forms.CharField(max_length=255, required=False)
    limit = forms.IntegerField(min_value=1, max_value=100, required=False, initial=20)


class UserIDForm(forms.Form):
    user_id = forms.CharField(max_length=100, required=True)


class VertexFeatureStoreForm(forms.Form):
    user_id = forms.CharField(max_length=100, required=True)
    features = forms.JSONField(required=True)


class ToTStreamForm(forms.Form):
    q = forms.CharField(max_length=500, required=True)
    breadth = forms.IntegerField(min_value=1, max_value=10, required=False, initial=3)
    depth = forms.IntegerField(min_value=1, max_value=10, required=False, initial=3)
