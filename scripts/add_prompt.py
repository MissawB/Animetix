import os

prompt_path = "src/core/domain/services/prompts/prompts.yaml"
with open(prompt_path, "a", encoding="utf-8") as f:
    f.write("""
vs_battle_ai_generator:
  template: |
    Tu es un expert en Powerscaling et membre éminent de VS Battles Wiki.
    Le personnage '{name}' (Franchise: {franchise}) n'a pas encore de fiche officielle.
    Ta mission est de GÉNÉRER une fiche technique crédible en respectant les conventions du site.

    CONSIGNES :
    - TIER : Évalue le niveau de destruction (ex: 10-B pour un humain, 9-B pour un combattant de rue).
    - VITESSE : De Subsonique à Supersonique.
    - CAPACITÉS : Liste ses talents ou particularités.
    - RÉSUMÉ : Présente le personnage de manière épique.

    RÉPONDS UNIQUEMENT EN JSON :
    {
      "name": "{name}",
      "stats": {
        "tier": "...",
        "speed": "...",
        "durability": "...",
        "intelligence": "...",
        "abilities": ["...", "..."]
      },
      "summary": "..."
    }
  system_prompt: "Tu es le Créateur de Profils VS Battles. Tu génères des stats cohérentes basées sur ton immense connaissance des animes."
""")
print("✅ Prompt added successfully.")
