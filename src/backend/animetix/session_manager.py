from typing import Any, Dict, Optional

class GameSessionManager:
    """
    Infrastructure adapter to manage game state within the Django session.
    Decouples views from raw session key manipulation.
    """
    def __init__(self, request):
        self.session = request.session

    def get(self, key: str, default: Any = None) -> Any:
        return self.session.get(key, default)

    def set(self, key: str, value: Any):
        self.session[key] = value
        self.session.modified = True

    def update(self, data: Dict[str, Any]):
        self.session.update(data)
        self.session.modified = True

    # --- Classic Mode Helpers ---
    def get_classic_state(self) -> Dict[str, Any]:
        return {
            'secret_title': self.get('secret_title'),
            'guesses': self.get('guesses', []),
            'game_over': self.get('game_over', False),
            'revealed_hints': self.get('revealed_hints', []),
            'media_type': self.get('media_type', 'Anime'),
            'difficulty': self.get('difficulty', 'Normal'),
            'is_daily': self.get('is_daily', False),
            'is_ranked': self.get('is_ranked', False),
        }

    def start_classic_game(self, secret_title: str, difficulty: str, media_type: str):
        self.update({
            'secret_title': secret_title,
            'max_raw_sim': 0.8,
            'difficulty': difficulty,
            'media_type': media_type,
            'guesses': [],
            'game_over': False,
            'revealed_hints': []
        })

    def add_guess(self, guess_data: Dict[str, Any]):
        guesses = self.get('guesses', [])
        guesses.append(guess_data)
        guesses.sort(key=lambda x: x['score'], reverse=True)
        self.set('guesses', guesses)

    def reveal_hint(self, hint_type: str):
        revealed = self.get('revealed_hints', [])
        if hint_type not in revealed:
            revealed.append(hint_type)
            self.set('revealed_hints', revealed)

    def set_game_over(self, status: bool = True):
        self.set('game_over', status)

    # --- Akinetix Mode Helpers ---
    def start_akinetix_game(self, game_state: Dict[str, Any]):
        self.update({
            'akinetix_history': game_state['history'],
            'akinetix_current_q': game_state['current_q'],
            'akinetix_current_attr': game_state['current_attr'],
            'akinetix_game_over': game_state['game_over'],
            'akinetix_ai_guess': game_state['ai_guess'],
            'akinetix_probs': game_state['probs'],
            'akinetix_asked_attrs': game_state['asked_attrs']
        })

    def update_akinetix_state(self, new_state: Dict[str, Any]):
        self.update({
            'akinetix_history': new_state['history'],
            'akinetix_current_q': new_state['current_q'],
            'akinetix_current_attr': new_state['current_attr'],
            'akinetix_game_over': new_state['game_over'],
            'akinetix_ai_guess': new_state['ai_guess'],
            'akinetix_probs': new_state['probs'],
            'akinetix_asked_attrs': new_state['asked_attrs']
        })

    def get_akinetix_state(self) -> Dict[str, Any]:
        return {
            'history': self.get('akinetix_history', []),
            'current_q': self.get('akinetix_current_q'),
            'current_attr': self.get('akinetix_current_attr'),
            'game_over': self.get('akinetix_game_over', False),
            'ai_guess': self.get('akinetix_ai_guess'),
            'probs': self.get('akinetix_probs'),
            'asked_attrs': self.get('akinetix_asked_attrs'),
            'is_daily': self.get('is_daily', False)
        }

    # --- Emoji Mode Helpers ---
    def start_emoji_game(self, secret_title: str, emojis: list):
        self.update({
            'emoji_secret': secret_title,
            'emoji_list': emojis,
            'emoji_guesses': [],
            'emoji_game_over': False
        })

    def get_emoji_state(self) -> Dict[str, Any]:
        return {
            'secret': self.get('emoji_secret'),
            'emojis': self.get('emoji_list', []),
            'guesses': self.get('emoji_guesses', []),
            'game_over': self.get('emoji_game_over', False),
            'is_daily': self.get('is_daily', False),
            'is_ranked': self.get('is_ranked', False)
        }

    # --- Paradox Mode Helpers ---
    def start_paradox_game(self, intruder: str, options: list, reasoning: str, scenario: str, media_type: str):
        self.update({
            'paradox_answer': intruder,
            'paradox_options': options,
            'paradox_reasoning': reasoning,
            'paradox_scenario': scenario,
            'paradox_media': media_type,
            'paradox_game_over': False
        })

    def get_paradox_state(self) -> Dict[str, Any]:
        return {
            'answer': self.get('paradox_answer'),
            'options': self.get('paradox_options', []),
            'reasoning': self.get('paradox_reasoning'),
            'scenario': self.get('paradox_scenario'),
            'media': self.get('paradox_media', 'Anime'),
            'is_daily': self.get('is_daily', False)
        }


    # --- Vision Mode Helpers ---
    def start_vision_game(self, secret_id: str, secret_title: str, image_url: str, media_type: str):
        self.update({
            'vision_secret_id': secret_id,
            'vision_secret_title': secret_title,
            'vision_secret_image': image_url,
            'vision_media_type': media_type,
            'vision_guesses': [],
            'vision_game_over': False,
            'vision_best_score': 0.0
        })

    def get_vision_state(self) -> Dict[str, Any]:
        return {
            'secret_id': self.get('vision_secret_id'),
            'secret_title': self.get('vision_secret_title'),
            'image_url': self.get('vision_secret_image'),
            'media_type': self.get('vision_media_type', 'Anime'),
            'guesses': self.get('vision_guesses', []),
            'game_over': self.get('vision_game_over', False),
            'best_score': self.get('vision_best_score', 0.0),
            'is_daily': self.get('is_daily', False)
        }


    # --- Blind Test Helpers ---
    def start_blindtest_game(self, theme: Dict[str, Any]):
        self.update({
            'blindtest_secret': theme['anime_title'],
            'blindtest_song': theme['song_title'],
            'blindtest_artists': theme['artists'],
            'blindtest_video': theme['video_url'],
            'blindtest_type': theme['type'],
            'blindtest_guesses': [],
            'blindtest_game_over': False
        })

    def get_blindtest_state(self) -> Dict[str, Any]:
        return {
            'secret': self.get('blindtest_secret'),
            'song': self.get('blindtest_song'),
            'artists': self.get('blindtest_artists'),
            'video': self.get('blindtest_video'),
            'type': self.get('blindtest_type'),
            'guesses': self.get('blindtest_guesses', []),
            'game_over': self.get('blindtest_game_over', False),
            'is_daily': self.get('is_daily', False)
        }

    # --- Cover Test Helpers ---
    def start_covertest_game(self, cover: Dict[str, Any]):
        self.update({
            'covertest_secret': cover['manga_title'],
            'covertest_url': cover['cover_url'],
            'covertest_locale': cover['locale'],
            'covertest_volume': cover['volume'],
            'covertest_guesses': [],
            'covertest_game_over': False
        })

    def get_covertest_state(self) -> Dict[str, Any]:
        return {
            'secret': self.get('covertest_secret'),
            'url': self.get('covertest_url'),
            'locale': self.get('covertest_locale'),
            'volume': self.get('covertest_volume'),
            'guesses': self.get('covertest_guesses', []),
            'game_over': self.get('game_over', False),
            'is_daily': self.get('is_daily', False)
        }

    # --- State Management (ex-utils) ---
    def get_current_mode(self) -> str:
        return self.get('media_type', 'Anime')

    def switch_mode(self, mode: str):
        if mode in ['Anime', 'Manga', 'Character']:
            self.set('media_type', mode)

    def switch_language(self, lang: str):
        if lang in ['Français', 'English']:
            self.set('language', lang)

    def switch_difficulty(self, diff: str):
        if diff in ['Easy', 'Normal', 'Hard', 'Impossible', 'Custom']:
            self.set('difficulty', diff)

    def handle_win_achievements(self, unlocked_achievements: list):
        """Stores newly unlocked achievements in the session for Toast display."""
        if not unlocked_achievements: 
            return
        new_ach = self.get('new_achievements', [])
        for ach in unlocked_achievements:
            new_ach.append({
                'code': ach.code,
                'name': ach.name,
                'icon': ach.icon,
                'xp': ach.xp_reward
            })
        self.set('new_achievements', new_ach)



