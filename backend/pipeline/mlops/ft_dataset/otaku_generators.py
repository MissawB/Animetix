# -*- coding: utf-8 -*-
"""Générateur d'instructions sur le vocabulaire méta otaku, les créateurs et
studios — Q&A bilingues (FR + traduction EN optionnelle via Gemini).
"""

from ..creators_db import CREATORS_AND_STUDIOS
from ..otaku_concepts import OTAKU_VOCABULARY
from .paraphrase import translate_to_english_via_gemini


def generate_otaku_meta_instructions(client=None):
    """Génère un grand nombre de variations expertes de Q&A pour le dictionnaire Otaku de base + les créateurs et studios."""
    otaku_instructions = []

    # 1. Génération par template pour les concepts généraux (15 variations par concept = ~6 000 exemples)
    for idx, (term, data) in enumerate(OTAKU_VOCABULARY.items()):
        if idx % 2 == 1:
            lang = "English"
            definition = translate_to_english_via_gemini(data["definition"], client)
            examples = translate_to_english_via_gemini(data["examples"], client)
            impact = translate_to_english_via_gemini(data["impact"], client)
            origin = translate_to_english_via_gemini(data["origin"], client)

            templates = [
                (
                    f"What does the term '{term}' mean in otaku culture? Provide examples.",
                    f"In otaku culture, the term '{term}' refers to: {definition}. Iconic examples include: {examples}. Cultural impact: {impact}",
                ),
                (
                    f"Give me a clear and precise definition of the concept of '{term}' in anime.",
                    f"The concept of '{term}' is defined as follows in Japanese animation: {definition}. It is illustrated through examples like: {examples}.",
                ),
                (
                    f"As an anime expert, how would you define the concept of '{term}'?",
                    f"As an expert, I define '{term}' as: {definition}. This concept has a strong domain impact: {impact}",
                ),
                (
                    f"Can you explain what '{term}' means to a manga fan?",
                    f"For a manga fan, '{term}' represents: {definition}. It is a common trope characterized by: {origin}",
                ),
                (
                    f"Explain the origin, etymology and deep meaning of the trope '{term}'.",
                    f"The trope '{term}' has a rich history and etymology. Origin: {origin}. Deep meaning: {definition}. This trope is particularly well illustrated by: {examples}.",
                ),
                (
                    f"Where does the word '{term}' used in otaku culture come from and what does it mean?",
                    f"The term '{term}' has its roots in: {origin}. It refers precisely to: {definition}. In the industry, this is explained by: {impact}",
                ),
                (
                    f"What is the history and linguistic root of the concept of '{term}' in manga?",
                    f"The linguistic history of '{term}' dates back to: {origin}. It is a fundamental concept meaning: {definition}",
                ),
                (
                    f"Which characters or works are considered iconic examples of '{term}'?",
                    f"Some of the key examples associated with '{term}' are: {examples}. By definition, this trope represents: {definition}",
                ),
                (
                    f"Give me examples of famous figures illustrating the trope '{term}' in anime.",
                    f"Major figures illustrating the trope '{term}' include: {examples}. This trope is characterized by: {definition} and originates from: {origin}",
                ),
                (
                    f"What are the major works that best represent the concept of '{term}'?",
                    f"The iconic works and characters for '{term}' are: {examples}. This concept is defined as: {definition}",
                ),
                (
                    f"What is the importance and cultural impact of the notion of '{term}' in the animation industry?",
                    f"The cultural impact of '{term}' in the industry is major. {impact} By definition: {definition}. It can be found in: {examples}",
                ),
                (
                    f"Analyze the influence and narrative role of the trope '{term}' in manga.",
                    f"The narrative role of '{term}' is highly influential. {impact} It expresses: {definition}. Examples: {examples}",
                ),
                (
                    f"Why is the concept of '{term}' so popular and recurring in Japanese anime?",
                    f"The popularity of '{term}' is explained by its resonance in pop culture. {impact} Origin: {origin}. Definition: {definition}",
                ),
                (
                    f"Give me a complete and expert summary of the otaku concept of '{term}'.",
                    f"Expert Summary - '{term}': {definition}. Etymological origin: {origin}. Reference works and characters: {examples}. Writing impact: {impact}",
                ),
                (
                    f"What are the key details and analysis to remember about the concept of '{term}'?",
                    f"The essential points to remember about '{term}' are: its definition ({definition}), its historical root ({origin}) and its major incarnations ({examples}).",
                ),
            ]
        else:
            lang = "Français"
            templates = [
                (
                    f"Qu'est-ce que le terme '{term}' dans la culture otaku ? Cite des exemples.",
                    f"Dans la culture otaku, le terme '{term}' désigne : {data['definition']}. Parmi les exemples emblématiques, on peut citer : {data['examples']}. Impact culturel : {data['impact']}",
                ),
                (
                    f"Donne-moi une définition claire et précise du concept de '{term}' dans les animés.",
                    f"Le concept de '{term}' se définit comme suit dans l'animation japonaise : {data['definition']}. On l'illustre à travers des exemples comme : {data['examples']}.",
                ),
                (
                    f"En tant qu'expert de la japanimation, comment définirais-tu le concept de '{term}' ?",
                    f"En tant qu'expert, je définis '{term}' par : {data['definition']}. Cette notion a un fort impact de domaine : {data['impact']}",
                ),
                (
                    f"Peux-tu m'expliquer ce que signifie '{term}' pour un passionné de mangas ?",
                    f"Pour un passionné de mangas, '{term}' représente : {data['definition']}. C'est une figure courante caractérisée par : {data['origin']}",
                ),
                (
                    f"Explique l'origine, l'étymologie et la signification profonde du trope '{term}'.",
                    f"Le trope '{term}' possède une étymologie et une histoire riches. Origine : {data['origin']}. Signification profonde : {data['definition']}. Ce trope s'illustre particulièrement bien avec : {data['examples']}.",
                ),
                (
                    f"D'où vient le mot '{term}' utilisé dans la culture otaku et que signifie-t-il ?",
                    f"Le terme '{term}' trouve sa racine dans : {data['origin']}. Il désigne précisément : {data['definition']}. En industrie, cela s'explique par : {data['impact']}",
                ),
                (
                    f"Quelle est l'histoire et la racine linguistique du concept de '{term}' dans les mangas ?",
                    f"L'histoire linguistique de '{term}' remonte à : {data['origin']}. C'est un concept fondamental signifiant : {data['definition']}",
                ),
                (
                    f"Quels personnages ou œuvres sont considérés comme des exemples emblématiques de '{term}' ?",
                    f"Parmi les exemples phares associés à '{term}' sont : {data['examples']}. Par définition, ce trope représente : {data['definition']}",
                ),
                (
                    f"Donne-moi des exemples de figures célèbres illustrant le trope '{term}' dans les animés.",
                    f"Les figures majeures illustrant le trope '{term}' incluent : {data['examples']}. Ce trope se caractérise par : {data['definition']} et tire son origine de : {data['origin']}",
                ),
                (
                    f"Quelles sont les œuvres majeures qui représentent le mieux le concept de '{term}' ?",
                    f"Les œuvres et personnages emblématiques pour '{term}' sont : {data['examples']}. Ce concept est défini comme : {data['definition']}",
                ),
                (
                    f"Quelle est l'importance et l'impact culturel de la notion de '{term}' dans l'industrie de l'animation ?",
                    f"L'impact culturel de '{term}' dans l'industrie est majeur. {data['impact']} Par définition : {data['definition']}. On le retrouve dans : {data['examples']}",
                ),
                (
                    f"Analyse l'influence et le rôle scénaristique du trope '{term}' dans les mangas.",
                    f"Le rôle scénaristique de '{term}' est très influent. {data['impact']} Il permet d'exprimer : {data['definition']}. Exemples : {data['examples']}",
                ),
                (
                    f"Pourquoi le concept de '{term}' est-il si populaire et récurrent dans les animés japonais ?",
                    f"La popularité de '{term}' s'explique par sa résonance dans la pop-culture. {data['impact']} Origine : {data['origin']}. Définition : {data['definition']}",
                ),
                (
                    f"Fais-moi une synthèse complète et experte sur le concept Otaku de '{term}'.",
                    f"Synthèse Experte - '{term}' : {data['definition']}. Origine étymologique : {data['origin']}. Œuvres et personnages repères : {data['examples']}. Impact d'écriture : {data['impact']}",
                ),
                (
                    f"Quels sont les détails clés et l'analyse à retenir sur la notion de '{term}' ?",
                    f"Les points essentiels à retenir sur '{term}' sont : sa définition ({data['definition']}), sa racine historique ({data['origin']}) et ses incarnations majeures ({data['examples']}).",
                ),
            ]
        for q, a in templates:
            otaku_instructions.append(
                {"instruction": q, "input": "", "output": a, "language": lang}
            )

    # 2. Génération par template pour les créateurs et studios d'animation (15 variations par concept = 1 500 exemples)
    for idx, (creator, data) in enumerate(CREATORS_AND_STUDIOS.items()):
        if idx % 2 == 1:
            lang = "English"
            definition = translate_to_english_via_gemini(data["definition"], client)
            examples = translate_to_english_via_gemini(data["examples"], client)
            impact = translate_to_english_via_gemini(data["impact"], client)
            origin = translate_to_english_via_gemini(data["origin"], client)

            templates = [
                (
                    f"Who is '{creator}' in the world of Japanese animation and manga?",
                    f"In the Japanese industry, '{creator}' is: {definition}. Their most notable works include: {examples}. Impact: {impact}",
                ),
                (
                    f"Present in detail the profile and industrial impact of '{creator}'.",
                    f"Domain profile - '{creator}': {definition} Origins and context: {origin}. Among their most famous works are: {examples}. Their impact is immense: {impact}",
                ),
                (
                    f"What are the iconic works of '{creator}' and their historical role?",
                    f"'{creator}' has marked history through their creations: {examples}. They are defined as: {definition} Major influence: {impact}",
                ),
                (
                    f"As a Japanese animation specialist, what can you tell me about '{creator}'?",
                    f"As a specialist, I can tell you that '{creator}' is: {definition} Historical context: {origin}. They have worked on projects like: {examples}.",
                ),
                (
                    f"Why is '{creator}' considered a legendary figure in otaku culture?",
                    f"'{creator}' is considered legendary because their impact has been revolutionary: {impact} They established themselves as: {definition}",
                ),
                (
                    f"What are the key projects of '{creator}'?",
                    f"The notable projects of '{creator}' include: {examples}. Their philosophy and career path: {origin}",
                ),
                (
                    f"Present a complete summary of the studio or creator '{creator}'.",
                    f"Domain Summary - '{creator}': {definition}. History and origins: {origin}. Major achievements: {examples}. Industry impact: {impact}",
                ),
                (
                    f"Can you analyze the importance of '{creator}' for the manga industry?",
                    f"The importance of '{creator}' is indisputable: {impact} They worked through: {definition}. Reference works: {examples}",
                ),
                (
                    f"What was the role of '{creator}' in the development of Japanese animation?",
                    f"'{creator}' played a crucial role: {impact} By definition: {definition}. Context: {origin}",
                ),
                (
                    f"Give details on the style or contributions of '{creator}'.",
                    f"The contributions of '{creator}' can be summarized as follows: {definition}. Their key works: {examples}. Style and impact: {impact}",
                ),
                (
                    f"Explain how '{creator}' influenced other authors or studios.",
                    f"The influence of '{creator}' extends widely: {impact} They redefined the industry as: {definition}. Their reference creations are: {examples}",
                ),
                (
                    f"What are the major characteristics associated with the creations of '{creator}'?",
                    f"The creations of '{creator}' are characterized by their style: {definition}. Notable examples: {examples}. Context: {origin}",
                ),
                (
                    f"Describe the artistic career and profile of '{creator}'.",
                    f"Artistic path of '{creator}': {definition}. Origins and evolution: {origin}. Their most influential projects: {examples}",
                ),
                (
                    f"Analyze the historical importance and legacy of '{creator}'.",
                    f"The legacy of '{creator}' is colossal. {impact} Known for: {definition}. Key achievements: {examples}",
                ),
                (
                    f"What makes '{creator}' essential in the modern otaku landscape?",
                    f"'{creator}' is essential as: {definition}. Their popular creations ({examples}) and impact ({impact}) make them an absolute reference.",
                ),
            ]
        else:
            lang = "Français"
            templates = [
                (
                    f"Qui est '{creator}' dans le monde de l'animation et du manga japonais ?",
                    f"Dans l'industrie japonaise, '{creator}' est : {data['definition']}. Ses travaux les plus marquants incluent : {data['examples']}. Impact : {data['impact']}",
                ),
                (
                    f"Présente-moi en détail le profil et l'impact industriel de '{creator}'.",
                    f"Profil de domaine - '{creator}' : {data['definition']} Origines et contexte : {data['origin']}. Parmi ses œuvres les plus célèbres, on compte : {data['examples']}. Son impact est immense : {data['impact']}",
                ),
                (
                    f"Quelles sont les œuvres emblématiques de '{creator}' et son rôle historique ?",
                    f"'{creator}' a marqué l'histoire à travers ses créations : {data['examples']}. Il est défini comme : {data['definition']} Influence majeure : {data['impact']}",
                ),
                (
                    f"En tant que spécialiste de la japanimation, que peux-tu me dire sur '{creator}' ?",
                    f"En tant que spécialiste, je peux vous dire que '{creator}' est : {data['definition']} Contexte historique : {data['origin']}. Il a travaillé sur des projets comme : {data['examples']}.",
                ),
                (
                    f"Pourquoi '{creator}' est-il considéré comme une figure légendaire de la culture otaku ?",
                    f"'{creator}' est considéré comme légendaire car son impact a été révolutionnaire : {data['impact']} Il s'est imposé comme : {data['definition']}",
                ),
                (
                    f"Quels sont les projets phares de '{creator}' ?",
                    f"Les projets marquants de '{creator}' comprennent : {data['examples']}. Sa philosophie et son parcours : {data['origin']}",
                ),
                (
                    f"Présente une synthèse complète du studio ou créateur '{creator}'.",
                    f"Synthèse de domaine - '{creator}' : {data['definition']}. Histoire et origines : {data['origin']}. Réalisations majeures : {data['examples']}. Impact d'industrie : {data['impact']}",
                ),
                (
                    f"Peux-tu analyser l'importance de '{creator}' pour l'industrie du manga ?",
                    f"L'importance de '{creator}' est indiscutable : {data['impact']} Il a œuvré à travers : {data['definition']}. Œuvres repères : {data['examples']}",
                ),
                (
                    f"Quel a été le rôle de '{creator}' dans le développement de l'animation japonaise ?",
                    f"'{creator}' a joué un rôle déterminant : {data['impact']} Par définition : {data['definition']}. Contexte : {data['origin']}",
                ),
                (
                    f"Donne des détails sur le style ou les contributions de '{creator}'.",
                    f"Les contributions de '{creator}' se résument ainsi : {data['definition']}. Ses travaux phares : {data['examples']}. Style et impact : {data['impact']}",
                ),
                (
                    f"Explique comment '{creator}' a influencé d'autres auteurs ou studios.",
                    f"L'influence de '{creator}' s'étend largement : {data['impact']} Il a redéfini le secteur comme : {data['definition']}. Ses créations repères sont : {data['examples']}",
                ),
                (
                    f"Quelles sont les caractéristiques majeures associées aux créations de '{creator}' ?",
                    f"Les créations de '{creator}' se caractérisent par son style : {data['definition']}. Exemples notables : {data['examples']}. Contexte : {data['origin']}",
                ),
                (
                    f"Décris le parcours artistique et le profil de '{creator}'.",
                    f"Parcours de '{creator}' : {data['definition']}. Origines et évolutions : {data['origin']}. Ses projets les plus influents : {data['examples']}",
                ),
                (
                    f"Analyse l'importance historique et l'héritage de '{creator}'.",
                    f"L'héritage de '{creator}' est colossal. {data['impact']} Connu pour : {data['definition']}. Réalisations clés : {data['examples']}",
                ),
                (
                    f"Qu'est-ce qui rend '{creator}' incontournable dans le paysage otaku moderne ?",
                    f"'{creator}' est incontournable en tant que : {data['definition']}. Ses créations populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.",
                ),
            ]
        for q, a in templates:
            otaku_instructions.append(
                {"instruction": q, "input": "", "output": a, "language": lang}
            )

    # 3. Ajout de comparaisons croisées (12 exemples)
    comparisons = [
        (
            "Tsundere",
            "Yandere",
            "Alors que le personnage Tsundere cache son affection derrière de l'agressivité verbale mais reste fondamentalement sain, le Yandere bascule dans une folie obsessionnelle et violente (pouvant aller jusqu'au meurtre) pour posséder l'être aimé.",
        ),
        (
            "Kuudere",
            "Dandere",
            "Le personnage Kuudere est calme, froid, impassible et garde le contrôle de ses émotions en public ('cool'), tandis que le Dandere est d'une timidité maladive, asocial et silencieux par peur d'interagir, bien qu'il soit extrêmement chaleureux une fois en confiance.",
        ),
        (
            "Shonen",
            "Seinen",
            "Le Shonen cible un public de jeunes garçons adolescents (focus sur les combats, l'amitié sacrée 'nakama' et le dépassement de soi), tandis que le Seinen vise les jeunes adultes masculins, abordant des thèmes plus matures, sombres, philosophiques ou politiques (comme la vengeance dans *Berserk* ou l'éthique dans *Monster*).",
        ),
        (
            "Shojo",
            "Josei",
            "Le Shojo cible les adolescentes (romances idéalisées, esthétique fleurie et focus émotionnel), tandis que le Josei s'adresse aux femmes adultes, traitant de relations amoureuses ou professionnelles de manière beaucoup plus réaliste et mature (ex: *Nana*).",
        ),
        (
            "Sub",
            "Dub",
            "Le format 'Sub' (VOSTFR/VOST) conserve les voix et l'interprétation originale des seiyuu japonais qui est souvent considérée comme plus expressive et authentique, tandis que le 'Dub' (doublage local) offre un confort de visionnage maximal et une immersion immédiate sans lecture de sous-titres, idéal pour toucher un public plus large.",
        ),
        (
            "Raw",
            "Sub",
            "La version 'Raw' désigne le flux vidéo brut tel qu'il est diffusé à la TV japonaise sans aucun sous-titre ni modification, alors que la version 'Sub' intègre les pistes de sous-titres traduits pour la diffusion internationale.",
        ),
        (
            "Maid",
            "Butler",
            "La Maid incarne la servante en uniforme victorien/français et est l'icône de la culture kawaii et des maid cafés, tandis que le Butler (majordome) incarne la classe, le sang-froid et la protection élégante, souvent doté de capacités martiales démesurées.",
        ),
        (
            "Himedere",
            "Oujidere",
            "La Himedere exige d'être traitée comme une reine/princesse exigeante et capricieuse, tandis que l'Oujidere incarne l'équivalent masculin exigeant d'être traité comme un prince hautain et charismatique.",
        ),
        (
            "Isekai",
            "Reverse Isekai",
            "L'Isekai traditionnel projette un humain ordinaire dans un autre monde fantastique, tandis que le Reverse Isekai amène des créatures magiques ou divines (ex: un roi démon) dans notre monde moderne et terre-à-terre.",
        ),
        (
            "Slow Life",
            "Isekai",
            "L'Isekai traditionnel met en scène des quêtes héroïques et des combats contre des rois démons, alors que le sous-genre 'Slow Life' se concentre sur l'agriculture, l'artisanat et une vie paisible loin des conflits.",
        ),
        (
            "Kamidere",
            "Himedere",
            "Le Kamidere a un complexe divin absolu et veut réformer le monde ou dominer l'humanité, tandis que la Himedere cherche simplement à être adorée, servie et choyée comme une princesse royale.",
        ),
        (
            "Sadodere",
            "Tsundere",
            "La Tsundere est hostile par gêne et fierté mais devient douce rapidement, tandis que la Sadodere prend un plaisir délibéré et malicieux à taquiner, manipuler ou dominer psychologiquement l'être aimé.",
        ),
    ]
    for t1, t2, diff in comparisons:
        otaku_instructions.append(
            {
                "instruction": f"Quelle est la différence fondamentale entre les termes '{t1}' et '{t2}' dans les animés et mangas ?",
                "input": "",
                "output": f"La distinction entre '{t1}' et '{t2}' est essentielle pour comprendre les archétypes d'animes. {diff} Par exemple, pour les {t1}, on pense souvent à {OTAKU_VOCABULARY[t1]['examples']}, tandis que pour les {t2}, un exemple frappant est {OTAKU_VOCABULARY[t2]['examples']}.",
            }
        )

    return otaku_instructions
