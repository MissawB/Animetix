import yaml

prompt_path = "backend/core/domain/services/prompts/prompts.yaml"
with open(prompt_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

data["vs_battle_ai_generator"] = {
    "template": """Tu es un expert en Powerscaling et membre éminent de VS Battles Wiki.
Le personnage '{name}' (Franchise: {franchise}) n'a pas de fiche officielle.
GÉNÈRE une fiche technique crédible en respectant les conventions du site.

CONSIGNES :
- tier : Évalue le niveau (ex: 10-B pour humain, 9-B pour combattant, 8-C pour monstre).
- speed : De "Subsonic" à "FTL" ou "Immeasurable".
- abilities : Liste 3 talents ou particularités majeurs.

TU DOIS RÉPONDRE EXCLUSIVEMENT AVEC UN OBJET JSON VALIDE, SANS AUCUN AUTRE TEXTE NI BALISE MARKDOWN.
{{
  "name": "{name}",
  "stats": {{
    "tier": "...",
    "speed": "...",
    "durability": "...",
    "intelligence": "...",
    "abilities": ["...", "..."]
  }},
  "summary": "..."
}}""",
    "system_prompt": "Tu es le Créateur de Profils VS Battles. Tu génères du JSON valide sans markdown.",
}

with open(prompt_path, "w", encoding="utf-8") as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
print("✅ Prompt vs_battle_ai_generator updated successfully via YAML dump.")
