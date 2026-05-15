import random
import json

class ArchetypistPresenter:
    """Helper class to prepare UI data for the Archetypist view."""

    POSITIONS = [
        {"style": "top-[-20px] left-[10%] rotate-[-12deg]", "fly": "fly-top"},
        {"style": "top-[20%] left-[-40px] rotate-[8deg]", "fly": "fly-left"},
        {"style": "bottom-[15%] left-[2%] rotate-[-6deg]", "fly": "fly-left"},
        {"style": "bottom-[-50px] left-[30%] rotate-[15deg]", "fly": "fly-bottom"},
        {"style": "bottom-[5%] right-[25%] rotate-[-10deg]", "fly": "fly-bottom"},
        {"style": "top-[10%] right-[-20px] rotate-[-5deg]", "fly": "fly-right"},
        {"style": "bottom-[25%] right-[-30px] rotate-[12deg]", "fly": "fly-right"},
        {"style": "top-[-40px] right-[20%] rotate-[8deg]", "fly": "fly-top"}
    ]

    CROSS_MEDIA_MAPPING = {
        'Anime': [
            {'label': 'Jeux Vidéo', 'type': 'Game', 'icon': 'bi-controller'},
            {'label': 'Mangas', 'type': 'Manga', 'icon': 'bi-book'},
            {'label': 'Films', 'type': 'Movie', 'icon': 'bi-film'},
        ],
        'Manga': [
            {'label': 'Jeux Vidéo', 'type': 'Game', 'icon': 'bi-controller'},
            {'label': 'Animes', 'type': 'Anime', 'icon': 'bi-tv'},
            {'label': 'Films', 'type': 'Movie', 'icon': 'bi-film'},
        ],
        'Character': [
            {'label': 'Acteurs', 'type': 'Actor', 'icon': 'bi-person-badge'},
            {'label': 'Perso Film', 'type': 'Movie', 'icon': 'bi-film'},
            {'label': 'Perso Jeux', 'type': 'Game', 'icon': 'bi-controller'},
        ]
    }

    @classmethod
    def get_cross_media_options(cls, media_type):
        return cls.CROSS_MEDIA_MAPPING.get(media_type, [])

    @classmethod
    def get_example_covers(cls, pool, limit=8):
        items_with_img = [item for item in pool if item.get('image')]
        if not items_with_img:
            return []
            
        selected = random.sample(items_with_img, min(len(items_with_img), limit))
        
        for i, item in enumerate(selected):
            pos = cls.POSITIONS[i] if i < len(cls.POSITIONS) else {"style": "", "fly": "fly-bottom"}
            item['css_style'] = pos["style"]
            item['fly_class'] = pos["fly"]
            item['animation_delay'] = round((i + 1) * 0.15, 2)
            
        return selected

    @staticmethod
    def build_forge_items(data_dict, limit=500):
        """Helper to build a clean list for JS (used by the Forge)."""
        items = []
        pool = data_dict.get('lookup', []) if data_dict.get('lookup') else [{"title": t} for t in data_dict.get('titles', [])]
        
        title_to_full = data_dict.get('title_to_full_data', {})

        for it in pool:
            title = it.get('title') or it.get('name')
            if not title: continue
            full = title_to_full.get(title, {})
            img = it.get('image') or full.get('image')
            if not img: continue
            
            items.append({
                "title": title,
                "title_native": it.get('title_native') or full.get('title_native') or full.get('title_jp') or "",
                "image": img
            })
            if len(items) >= limit: break
        
        # Fallback if few images found
        if len(items) < 10:
            for it in pool[:limit]:
                title = it.get('title') or it.get('name')
                if not title: continue
                if any(x['title'] == title for x in items): continue
                full = title_to_full.get(title, {})
                items.append({
                    "title": title,
                    "title_native": it.get('title_native') or full.get('title_native') or full.get('title_jp') or "",
                    "image": it.get('image') or full.get('image') or ""
                })
                if len(items) >= limit: break
        return items
