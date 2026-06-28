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

    def format(self, attribute: str) -> str:
        """Transforme l'attribut interne en question naturelle."""
        if not attribute:
            return "Es-tu prêt ?"

        if ":" not in attribute:
            return f"Est-ce que l'attribut {attribute} est présent ?"

        attr_type, attr_val = attribute.split(":", 1)

        if attr_type == "fine":
            # Conversion snake_case -> Question
            # Ex: hair_is_blue -> Hair is blue ?
            q = attr_val.replace("_", " ").capitalize()
            if not q.endswith("?"):
                q += " ?"
            return q

        mapping = {
            "genre": "Est-ce une œuvre de type {} ?",
            "tag": "Est-ce que l'œuvre possède le tag '{}' ?",
            "studio": "Est-ce que le studio {} a travaillé dessus ?",
            "theme": "Le thème '{}' est-il central ?",
        }

        template = mapping.get(attr_type, "L'attribut {} est-il présent ?")
        return template.format(attr_val)
