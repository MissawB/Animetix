from typing import Any, Dict, List

from core.ports.game_state_port import GameStatePort


class GameSessionService:
    """
    Domain service to manage game state logic.
    Decouples business logic from specific storage infrastructure.
    """

    def __init__(self, state_port: GameStatePort):
        self.port = state_port

    def get(self, key: str, default: Any = None) -> Any:
        return self.port.get(key, default)

    def set(self, key: str, value: Any):
        self.port.set(key, value)

    def update(self, data: Dict[str, Any]):
        self.port.update(data)

    # --- Classic Mode Helpers ---
    def get_classic_state(self) -> Dict[str, Any]:
        return {
            "secret_title": self.port.get("secret_title"),
            "guesses": self.port.get("guesses", []),
            "game_over": self.port.get("game_over", False),
            "revealed_hints": self.port.get("revealed_hints", []),
            "media_type": self.port.get("media_type", "Anime"),
            "difficulty": self.port.get("difficulty", "Normal"),
            "is_daily": self.port.get("is_daily", False),
            "is_ranked": self.port.get("is_ranked", False),
        }

    def start_classic_game(self, secret_title: str, difficulty: str, media_type: str):
        self.port.update(
            {
                "secret_title": secret_title,
                "max_raw_sim": 0.8,
                "difficulty": difficulty,
                "media_type": media_type,
                "guesses": [],
                "game_over": False,
                "revealed_hints": [],
            }
        )

    def add_guess(self, guess_data: Dict[str, Any]):
        guesses = self.port.get("guesses", [])
        guesses.append(guess_data)
        guesses.sort(key=lambda x: x["score"], reverse=True)
        self.port.set("guesses", guesses)

    def reveal_hint(self, hint_type: str):
        revealed = self.port.get("revealed_hints", [])
        if hint_type not in revealed:
            revealed.append(hint_type)
            self.port.set("revealed_hints", revealed)

    # --- Akinetix Mode Helpers ---
    def start_akinetix_game(self, game_state: Dict[str, Any]):
        self.port.update(
            {
                "akinetix_history": game_state["history"],
                "akinetix_current_q": game_state["current_q"],
                "akinetix_current_attr": game_state["current_attr"],
                "akinetix_game_over": game_state["game_over"],
                "akinetix_ai_guess": game_state["ai_guess"],
                "akinetix_probs": game_state["probs"],
                "akinetix_asked_attrs": game_state["asked_attrs"],
            }
        )

    def get_akinetix_state(self) -> Dict[str, Any]:
        return {
            "history": self.port.get("akinetix_history", []),
            "current_q": self.port.get("akinetix_current_q"),
            "current_attr": self.port.get("akinetix_current_attr"),
            "game_over": self.port.get("akinetix_game_over", False),
            "ai_guess": self.port.get("akinetix_ai_guess"),
            "probs": self.port.get("akinetix_probs"),
            "asked_attrs": self.port.get("akinetix_asked_attrs"),
            "is_daily": self.port.get("is_daily", False),
        }

    # --- Emoji Mode Helpers ---
    def start_emoji_game(self, secret_title: str, emojis: list):
        self.port.update(
            {
                "emoji_secret": secret_title,
                "emoji_list": emojis,
                "emoji_guesses": [],
                "emoji_game_over": False,
            }
        )

    def get_emoji_state(self) -> Dict[str, Any]:
        return {
            "secret": self.port.get("emoji_secret"),
            "emojis": self.port.get("emoji_list", []),
            "guesses": self.port.get("emoji_guesses", []),
            "game_over": self.port.get("emoji_game_over", False),
            "is_daily": self.port.get("is_daily", False),
            "is_ranked": self.port.get("is_ranked", False),
        }

    # --- Paradox Mode Helpers ---
    def start_paradox_game(
        self,
        intruder: str,
        options: list,
        reasoning: str,
        scenario: str,
        media_type: str,
    ):
        self.port.update(
            {
                "paradox_answer": intruder,
                "paradox_options": options,
                "paradox_reasoning": reasoning,
                "paradox_scenario": scenario,
                "paradox_media": media_type,
                "paradox_game_over": False,
            }
        )

    def get_paradox_state(self) -> Dict[str, Any]:
        return {
            "answer": self.port.get("paradox_answer"),
            "options": self.port.get("paradox_options", []),
            "reasoning": self.port.get("paradox_reasoning"),
            "scenario": self.port.get("paradox_scenario"),
            "media": self.port.get("paradox_media", "Anime"),
            "is_daily": self.port.get("is_daily", False),
        }

    # --- Vision Mode Helpers ---
    def start_vision_game(
        self, secret_id: str, secret_title: str, image_url: str, media_type: str
    ):
        self.port.update(
            {
                "vision_secret_id": secret_id,
                "vision_secret_title": secret_title,
                "vision_secret_image": image_url,
                "vision_media_type": media_type,
                "vision_guesses": [],
                "vision_game_over": False,
                "vision_best_score": 0.0,
            }
        )

    def get_vision_state(self) -> Dict[str, Any]:
        return {
            "secret_id": self.port.get("vision_secret_id"),
            "secret_title": self.port.get("vision_secret_title"),
            "image_url": self.port.get("vision_secret_image"),
            "media_type": self.port.get("vision_media_type", "Anime"),
            "guesses": self.port.get("vision_guesses", []),
            "game_over": self.port.get("vision_game_over", False),
            "best_score": self.port.get("vision_best_score", 0.0),
            "is_daily": self.port.get("is_daily", False),
        }

    # --- Blind Test Helpers ---
    def start_blindtest_game(self, theme: Dict[str, Any]):
        self.port.update(
            {
                "blindtest_secret": theme["anime_title"],
                "blindtest_song": theme["song_title"],
                "blindtest_artists": theme["artists"],
                "blindtest_video": theme["video_url"],
                "blindtest_type": theme["type"],
                "blindtest_guesses": [],
                "blindtest_game_over": False,
            }
        )

    def get_blindtest_state(self) -> Dict[str, Any]:
        return {
            "secret": self.port.get("blindtest_secret"),
            "song": self.port.get("blindtest_song"),
            "artists": self.port.get("blindtest_artists"),
            "video": self.port.get("blindtest_video"),
            "type": self.port.get("blindtest_type"),
            "guesses": self.port.get("blindtest_guesses", []),
            "game_over": self.port.get("blindtest_game_over", False),
            "is_daily": self.port.get("is_daily", False),
        }

    # --- Cover Test Helpers ---
    def start_covertest_game(self, cover: Dict[str, Any]):
        self.port.update(
            {
                "covertest_secret": cover["manga_title"],
                "covertest_url": cover["cover_url"],
                "covertest_locale": cover["locale"],
                "covertest_volume": cover["volume"],
                "covertest_guesses": [],
                "covertest_game_over": False,
            }
        )

    def get_covertest_state(self) -> Dict[str, Any]:
        return {
            "secret": self.port.get("covertest_secret"),
            "url": self.port.get("covertest_url"),
            "locale": self.port.get("covertest_locale"),
            "volume": self.port.get("covertest_volume"),
            "guesses": self.port.get("covertest_guesses", []),
            "game_over": self.port.get("covertest_game_over", False),
            "is_daily": self.port.get("is_daily", False),
        }

    # --- State Management ---
    def get_current_mode(self) -> str:
        return self.port.get("media_type", "Anime")

    def switch_mode(self, mode: str):
        if mode in ["Anime", "Manga", "Character"]:
            self.port.set("media_type", mode)

    def switch_language(self, lang: str):
        if lang in ["Français", "English"]:
            self.port.set("language", lang)

    def switch_difficulty(self, diff: str):
        if diff in ["Easy", "Normal", "Hard", "Impossible", "Custom"]:
            self.port.set("difficulty", diff)

    def set_game_over(self, status: bool = True):
        self.port.set("game_over", status)

    def handle_win_achievements(self, unlocked_achievements: List[Any]):
        """Stores newly unlocked achievements in the state for notification."""
        if not unlocked_achievements:
            return
        new_ach = self.port.get("new_achievements", [])
        for ach in unlocked_achievements:
            new_ach.append(
                {
                    "code": ach.code,
                    "name": ach.name,
                    "icon": ach.icon,
                    "xp": ach.xp_reward,
                }
            )
        self.port.set("new_achievements", new_ach)
