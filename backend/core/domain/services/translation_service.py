from typing import Dict

class TranslationService:
    """
    Service dedicated to AI-generated content translations and dynamic game prompts.
    Static interface text is now handled by Django's standard i18n system (.po files).
    """
    def __init__(self):
        self._translations = {
            'Français': {
                'ai_thinking': 'L\'IA réfléchit...',
                'ai_oracle_prefix': 'L\'Oracle dit :',
                'ai_guess_prefix': 'Je pense à :',
                'ai_paradox_scenario': 'Scénario Paradoxal',
                'ai_fusion_reasoning': 'Analyse de Fusion',
                'ai_confidence': 'Indice de confiance',
                'game_over_win': 'Gagné ! Félicitations.',
                'game_over_loss': 'Perdu... Retente ta chance !',
                'game_over_secret_was': 'Le titre secret était :',
                'hint_poster': 'Affiche floutée',
                'hint_character': 'Un personnage clé',
                'hint_rec': 'Recommandation similaire',
                'hint_sim': 'Personnage sémantiquement proche',
                'hint_chars': 'Liste des personnages',
                'hint_origin': 'Œuvre d\'origine',
                'hint_words': 'Mots-clés thématiques',
                'hint_vibe': 'Ambiance (Vibe)',
            },
            'English': {
                'ai_thinking': 'AI is thinking...',
                'ai_oracle_prefix': 'The Oracle says:',
                'ai_guess_prefix': 'I am thinking of:',
                'ai_paradox_scenario': 'Paradox Scenario',
                'ai_fusion_reasoning': 'Fusion Analysis',
                'ai_confidence': 'Confidence level',
                'game_over_win': 'Victory! Congratulations.',
                'game_over_loss': 'Lost... Try again!',
                'game_over_secret_was': 'The secret title was:',
                'hint_poster': 'Blurred poster',
                'hint_character': 'A key character',
                'hint_rec': 'Similar recommendation',
                'hint_sim': 'Semantically close character',
                'hint_chars': 'Character list',
                'hint_origin': 'Original work',
                'hint_words': 'Thematic keywords',
                'hint_vibe': 'Atmosphere (Vibe)',
            }
        }

    def get_translations(self, lang: str) -> Dict[str, str]:
        """Returns the dictionary for AI content based on the language name."""
        return self._translations.get(lang, self._translations['Français'])
