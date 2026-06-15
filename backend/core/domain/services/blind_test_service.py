import random
import hashlib
from typing import Optional, Dict
from ...ports.repository_port import RepositoryPort

class BlindTestDomainService:
    def __init__(self, repository: RepositoryPort):
        self.repository = repository
        self._themes = None

    def _get_themes(self):
        if self._themes is None:
            self._themes = self.repository.load_themes()
        return self._themes

    def get_random_theme(self, theme_type: Optional[str] = None) -> Optional[Dict]:
        return self._pick_theme(theme_type)

    def get_daily_theme(self, date_obj) -> Optional[Dict]:
        seed = int(hashlib.md5(f"blindtest-{date_obj}".encode(), usedforsecurity=False).hexdigest(), 16)
        return self._pick_theme(seed=seed)

    def _pick_theme(self, theme_type: Optional[str] = None, seed: Optional[int] = None) -> Optional[Dict]:
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
            themes = [t for t in data.get('themes', []) if not theme_type or t.get('type') == theme_type]
            
            if themes:
                theme = random.choice(themes)
                video_url = next((v['link'] for entry in theme.get('entries', []) 
                                 for v in entry.get('videos', []) if v.get('link')), None)
                if video_url:
                    result = {
                        'anime_id': anime_id,
                        'anime_title': data['title'],
                        'song_title': theme['song_title'],
                        'artists': theme['artists'],
                        'type': theme['type'],
                        'video_url': video_url
                    }
                    break
        
        if seed:
            random.seed(None)
        return result
