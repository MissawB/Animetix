from typing import Optional

class QuestionFormatter:
    """
    Formate les attributs techniques du moteur Akinetix en questions naturelles.
    Permet de séparer la logique algorithmique de la présentation (i18n ready).
    """
    
    def format(self, attribute: str) -> str:
        """Transforme l'attribut interne en question naturelle."""
        if not attribute:
            return "Es-tu prêt ?"
            
        if ':' not in attribute:
            return f"Est-ce que l'attribut {attribute} est présent ?"

        attr_type, attr_val = attribute.split(':', 1)
        
        if attr_type == 'fine':
            # Conversion snake_case -> Question
            # Ex: hair_is_blue -> Hair is blue ?
            q = attr_val.replace('_', ' ').capitalize()
            if not q.endswith('?'):
                q += " ?"
            return q
            
        mapping = {
            'genre': "Est-ce une œuvre de type {} ?",
            'tag': "Est-ce que l'œuvre possède le tag '{}' ?",
            'studio': "Est-ce que le studio {} a travaillé dessus ?",
            'theme': "Le thème '{}' est-il central ?"
        }
        
        template = mapping.get(attr_type, "L'attribut {} est-il présent ?")
        return template.format(attr_val)
