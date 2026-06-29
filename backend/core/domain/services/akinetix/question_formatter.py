import random
from typing import Any

# Some catalogue entries have polluted micro_tags (e.g. an inference error string
# stored as a tag when the offline tagging pipeline ran without a compute unit).
# Such tags must never surface as questions like "possède le tag '<error>'".
_INVALID_TAG_MARKERS = (
    "aucune unité",
    "n'est disponible",
    "ollama",
    "no computational",
    "désolé",
    "sorry",
    "erreur",
    "error",
)


def is_valid_micro_tag(tag: Any) -> bool:
    """A real micro-tag is a short thematic label, not a sentence or error."""
    if not isinstance(tag, str):
        return False
    t = tag.strip()
    if not t or len(t) > 50:
        return False
    low = t.lower()
    return not any(marker in low for marker in _INVALID_TAG_MARKERS)


class QuestionFormatter:
    """
    Formate les attributs techniques du moteur Akinetix en questions naturelles.
    Permet de séparer la logique algorithmique de la présentation (i18n ready).
    """

    # Plusieurs tournures par type pour éviter la monotonie : une variante est
    # tirée au hasard à chaque question (le texte est figé ensuite dans l'état).
    TEMPLATES = {
        "genre": [
            "Est-ce une œuvre de type {} ?",
            "Le genre {} colle-t-il ?",
            "On est plutôt sur du {} ?",
            "Dirais-tu que c'est du {} ?",
            "Y a-t-il une dimension {} ?",
        ],
        "tag": [
            "Y a-t-il une notion de « {} » ?",
            "Le thème « {} » est-il présent ?",
            "Ça parle de « {} » ?",
            "Trouve-t-on du « {} » là-dedans ?",
            "L'élément « {} » est-il là ?",
        ],
        "studio": [
            "Est-ce que le studio {} a travaillé dessus ?",
            "C'est signé {} ?",
            "Le studio {} est-il derrière l'œuvre ?",
        ],
        "theme": [
            "Le thème « {} » est-il central ?",
            "Est-ce centré sur « {} » ?",
            "« {} » est-il au cœur de l'œuvre ?",
        ],
        # attr_val est déjà un fragment prêt : "avant 1990" / "dans les années 2010".
        "era": [
            "Est-ce sorti {} ?",
            "L'œuvre est-elle sortie {} ?",
        ],
    }

    FINE_TEMPLATES = [
        "{q} ?",
        "Ton personnage {ql} ?",
        "Est-ce que ton perso {ql} ?",
        "Dirais-tu qu'il/elle {ql} ?",
    ]

    def format(self, attribute: str) -> str:
        """Transforme l'attribut interne en question naturelle (phrasé varié)."""
        if not attribute:
            return "Es-tu prêt ?"

        if ":" not in attribute:
            return f"Est-ce que l'attribut {attribute} est présent ?"

        attr_type, attr_val = attribute.split(":", 1)

        if attr_type == "fine":
            # Trait perso en snake_case français, ex: a_des_cheveux_blonds.
            phrase = attr_val.replace("_", " ").strip()
            template = random.choice(self.FINE_TEMPLATES)  # nosec B311
            return template.format(q=phrase.capitalize(), ql=phrase.lower())

        variants = self.TEMPLATES.get(attr_type)
        if not variants:
            return f"L'attribut {attr_val} est-il présent ?"
        return random.choice(variants).format(attr_val)  # nosec B311
