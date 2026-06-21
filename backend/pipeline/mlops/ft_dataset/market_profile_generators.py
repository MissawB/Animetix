# -*- coding: utf-8 -*-
"""Générateurs de profils des marchés français et japonais (pilotés par données).

Q&A expertes par comédien (doubleur/seiyuu), éditeur et plateforme, construites
à partir des bases de marché — aucun helper de texte ni appel LLM.
"""

from ..french_market_db import (
    FRENCH_ANIME_DISTRIBUTORS,
    FRENCH_MANGA_PUBLISHERS,
    FRENCH_VOICE_ACTORS,
)
from ..japanese_market_db import (
    JAPANESE_ANIME_DISTRIBUTORS,
    JAPANESE_MANGA_PUBLISHERS,
)
from ..songs_and_seiyuu_db import SEIYUU_PROFILES as JAPANESE_VOICE_ACTORS


def generate_french_market_profile_instructions():
    """Génère 15 variations de Q&A pour chaque comédien, éditeur et plateforme du marché français (600 instructions)."""
    instructions = []

    # 1. Comédiens de doublage VF (15 * 15 = 225 instructions)
    for actor, data in FRENCH_VOICE_ACTORS.items():
        templates = [
            (
                f"Qui est '{actor}' dans le doublage français d'animés ?",
                f"Dans le doublage VF, '{actor}' est : {data['definition']}. Rôles cultes : {data['examples']}. Parcours : {data['origin']}",
            ),
            (
                f"Présente-moi le parcours de la voix française culte '{actor}'.",
                f"Fiche de doublage - '{actor}' : {data['definition']} Carrière : {data['origin']}. Rôles en VF : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Quels sont les rôles majeurs doublés par '{actor}' en version française ?",
                f"Les doublages de '{actor}' incluent : {data['examples']}. Il/Elle est connu(e) comme : {data['definition']}",
            ),
            (
                f"En tant que spécialiste des voix françaises, que peux-tu me dire sur '{actor}' ?",
                f"Spécialité VF - '{actor}' : {data['definition']} Origines : {data['origin']}. Ses rôles phares : {data['examples']}",
            ),
            (
                f"Pourquoi le doublage de '{actor}' a-t-il tant marqué le public français ?",
                f"Le doublage de '{actor}' est légendaire : {data['impact']} Il/Elle est reconnu(e) en tant que : {data['definition']}",
            ),
            (
                f"Quels personnages célèbres ont la voix française de '{actor}' ?",
                f"Les figures doublées par '{actor}' comprennent : {data['examples']}. Style vocal : {data['origin']}",
            ),
            (
                f"Fais-moi une synthèse complète de la carrière de doublage de '{actor}'.",
                f"Synthèse Doublage - '{actor}' : {data['definition']}. Histoire : {data['origin']}. Rôles repères : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Peux-tu analyser l'importance de '{actor}' pour la VF de nos animés d'enfance ?",
                f"L'importance de '{actor}' en VF est colossale. {data['impact']} Connu pour : {data['definition']}. Rôles majeurs : {data['examples']}",
            ),
            (
                f"Quel a été le rôle de '{actor}' au sein d'AB Production ou du doublage d'animes ?",
                f"'{actor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Parcours : {data['origin']}",
            ),
            (
                f"Donne des détails sur le timbre ou le registre de voix de '{actor}'.",
                f"Le timbre et registre de '{actor}' se caractérisent ainsi : {data['definition']}. Ses rôles phares : {data['examples']}. Style : {data['impact']}",
            ),
            (
                f"Explique comment '{actor}' insuffle de la personnalité à ses doublages en français.",
                f"L'interprétation de '{actor}' se distingue par son énergie : {data['impact']} Notamment à travers : {data['definition']}. Rôles repères : {data['examples']}",
            ),
            (
                f"Quelles sont les séries majeures où l'on peut apprécier le doublage de '{actor}' ?",
                f"On l'entend dans plusieurs animés cultes : {data['examples']}. Profil : {data['definition']}",
            ),
            (
                f"Décris le parcours artistique et le profil vocal de '{actor}'.",
                f"Parcours de '{actor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Rôles majeurs : {data['examples']}",
            ),
            (
                f"Analyse l'importance historique et l'héritage de la voix de '{actor}' pour les otakus français.",
                f"L'héritage de '{actor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Rôles d'enfance : {data['examples']}",
            ),
            (
                f"Qu'est-ce qui rend '{actor}' incontournable dans le paysage du doublage VF ?",
                f"'{actor}' est incontournable en tant que : {data['definition']}. Ses créations populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})

    # 2. Éditeurs de mangas en France (15 * 15 = 225 instructions)
    for publisher, data in FRENCH_MANGA_PUBLISHERS.items():
        templates = [
            (
                f"Qui est l'éditeur français '{publisher}' dans le milieu du manga ?",
                f"Sur le marché français, '{publisher}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}",
            ),
            (
                f"Présente-moi le profil et l'impact sur le marché de l'éditeur '{publisher}'.",
                f"Fiche Éditeur - '{publisher}' : {data['definition']} Création : {data['origin']}. Mangas clés : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Quelles sont les œuvres emblématiques publiées par '{publisher}' en France ?",
                f"Les licences phares éditées par '{publisher}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}",
            ),
            (
                f"En tant que spécialiste du marché du manga en France, que peux-tu me dire sur '{publisher}' ?",
                f"Marché français - '{publisher}' : {data['definition']} Histoire : {data['origin']}. Succès : {data['examples']}",
            ),
            (
                f"Pourquoi l'éditeur '{publisher}' a-t-il rencontré un si grand succès en France ?",
                f"Le succès éditorial de '{publisher}' s'explique par sa ligne éditoriale : {data['impact']} Définition : {data['definition']}",
            ),
            (
                f"Quels mangas célèbres sont publiés sous le label de '{publisher}' ?",
                f"Les titres édités par '{publisher}' comprennent : {data['examples']}. Démarche : {data['origin']}",
            ),
            (
                f"Fais-moi une synthèse complète de l'historique de la maison d'édition '{publisher}'.",
                f"Synthèse Éditeur - '{publisher}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Peux-tu analyser l'importance de '{publisher}' pour la popularisation du manga en France ?",
                f"L'importance de '{publisher}' en France est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}",
            ),
            (
                f"Quel a été le rôle de '{publisher}' dans l'importation de mangas shonen ou seinen ?",
                f"'{publisher}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}",
            ),
            (
                f"Donne des détails sur la ligne éditoriale ou les traductions de '{publisher}'.",
                f"La ligne éditoriale de '{publisher}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}",
            ),
            (
                f"Explique comment '{publisher}' se démarque des autres éditeurs de mangas français.",
                f"La force de '{publisher}' réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}",
            ),
            (
                f"Quels sont les mangas majeurs que l'on doit lire chez '{publisher}' ?",
                f"On peut lire plusieurs œuvres majeures chez cet éditeur : {data['examples']}. Profil : {data['definition']}",
            ),
            (
                f"Décris le parcours d'édition et le profil de '{publisher}'.",
                f"Parcours de '{publisher}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}",
            ),
            (
                f"Analyse l'importance historique et l'héritage de '{publisher}' pour les lecteurs français.",
                f"L'héritage de '{publisher}' est inestimable. {data['impact']} Définition : {data['definition']}. Succès clés : {data['examples']}",
            ),
            (
                f"Qu'est-ce qui rend '{publisher}' incontournable dans les librairies françaises ?",
                f"'{publisher}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})

    # 3. Distributeurs et sites de streaming d'animés (10 * 15 = 150 instructions)
    for distributor, data in FRENCH_ANIME_DISTRIBUTORS.items():
        templates = [
            (
                f"Qu'est-ce que la plateforme ou distributeur français '{distributor}' ?",
                f"Sur le marché français, '{distributor}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}",
            ),
            (
                f"Présente-moi le profil et l'impact sur le streaming ou le physique de '{distributor}'.",
                f"Fiche Distributeur - '{distributor}' : {data['definition']} Lancement : {data['origin']}. Animés : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Quels sont les animés phares diffusés par '{distributor}' en France ?",
                f"Les licences majeures diffusées par '{distributor}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}",
            ),
            (
                f"En tant que spécialiste de la diffusion d'animés en France, que peux-tu me dire sur '{distributor}' ?",
                f"Diffusion France - '{distributor}' : {data['definition']} Contexte : {data['origin']}. Succès : {data['examples']}",
            ),
            (
                f"Pourquoi le service de '{distributor}' s'est-il imposé dans l'Hexagone ?",
                f"Le succès s'explique par sa distribution : {data['impact']} Définition : {data['definition']}",
            ),
            (
                f"Quels animés célèbres sont disponibles chez '{distributor}' ?",
                f"Les titres diffusés par '{distributor}' comprennent : {data['examples']}. Démarche : {data['origin']}",
            ),
            (
                f"Fais-moi une synthèse complète de l'histoire du diffuseur ou distributeur '{distributor}'.",
                f"Synthèse Diffusion - '{distributor}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Peux-tu analyser l'importance de '{distributor}' pour le marché français de la japanimation ?",
                f"L'importance de '{distributor}' en France est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}",
            ),
            (
                f"Quel a été le rôle de '{distributor}' dans le développement du simulcast ou du physique ?",
                f"'{distributor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}",
            ),
            (
                f"Donne des détails sur le mode de fonctionnement ou l'histoire de '{distributor}'.",
                f"Le service de '{distributor}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}",
            ),
            (
                f"Explique comment '{distributor}' a transformé la consommation légale d'animés en France.",
                f"La force réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}",
            ),
            (
                f"Quels sont les animés majeurs que l'on doit regarder chez '{distributor}' ?",
                f"On peut regarder plusieurs œuvres majeures chez ce diffuseur : {data['examples']}. Profil : {data['definition']}",
            ),
            (
                f"Décris le parcours de diffusion et le profil de '{distributor}'.",
                f"Parcours de '{distributor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}",
            ),
            (
                f"Analyse l'importance historique et l'héritage de '{distributor}' pour les passionnés français.",
                f"L'héritage de '{distributor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Succès de diffusion : {data['examples']}",
            ),
            (
                f"Qu'est-ce qui rend '{distributor}' incontournable dans le streaming d'animés moderne ?",
                f"'{distributor}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})

    return instructions


def generate_japanese_market_profile_instructions():
    """Génère 15 variations de Q&A pour chaque comédien (seiyuu), éditeur et plateforme du marché japonais (600 instructions)."""
    instructions = []

    # 1. Seiyuu Japonais (15 * 15 = 225 instructions)
    for actor, data in JAPANESE_VOICE_ACTORS.items():
        templates = [
            (
                f"Qui est '{actor}' dans le doublage japonais d'animés ?",
                f"Dans le doublage japonais (seiyuu), '{actor}' est : {data['definition']}. Doublages cultes : {data['examples']}. Parcours : {data['origin']}",
            ),
            (
                f"Présente-moi le parcours de la voix japonaise (seiyuu) culte '{actor}'.",
                f"Fiche de doublage - '{actor}' : {data['definition']} Carrière : {data['origin']}. Rôles phares : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Quels sont les rôles majeurs doublés par '{actor}' en version originale japonaise ?",
                f"Les doublages originaux de '{actor}' incluent : {data['examples']}. Il/Elle est connu(e) comme : {data['definition']}",
            ),
            (
                f"En tant que spécialiste des seiyuu japonais, que peux-tu me dire sur '{actor}' ?",
                f"Spécialité Seiyuu - '{actor}' : {data['definition']} Origines : {data['origin']}. Ses rôles phares : {data['examples']}",
            ),
            (
                f"Pourquoi le doublage de '{actor}' a-t-il tant marqué le public de la japanimation ?",
                f"Le doublage de '{actor}' est légendaire : {data['impact']} Il/Elle est reconnu(e) en tant que : {data['definition']}",
            ),
            (
                f"Quels personnages célèbres ont la voix originale de '{actor}' ?",
                f"Les figures doublées par '{actor}' comprennent : {data['examples']}. Style vocal : {data['origin']}",
            ),
            (
                f"Fais-moi une synthèse complète de la carrière de seiyuu de '{actor}'.",
                f"Synthèse Seiyuu - '{actor}' : {data['definition']}. Histoire : {data['origin']}. Rôles repères : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Peux-tu analyser l'importance de '{actor}' pour le doublage de nos animés cultes ?",
                f"L'importance de '{actor}' en tant que seiyuu est colossale. {data['impact']} Connu pour : {data['definition']}. Rôles majeurs : {data['examples']}",
            ),
            (
                f"Quel a été le rôle de '{actor}' au sein de l'industrie du doublage au Japon ?",
                f"'{actor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Parcours : {data['origin']}",
            ),
            (
                f"Donne des détails sur le timbre ou le registre de voix de '{actor}'.",
                f"Le timbre et registre de '{actor}' se caractérisent ainsi : {data['definition']}. Ses rôles phares : {data['examples']}. Style : {data['impact']}",
            ),
            (
                f"Explique comment '{actor}' insuffle de la personnalité à ses doublages originaux.",
                f"L'interprétation de '{actor}' se distingue par son énergie : {data['impact']} Notamment à travers : {data['definition']}. Rôles repères : {data['examples']}",
            ),
            (
                f"Quelles sont les séries majeures où l'on peut apprécier le doublage de '{actor}' ?",
                f"On l'entend dans plusieurs animés cultes : {data['examples']}. Profil : {data['definition']}",
            ),
            (
                f"Décris le parcours artistique et le profil vocal de '{actor}'.",
                f"Parcours de '{actor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Rôles majeurs : {data['examples']}",
            ),
            (
                f"Analyse l'importance historique et l'héritage de la voix de '{actor}' pour les passionnés d'animation.",
                f"L'héritage de '{actor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Rôles cultes : {data['examples']}",
            ),
            (
                f"Qu'est-ce qui rend '{actor}' incontournable dans le paysage des seiyuu japonais ?",
                f"'{actor}' est incontournable en tant que : {data['definition']}. Ses créations populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})

    # 2. Éditeurs de mangas au Japon (15 * 15 = 225 instructions)
    for publisher, data in JAPANESE_MANGA_PUBLISHERS.items():
        templates = [
            (
                f"Qui est l'éditeur japonais '{publisher}' dans le milieu du manga ?",
                f"Sur le marché japonais, '{publisher}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}",
            ),
            (
                f"Présente-moi le profil et l'impact sur le marché de l'éditeur japonais '{publisher}'.",
                f"Fiche Éditeur JP - '{publisher}' : {data['definition']} Création : {data['origin']}. Mangas clés : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Quelles sont les œuvres emblématiques publiées par '{publisher}' au Japon ?",
                f"Les licences phares éditées par '{publisher}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}",
            ),
            (
                f"En tant que spécialiste du marché du manga au Japon, que peux-tu me dire sur '{publisher}' ?",
                f"Marché japonais - '{publisher}' : {data['definition']} Histoire : {data['origin']}. Succès : {data['examples']}",
            ),
            (
                f"Pourquoi l'éditeur '{publisher}' a-t-il rencontré un si grand succès au Japon ?",
                f"Le succès éditorial de '{publisher}' s'explique par sa ligne éditoriale : {data['impact']} Définition : {data['definition']}",
            ),
            (
                f"Quels mangas célèbres sont publiés sous le label japonais de '{publisher}' ?",
                f"Les titres édités par '{publisher}' comprennent : {data['examples']}. Démarche : {data['origin']}",
            ),
            (
                f"Fais-moi une synthèse complète de l'historique de la maison d'édition japonaise '{publisher}'.",
                f"Synthèse Éditeur JP - '{publisher}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Peux-tu analyser l'importance de '{publisher}' pour la popularisation du manga au Japon et dans le monde ?",
                f"L'importance de '{publisher}' est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}",
            ),
            (
                f"Quel a été le rôle de '{publisher}' dans l'essor mondial des magazines de prépublication ?",
                f"'{publisher}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}",
            ),
            (
                f"Donne des détails sur la ligne éditoriale ou le style éditorial de '{publisher}'.",
                f"La ligne éditoriale de '{publisher}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}",
            ),
            (
                f"Explique comment '{publisher}' se démarque des autres éditeurs de mangas au Japon.",
                f"La force de '{publisher}' réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}",
            ),
            (
                f"Quels sont les mangas majeurs que l'on doit lire chez l'éditeur japonais '{publisher}' ?",
                f"On peut lire plusieurs œuvres majeures chez cet éditeur : {data['examples']}. Profil : {data['definition']}",
            ),
            (
                f"Décris le parcours d'édition et le profil de '{publisher}' au Japon.",
                f"Parcours de '{publisher}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}",
            ),
            (
                f"Analyse l'importance historique et l'héritage de '{publisher}' pour l'industrie du manga.",
                f"L'héritage de '{publisher}' est inestimable. {data['impact']} Définition : {data['definition']}. Succès clés : {data['examples']}",
            ),
            (
                f"Qu'est-ce qui rend '{publisher}' incontournable dans l'édition de mangas japonaise ?",
                f"'{publisher}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})

    # 3. Distributeurs et sites de diffusion au Japon (10 * 15 = 150 instructions)
    for distributor, data in JAPANESE_ANIME_DISTRIBUTORS.items():
        templates = [
            (
                f"Qu'est-ce que la plateforme, diffuseur ou comité de production japonais '{distributor}' ?",
                f"Sur le marché japonais, '{distributor}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}",
            ),
            (
                f"Présente-moi le profil et l'impact sur la production et la distribution de '{distributor}' au Japon.",
                f"Fiche Diffuseur JP - '{distributor}' : {data['definition']} Lancement : {data['origin']}. Animés : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Quels sont les animés phares produits ou diffusés par '{distributor}' au Japon ?",
                f"Les licences majeures produites ou diffusées par '{distributor}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}",
            ),
            (
                f"En tant que spécialiste de la diffusion d'animés au Japon, que peux-tu me dire sur '{distributor}' ?",
                f"Diffusion Japon - '{distributor}' : {data['definition']} Contexte : {data['origin']}. Succès : {data['examples']}",
            ),
            (
                f"Pourquoi le service ou la diffusion de '{distributor}' s'est-il imposé dans l'archipel ?",
                f"Le succès s'explique par sa distribution : {data['impact']} Définition : {data['definition']}",
            ),
            (
                f"Quels animés célèbres sont disponibles ou diffusés par '{distributor}' ?",
                f"Les titres diffusés par '{distributor}' comprennent : {data['examples']}. Démarche : {data['origin']}",
            ),
            (
                f"Fais-moi une synthèse complète de l'histoire du diffuseur ou producteur japonais '{distributor}'.",
                f"Synthèse Diffusion JP - '{distributor}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}",
            ),
            (
                f"Peux-tu analyser l'importance de '{distributor}' pour l'industrie de la japanimation ?",
                f"L'importance de '{distributor}' au Japon est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}",
            ),
            (
                f"Quel a été le rôle de '{distributor}' dans le développement ou le financement des animés ?",
                f"'{distributor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}",
            ),
            (
                f"Donne des détails sur le mode de fonctionnement ou l'histoire de '{distributor}'.",
                f"Le service de '{distributor}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}",
            ),
            (
                f"Explique comment '{distributor}' a transformé la distribution ou production d'animés au Japon.",
                f"La force réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}",
            ),
            (
                f"Quels sont les animés majeurs que l'on doit regarder issus de '{distributor}' ?",
                f"On peut regarder plusieurs œuvres majeures issues de ce diffuseur/producteur : {data['examples']}. Profil : {data['definition']}",
            ),
            (
                f"Décris le parcours de production ou diffusion et le profil de '{distributor}'.",
                f"Parcours de '{distributor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}",
            ),
            (
                f"Analyse l'importance historique et l'héritage de '{distributor}' pour les passionnés d'animes.",
                f"L'héritage de '{distributor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Succès de diffusion : {data['examples']}",
            ),
            (
                f"Qu'est-ce qui rend '{distributor}' incontournable dans le paysage de la japanimation ?",
                f"'{distributor}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
            ),
        ]
        for q, a in templates:
            instructions.append({"instruction": q, "input": "", "output": a})

    return instructions
