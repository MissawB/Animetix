# -*- coding: utf-8 -*-
import os
import sys
import json
import urllib.request
import urllib.error

# Force UTF-8 for console output on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Root detection
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

print("Initializing Synthetic Gold Dataset Generator...")

try:
    from pipeline.mlops.french_market_db import FRENCH_VOICE_ACTORS
    from pipeline.mlops.songs_and_seiyuu_db import SEIYUU_PROFILES, ANIME_SONGS_AND_SINGERS
    from pipeline.mlops.magazines_and_awards_db import SERIALIZATION_MAGAZINES, POP_CULTURE_AWARDS
except ImportError as e:
    print(f"Import error: {e}. Attempting manual path injection...")
    sys.path.insert(0, os.path.join(BASE_DIR, "src", "pipeline", "mlops"))
    from french_market_db import FRENCH_VOICE_ACTORS
    from songs_and_seiyuu_db import SEIYUU_PROFILES, ANIME_SONGS_AND_SINGERS
    from magazines_and_awards_db import SERIALIZATION_MAGAZINES, POP_CULTURE_AWARDS

# List of rich relational facts to synthesize
FACTS = [
    # French Voice Actors
    {
        "fact": "Brigitte Lecordier est la voix française d'enfance emblématique de Son Goku, Son Gohan et Son Goten dans la saga Dragon Ball.",
        "domain": "voice_actors_vf",
        "difficulty": "easy",
        "query_type": "standard",
        "expected_title": "Dragon Ball",
        "expected_id": "223"
    },
    {
        "fact": "Alexis Tomassian prête sa voix française cultissime à Light Yagami dans l'anime de thriller psychologique Death Note.",
        "domain": "voice_actors_vf",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Death Note",
        "expected_id": "1535"
    },
    {
        "fact": "Geneviève Doang est la voix française de Mikasa Ackerman dans l'adaptation animée de L'Attaque des Titans.",
        "domain": "voice_actors_vf",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Attack on Titan",
        "expected_id": "16498"
    },
    # Seiyuu
    {
        "fact": "Yuki Kaji prête sa voix originale japonaise (seiyuu) au protagoniste Eren Jäger dans L'Attaque des Titans et à Koichi Hirose dans JoJo's Bizarre Adventure.",
        "domain": "seiyuu",
        "difficulty": "hard",
        "query_type": "graph",
        "expected_title": "Multiple",
        "expected_id": "0"
    },
    {
        "fact": "Rie Takahashi est la doubleuse japonaise (seiyuu) d'Emilia dans Re:Zero et de Megumin dans KonoSuba.",
        "domain": "seiyuu",
        "difficulty": "hard",
        "query_type": "graph",
        "expected_title": "Multiple",
        "expected_id": "0"
    },
    # Anisongs
    {
        "fact": "L'artiste emblématique Aimer interprète le générique d'ouverture Zankyou Sancka pour l'arc du Quartier des Plaisirs de l'anime Demon Slayer.",
        "domain": "anisongs",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Demon Slayer",
        "expected_id": "38000"
    },
    {
        "fact": "Le groupe de rock japonais FLOW chante les openings mythiques GO!!! et Sign de l'anime Naruto Shippuden.",
        "domain": "anisongs",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Naruto",
        "expected_id": "20"
    },
    # Magazines & Awards
    {
        "fact": "Le prestigieux Prix culturel Osamu Tezuka a récompensé le manga chef-d'œuvre Monster de Naoki Urasawa en 1999.",
        "domain": "magazines",
        "difficulty": "hard",
        "query_type": "cross-media",
        "expected_title": "Monster",
        "expected_id": "19"
    },
    {
        "fact": "Le manga mythique Slam Dunk d'Takehiko Inoue a été prépublié au Japon dans le célèbre magazine Weekly Shōnen Jump.",
        "domain": "magazines",
        "difficulty": "medium",
        "query_type": "standard",
        "expected_title": "Slam Dunk",
        "expected_id": "170"
    }
]

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

def ask_ollama(prompt: str) -> str:
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": "Tu es un assistant expert en structuration de données de pop culture japonaise. Réponds exclusivement en JSON valide."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Ollama API Error or Timeout: {e}")
        return ""

synthetic_gold_dataset = []

print(f"Generating synthetic QA pairs for {len(FACTS)} relational motifs...")

for i, entry in enumerate(FACTS):
    fact = entry["fact"]
    print(f"\n[{i+1}/{len(FACTS)}] Synthesizing: '{fact}'")
    
    prompt = f"""
Basé sur le fait véridique suivant en français :
"{fact}"

Génère une question RAG en français naturel et sa réponse exacte associée.
Tu dois renvoyer STRICTEMENT un objet JSON avec la structure exacte suivante :
{{
  "query": "La question posée de manière fluide en français",
  "ground_truth": "La réponse précise contenant le fait historique ou la relation"
}}

Règles critiques :
- N'invente aucun fait en dehors de la phrase fournie.
- La sortie doit être exclusivement du JSON valide, sans aucune phrase d'introduction ni de conclusion.
"""
    
    response_json = ""
    success = False
    
    # Try calling Ollama llama3
    response_raw = ask_ollama(prompt)
    if response_raw:
        try:
            parsed = json.loads(response_raw)
            if "query" in parsed and "ground_truth" in parsed:
                query = parsed["query"]
                ground_truth = parsed["ground_truth"]
                success = True
                print(" -> Success via Ollama llama3!")
        except Exception as pe:
            print(f" -> Parse error: {pe}")
            
    # Safe fallback if LLM offline or chokes
    if not success:
        print(" -> Fallback: Generating programmatic QA pair.")
        if entry["domain"] == "voice_actors_vf":
            query = f"Qui est le comédien ou la comédienne de doublage français qui prête sa voix à {entry['expected_title']} dans la VF ?"
            ground_truth = fact
        elif entry["domain"] == "seiyuu":
            query = f"Quels personnages célèbres d'animes sont doublés en version originale japonaise par la même voix (seiyuu) ?"
            ground_truth = fact
        elif entry["domain"] == "anisongs":
            query = f"Qui interprète la chanson ou l'opening de l'anime {entry['expected_title']} ?"
            ground_truth = fact
        else:
            query = f"Dans quel magazine ou avec quel prix est lié le manga {entry['expected_title']} ?"
            ground_truth = fact

    # Structure into final RAGAS-ready gold record
    record = {
        "query": query,
        "expected_id": entry["expected_id"],
        "expected_title": entry["expected_title"],
        "is_architectural": entry["difficulty"] == "hard",
        "query_type": entry["query_type"],
        "ground_truth": ground_truth,
        "domain": entry["domain"],
        "difficulty": entry["difficulty"],
        "contexts": [fact]
    }
    
    synthetic_gold_dataset.append(record)

# Output directory and write
output_dir = os.path.join(BASE_DIR, "data", "mlops")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "synthetic_gold_dataset.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(synthetic_gold_dataset, f, indent=2, ensure_ascii=False)

print(f"\n✅ Generation complete! Saved exactly {len(synthetic_gold_dataset)} records to {output_path}")
