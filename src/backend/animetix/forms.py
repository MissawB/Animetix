from django import forms
from django.core.exceptions import ValidationError
import re

class BaseGameForm(forms.Form):
    """Base class for all game-related forms with common validation."""
    def clean_text(self, field_name, max_len=150):
        text = self.cleaned_data.get(field_name, '').strip()
        if not text:
            raise ValidationError("Ce champ ne peut pas être vide.")
        if len(text) > max_len:
            raise ValidationError(f"Le texte est trop long (max {max_len} caractères).")
        # Anti-spam / Anti-injection basic
        if re.search(r'[<>{}[\]]', text):
            raise ValidationError("Caractères spéciaux non autorisés.")
        return text

class GameGuessForm(BaseGameForm):
    guess = forms.CharField(max_length=100, required=True, label="Votre proposition")
    
    def clean_guess(self):
        return self.clean_text('guess', 100)

class VisionQuestForm(BaseGameForm):
    description = forms.CharField(max_length=200, required=True, label="Description de l'image")
    
    def clean_description(self):
        return self.clean_text('description', 200)

class AniminatorForm(BaseGameForm):
    question = forms.CharField(max_length=150, required=True, label="Votre question")
    
    def clean_question(self):
        return self.clean_text('question', 150)

class AkinetixAnswerForm(forms.Form):
    answer = forms.ChoiceField(choices=[('OUI', 'Oui'), ('NON', 'Non'), ('PEUT-ÊTRE', 'Peut-être')], required=True)

class CustomConfigForm(forms.Form):
    whitelist = forms.MultipleChoiceField(required=False)
    blacklist = forms.MultipleChoiceField(required=False)
    genres_white = forms.MultipleChoiceField(required=False)
    genres_black = forms.MultipleChoiceField(required=False)
    tags_white = forms.MultipleChoiceField(required=False)
    tags_black = forms.MultipleChoiceField(required=False)
    mode = forms.ChoiceField(choices=[('all', 'All'), ('white', 'Whitelist')], initial='all')
