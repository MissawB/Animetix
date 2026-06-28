import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.ports.game_state_port import GameStatePort

from ...ports.repository_port import RepositoryPort


@dataclass
class BlindTestGameState:
    secret: Optional[str] = None
    video: Optional[str] = None
    type: Optional[str] = None
    sequence: Any = None
    song: Optional[str] = None
    artists: Any = None
    guesses: List[Any] = field(default_factory=list)
    game_over: bool = False
    is_daily: bool = False
    difficulty: str = "Normal"


class BlindTestDomainService:
    def __init__(self, repository: RepositoryPort):
        self.repository = repository
        self._themes = None

    def get_state(self, port: GameStatePort) -> BlindTestGameState:
        """Load the Blind Test state for the current session from the port."""
        return BlindTestGameState(
            secret=port.get("blindtest_secret"),
            video=port.get("blindtest_video"),
            type=port.get("blindtest_type"),
            sequence=port.get("blindtest_sequence"),
            song=port.get("blindtest_song"),
            artists=port.get("blindtest_artists"),
            guesses=port.get("blindtest_guesses", []),
            game_over=port.get("blindtest_game_over", False),
            is_daily=port.get("is_daily", False),
            difficulty=port.get("blindtest_difficulty", "Normal"),
        )

    def save_state(self, port: GameStatePort, state: BlindTestGameState) -> None:
        """Persist the Blind Test state for the current session to the port."""
        port.update(
            {
                "blindtest_secret": state.secret,
                "blindtest_video": state.video,
                "blindtest_type": state.type,
                "blindtest_sequence": state.sequence,
                "blindtest_song": state.song,
                "blindtest_artists": state.artists,
                "blindtest_guesses": state.guesses,
                "blindtest_game_over": state.game_over,
                "is_daily": state.is_daily,
                "blindtest_difficulty": state.difficulty,
            }
        )

    def _get_themes(self):
        if self._themes is None:
            self._themes = self.repository.load_themes()
        return self._themes

    def get_random_theme(self, theme_type: Optional[str] = None) -> Optional[Dict]:
        return self._pick_theme(theme_type)

    def get_daily_theme(self, date_obj) -> Optional[Dict]:
        seed = int(
            hashlib.md5(
                f"blindtest-{date_obj}".encode(), usedforsecurity=False
            ).hexdigest(),
            16,
        )
        return self._pick_theme(seed=seed)

    def _pick_theme(
        self, theme_type: Optional[str] = None, seed: Optional[int] = None
    ) -> Optional[Dict]:
        themes_data = self._get_themes()
        if not themes_data:
            return None

        if seed:
            random.seed(seed)

        anime_ids = sorted(list(themes_data.keys()))
        result = None

        for _ in range(50):
            anime_id = random.choice(anime_ids)
            data = themes_data[anime_id]
            themes = [
                t
                for t in data.get("themes", [])
                if not theme_type or t.get("type") == theme_type
            ]

            if themes:
                theme = random.choice(themes)
                video_url = next(
                    (
                        v["link"]
                        for entry in theme.get("entries", [])
                        for v in entry.get("videos", [])
                        if v.get("link")
                    ),
                    None,
                )
                if video_url:
                    result = {
                        "anime_id": anime_id,
                        "anime_title": data["title"],
                        "song_title": theme["song_title"],
                        "artists": theme["artists"],
                        "type": theme["type"],
                        "sequence": theme.get("sequence"),
                        "video_url": video_url,
                    }
                    break

        if seed:
            random.seed(None)
        return result
