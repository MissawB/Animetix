import numpy as np
import orjson
import os
import random
import requests
import re
import hashlib
import base64
import torch
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from chromadb import PersistentClient
from django.core.cache import cache
from sentence_transformers import SentenceTransformer, CrossEncoder

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    "Anime": {"Easy": 100, "Normal": 300, "Hard": 800, "Impossible": None},
    "Manga": {"Easy": 100, "Normal": 300, "Hard": 800, "Impossible": None},
    "Character": {"Easy": 250, "Normal": 600, "Hard": 1400, "Impossible": None}
}

# --- DICTIONNAIRE DE TRADUCTIONS ---
TRANSLATIONS = {
    'Français': {
        'nav_home': 'Accueil', 'nav_daily': 'Défi du jour', 'nav_leaderboard': 'Classement',
        'nav_latent': 'Espace Latent', 'nav_grimoire': 'Grimoire', 'nav_settings': 'Paramètres',
        'nav_anime': 'Anime', 'nav_manga': 'Livre', 'nav_perso': 'Perso',
        'nav_difficulty': 'Difficulté', 'nav_lang': 'Langage', 'nav_appearance': 'Apparence',
        'theme_light': 'Clair', 'theme_dark': 'Sombre', 'theme_auto': 'Auto',
        'nav_anime_full': 'ANIME', 'nav_manga_full': 'LIVRE', 'nav_perso_full': 'PERSO',
        'nav_paradox': 'Le Paradoxe', 'nav_archetypist': 'La Forge', 'nav_undercover': 'Undercover',
        'mode_classic_title': 'Animetix Classic', 'mode_classic_desc': 'Trouvez le titre mystère par ressemblance sémantique.',
        'mode_emoji_title': 'Emoji Decode', 'mode_emoji_desc': 'Déchiffrez l\'œuvre derrière les emojis générés par l\'IA.',
        'mode_animinator_title': 'Animinator', 'mode_animinator_desc': 'Posez des questions libres à l\'Oracle pour deviner l\'œuvre.',
        'mode_akinetix_title': 'Akinetix', 'mode_akinetix_desc': 'Pensez à une œuvre, l\'IA tentera de la deviner.',
        'mode_paradox_title': 'Le Paradoxe', 'mode_paradox_desc': 'Identifiez l\'intrus parmi trois propositions thématiques.',
        'btn_start_game': 'Lancer la partie', 'btn_start_party': 'Mode Party', 'placeholder_guess': 'Entrez un titre...',
        'btn_guess': 'Proposer', 'btn_reveal': 'Révéler', 'btn_abandon': 'Abandonner',
        'table_guess': 'Vos essais', 'hints_available': 'Indices débloqués',
        'game_over_win': 'VICTOIRE !', 'game_over_loss': 'DÉFAITE',
        'hint_origin': 'Origine',
        'mode_undercover_title': 'Undercover', 'mode_undercover_desc': 'Débusquez l\'intrus parmi vous avec des mots-clés.',
        'mode_codemanga_title': 'Code Manga', 'mode_codemanga_desc': 'Débusquez les agents secrets de votre équipe avant l\'adversaire.',
        'mode_blindtest_title': 'Blind Test', 'mode_blindtest_desc': 'Devinez l\'animé à partir de son opening ou ending.',
    },
    'English': {
        'nav_home': 'Home', 'nav_daily': 'Daily Challenge', 'nav_leaderboard': 'Leaderboard',
        'nav_latent': 'Latent Space', 'nav_grimoire': 'Grimoire', 'nav_settings': 'Settings',
        'nav_anime': 'Anime', 'nav_manga': 'Book', 'nav_perso': 'Char',
        'nav_difficulty': 'Difficulty', 'nav_lang': 'Language', 'nav_appearance': 'Appearance',
        'theme_light': 'Light', 'theme_dark': 'Dark', 'theme_auto': 'Auto',
        'nav_anime_full': 'ANIME', 'nav_manga_full': 'BOOK', 'nav_perso_full': 'CHAR',
        'nav_paradox': 'The Paradox', 'nav_archetypist': 'The Forge', 'nav_undercover': 'Undercover',
        'mode_classic_title': 'Animetix Classic', 'mode_classic_desc': 'Find the secret title by semantic similarity.',
        'mode_emoji_title': 'Emoji Decode', 'mode_emoji_desc': 'Decode the work behind AI-generated emojis.',
        'mode_animinator_title': 'Animinator (Oracle)', 'mode_animinator_desc': 'Ask the Oracle questions to find the secret.',
        'mode_akinetix_title': 'Akinetix (The Guesser)', 'mode_akinetix_desc': 'Think of a work, the AI will try to guess it.',
        'mode_paradox_title': 'The Paradox', 'mode_paradox_desc': 'Identify the intruder among three thematic options.',
        'btn_start_game': 'Start Game', 'btn_start_party': 'Party Mode', 'placeholder_guess': 'Enter a title...',
        'btn_guess': 'Guess', 'btn_reveal': 'Reveal', 'btn_abandon': 'Give up',
        'table_guess': 'Your guesses', 'hints_available': 'Unlocked hints',
        'game_over_win': 'VICTORY!', 'game_over_loss': 'DEFEAT',
        'hint_origin': 'Origin',
        'mode_undercover_title': 'Undercover', 'mode_undercover_desc': 'Find the intruder among you using keywords.',
        'mode_codemanga_title': 'Code Manga', 'mode_codemanga_desc': 'Find your team\'s secret agents before the opponent.',
        'mode_blindtest_title': 'Blind Test', 'mode_blindtest_desc': 'Guess the anime from its opening or ending.',
    }
}

# --- 1. ANIMETIX DATA & INFRA SERVICE ---
class AnimetixService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnimetixService, cls).__new__(cls)
            cls._instance.data = {}
            # Correction : Utilisation d'un chemin relatif robuste
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_file_dir))
            cls._instance.chroma_client = PersistentClient(path=os.path.join(project_root, "data", "chroma_db"))
            print("🧠 Loading Reranker (INT8 Quantized)...")
            cls._instance.reranker = CrossEncoder('BAAI/bge-reranker-base')
            cls._instance.reranker.model = torch.quantization.quantize_dynamic(
                cls._instance.reranker.model, {torch.nn.Linear}, dtype=torch.qint8
            )
        return cls._instance

    def get_chroma_collection(self, name):
        return self.chroma_client.get_or_create_collection(name=name)

    def get_nearest_neighbors(self, collection_name, item_id, n_results=5):
        """Recherche les voisins les plus proches dans ChromaDB."""
        try:
            coll = self.get_chroma_collection(collection_name)
            # On récupère l'embedding de l'item source
            item_data = coll.get(ids=[str(item_id)], include=['embeddings'])
            embeddings = item_data.get('embeddings')
            if embeddings is None or len(embeddings) == 0:
                return None
            # On cherche les voisins
            return coll.query(query_embeddings=embeddings, n_results=n_results)
        except Exception as e:
            print(f"Chroma Nearest Error: {e}")
            return None

    def load_data(self, media_type):
        if media_type in self.data: return self.data[media_type]
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_file_dir))
        
        db_files = {
            'Anime': 'data/processed/clean_root_animes.json', 
            'Manga': 'data/processed/clean_root_mangas.json', 
            'Character': 'data/processed/filtered_characters.json',
            'Movie': 'data/processed/clean_root_movies.json',
            'Game': 'data/processed/clean_root_games.json',
            'Actor': 'data/processed/clean_root_actors.json'
        }
        coll_names = {
            'Anime': 'anime_thematic', 
            'Manga': 'manga_thematic', 
            'Character': 'character_vibe',
            'Movie': 'movie_thematic', # Hypothèse sur le nom, à vérifier ou créer
            'Game': 'game_thematic',
            'Actor': 'actor_vibe'
        }
        
        try:
            # On vérifie si le type est supporté
            if media_type not in db_files:
                return None

            # Tentative de récupération des embeddings via Chroma
            try:
                coll = self.get_chroma_collection(coll_names[media_type])
                res = coll.get(include=['metadatas']) # On n'a plus besoin des embeddings ici
            except:
                # Fallback si collection inexistante
                res = {"metadatas": []}

            db_path = os.path.join(project_root, db_files[media_type])
            with open(db_path, 'rb') as f: db_content = orjson.loads(f.read())
            
            self.data[media_type] = {
                "lookup": res['metadatas'], 
                "db": db_content
            }
            d = self.data[media_type]
            
            d["title_to_full_data"] = {str(item.get('title') or item.get('name')): item for item in d["db"]}
            d["titles"] = [str(item.get('title') or item.get('name')) for item in d["db"]]
            d["title_to_index"] = {t: i for i, t in enumerate(d["titles"])}
            d["id_to_full_data"] = {str(item['id']): item for item in d["db"]}

            # Optimisation Autocomplete : Pré-calcul de la liste JSON
            autocomplete_items = []
            for item in d['lookup']:
                title = item.get('title')
                if title in d['title_to_full_data']:
                    full = d['title_to_full_data'][title]
                    autocomplete_items.append({
                        'title': title,
                        'title_english': full.get('title_english'),
                        'image': full.get('image')
                    })
            d["autocomplete_json"] = orjson.dumps(autocomplete_items).decode('utf-8')
            
            return d
        except Exception as e: print(f"Error loading {media_type}: {e}"); return None

# --- 2. AGENTIC AI SERVICE (ReAct Pattern) ---
class LangChainService:
    def __init__(self):
        self.brain_url = os.getenv("BRAIN_API_URL")

    def _generate_via_brain(self, prompt, system_prompt="You are a helpful assistant."):
        """Appelle Llama 3.2 via l'API Brain."""
        if not self.brain_url:
            return None
        try:
            response = requests.post(f"{self.brain_url}/generate", json={
                "prompt": prompt,
                "system_prompt": system_prompt
            }, timeout=30)
            if response.status_code == 200:
                return response.json()["text"]
        except Exception as e:
            print(f"Brain LLM Error: {e}")
        return None

    def _safe_json_parse(self, text, default_reasoning="Analyse Indisponible", default_scenario="..."):
        """Extrait les champs avec une tolérance maximale aux erreurs de format."""
        if not text:
            return {"reasoning": default_reasoning, "scenario": default_scenario}

        try:
            clean_json = text[text.find('{'):text.rfind('}')+1]
            clean_json = clean_json.replace('\n', ' ').replace('\r', ' ')
            parsed = orjson.loads(clean_json)
            r = parsed.get('reasoning') or parsed.get('explanation')
            s = parsed.get('scenario') or parsed.get('synopsis')
            if r and s: return {"reasoning": r, "scenario": s}
        except: pass

        r_match = re.search(r'["\']?reasoning["\']?\s*:\s*["\'](.*?)["\'](?=,|$|\s*})', text, re.DOTALL | re.IGNORECASE)
        s_match = re.search(r'["\']?scenario["\']?\s*:\s*["\'](.*?)["\'](?=,|$|\s*})', text, re.DOTALL | re.IGNORECASE)

        reasoning = r_match.group(1) if r_match else ""
        scenario = s_match.group(1) if s_match else ""

        if not reasoning or len(reasoning) < 5:
            if "parce que" in text.lower() or "commun" in text.lower():
                reasoning = text[:300].split('}')[0].strip(' "{}\n')
            else:
                reasoning = default_reasoning

        if not scenario or len(scenario) < 10:
            scenario = text.split('scenario')[-1].strip(' ":{}\n') if 'scenario' in text else text   

        return {
            "reasoning": reasoning.replace('\\n', '\n').replace('\\"', '"').strip(),
            "scenario": scenario.replace('\\n', '\n').replace('\\"', '"').strip()
        }

    def generate_scenario_advanced(self, media_type, item_A, item_B, language):
        icon = "🦙"
        label_A = item_A.get('title') or item_A.get('name') or "Entité A"
        label_B = item_B.get('title') or item_B.get('name') or "Entité B"

        system_prompt = f"Tu es un expert Concept Creator spécialisé en {media_type}. Réponds UNIQUEMENT par un objet JSON."
        user_prompt = f"""
        MISSION : Fusionne l'univers de {label_A} et {label_B}.
        LANGUE : {language}. Pas de noms cités.
        JSON STRICT: {{"reasoning": "logique {icon}", "scenario": "histoire"}}
        """
        res_text = self._generate_via_brain(user_prompt, system_prompt)
        return self._safe_json_parse(res_text, f"Analyse Llama {icon}", "Fusion en cours...")        

    def generate_paradox_logic(self, media_type, item_A, item_B, item_I, language):
        icon = "🧩"
        label_A = item_A.get('title') or item_A.get('name')
        label_B = item_B.get('title') or item_B.get('name')
        label_I = item_I.get('title') or item_I.get('name')

        system_prompt = f"Tu es un expert Concept Creator. Ta mission est d'expliquer pourquoi '{label_I}' est l'intrus par rapport à '{label_A}' et '{label_B}'."
        user_prompt = f"""
        ANALYSE CES 3 ÉLÉMENTS :
        1. '{label_A}' : {item_A.get('description', '')[:200]}
        2. '{label_B}' : {item_B.get('description', '')[:200]}
        3. INTRUS : '{label_I}' : {item_I.get('description', '')[:200]}

        MISSION :
        - Dans "reasoning" : Explique spécifiquement pourquoi '{label_A}' et '{label_B}' sont similaires et pourquoi '{label_I}' est différent.
        - Dans "scenario" : Décris le point commun de '{label_A}' et '{label_B}' sans les nommer.    

        RÉPONDS UNIQUEMENT AU FORMAT JSON :
        {{
            "reasoning": "Ton explication ici {icon}",
            "scenario": "Ton synopsis ici"
        }}
        """
        res_text = self._generate_via_brain(user_prompt, system_prompt)
        return self._safe_json_parse(res_text, f"L'IA n'a pas pu justifier ce choix. {icon}", res_text)

    def generate_undercover_clue(self, media_type, item_A, item_B, language):
        prompt = f"Donne un seul mot-clé thématique commun à ces deux {media_type} : '{item_A}' et '{item_B}'. Ne cite aucun nom."
        res = self._generate_via_brain(prompt)
        return res if res else "Mystère..."

    def explain_undercover(self, maj_titles, maj_tags, intruder_title, intruder_tags, language):     
        icon = "🦙"
        prompt = f"""
        Groupe d'entités : {', '.join(maj_titles)}.
        L'intrus : {intruder_title}.

        Explique brièvement pourquoi c'est l'intrus.
        Réponds UNIQUEMENT au format JSON suivant :
        {{
            "reasoning": "Analyse thématique {icon}",
            "explanation": "ton explication courte en {language}"
        }}
        """
        res_text = self._generate_via_brain(prompt, "Tu es un expert en analyse d'animés.")
        if res_text:
            try:
                json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
                if json_match:
                    return orjson.loads(json_match.group(0))
            except: pass
        return {"reasoning": f"Erreur {icon}", "explanation": "Analyse non disponible."}

    def generate_emojis(self, media_type, title, description):
        """Génère une suite d'emojis pour représenter l'œuvre."""
        prompt = f"Donne une suite de 3 à 5 emojis qui représentent le mieux {media_type} '{title}'. Description: {description[:200]}. Réponds UNIQUEMENT avec les emojis."
        res = self._generate_via_brain(prompt)
        return res if res else "❓❓❓"

def check_achievements(user, action_type, context=None):
    """Placeholder pour éviter l'ImportError."""
    pass

# --- 3. BLIND TEST SERVICE ---
class BlindTestService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BlindTestService, cls).__new__(cls)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_file_dir))
            cls._instance.themes_path = os.path.join(project_root, 'data', 'processed', 'anime_themes.json')
            cls._instance.themes = {}
            cls._instance._load_themes()
        return cls._instance

    def _load_themes(self):
        if os.path.exists(self.themes_path):
            try:
                with open(self.themes_path, 'rb') as f:
                    self.themes = orjson.loads(f.read())
            except Exception as e:
                print(f"Error loading themes: {e}")
                self.themes = {}

    def get_random_theme(self, theme_type=None):
        """Retourne un thème aléatoire.
        theme_type: 'OP' ou 'ED'
        """
        return self._pick_theme(theme_type)

    def get_daily_theme(self, date_obj):
        """Retourne le thème du jour basé sur la date."""
        seed = int(hashlib.md5(f"blindtest-{date_obj}".encode()).hexdigest(), 16)
        return self._pick_theme(seed=seed)

    def _pick_theme(self, theme_type=None, seed=None):
        if not self.themes: return None
        if seed: random.seed(seed)
        
        anime_ids = list(self.themes.keys())
        anime_ids.sort() # Ensure deterministic order for seeding
        
        result = None
        for _ in range(50):
            anime_id = random.choice(anime_ids)
            data = self.themes[anime_id]
            themes = data.get('themes', [])
            if theme_type:
                themes = [t for t in themes if t.get('type') == theme_type]
            
            if themes:
                theme = random.choice(themes)
                video_url = None
                for entry in theme.get('entries', []):
                    for video in entry.get('videos', []):
                        if video.get('link'):
                            video_url = video['link']
                            break
                    if video_url: break
                
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
        
        if seed: random.seed(None)
        return result

# --- 4. COVER TEST SERVICE ---
class CoverTestService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CoverTestService, cls).__new__(cls)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_file_dir))
            cls._instance.covers_path = os.path.join(project_root, 'data', 'processed', 'manga_covers.json')
            cls._instance.covers = {}
            cls._instance._load_covers()
        return cls._instance

    def _load_covers(self):
        if os.path.exists(self.covers_path):
            try:
                with open(self.covers_path, 'rb') as f:
                    self.covers = orjson.loads(f.read())
            except Exception as e:
                print(f"Error loading covers: {e}")
                self.covers = {}

    def get_random_cover(self, locale=None):
        """Retourne une cover aléatoire.
        locale: 'ja' ou 'fr'
        """
        return self._pick_cover(locale)

    def get_daily_cover(self, date_obj):
        """Retourne la cover du jour basée sur la date."""
        seed = int(hashlib.md5(f"covertest-{date_obj}".encode()).hexdigest(), 16)
        return self._pick_cover(seed=seed)

    def _pick_cover(self, locale=None, seed=None):
        if not self.covers: return None
        if seed: random.seed(seed)
        
        manga_ids = list(self.covers.keys())
        manga_ids.sort()
        
        result = None
        for _ in range(50):
            manga_id = random.choice(manga_ids)
            data = self.covers[manga_id]
            covers_dict = data.get('covers', {})
            
            locs = [locale] if locale else ['ja', 'fr']
            random.shuffle(locs)
            
            for loc in locs:
                variant_list = covers_dict.get(loc, [])
                if variant_list:
                    vol1 = [v for v in variant_list if v.get('volume') == '1']
                    cover = random.choice(vol1) if vol1 else random.choice(variant_list)
                    
                    result = {
                        'manga_id': manga_id,
                        'manga_title': data['title'],
                        'cover_url': cover['url'],
                        'locale': loc,
                        'volume': cover.get('volume')
                    }
                    break
            if result: break
            
        if seed: random.seed(None)
        return result
