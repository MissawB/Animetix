# -*- coding: utf-8 -*-
"""
Base de données spécialisée sur le nombre d'épisodes, de saisons et de tomes (volumes)
des animés et mangas les plus populaires pour alimenter le jeu de données SFT.
"""

VOLUMES_AND_EPISODES_DATA = {
    "One Piece": {
        "anime_episodes": "Plus de 1100 épisodes (en cours de diffusion)",
        "anime_seasons": "Plus de 20 saisons / arcs majeurs (comme Alabasta, Water Seven, Marineford, Dressrosa, Wano Kuni, et l'île d'Egghead)",
        "manga_volumes": "Plus de 108 tomes parus (en cours de publication en France chez Glénat)",
        "status": "En cours de publication et de diffusion",
        "details": "L'anime produit par Toei Animation a franchi le cap historique du 1000ème épisode en 2021. Le manga, écrit et dessiné par Eiichiro Oda, est le manga le plus vendu de tous les temps.",
    },
    "Naruto": {
        "anime_episodes": "720 épisodes au total, divisés en deux parties : 220 épisodes pour la série originale 'Naruto' et 500 épisodes pour 'Naruto Shippuden'",
        "anime_seasons": "9 saisons pour la première série et 21 saisons pour la série Shippuden",
        "manga_volumes": "72 tomes reliés au total (complet, publiés en France par Kana)",
        "status": "Terminé (suivi par la série dérivée Boruto)",
        "details": "Le manga de Masashi Kishimoto s'est terminé en 2014. L'adaptation animée par le studio Pierrot est célèbre pour ses nombreux épisodes hors-série ('fillers'), mais reste une référence absolue du shonen.",
    },
    "L'Attaque des Titans": {
        "anime_episodes": "88 épisodes au total, plus 8 OAV",
        "anime_seasons": "4 saisons (Saison 1 : 25 épisodes, Saison 2 : 12 épisodes, Saison 3 : 22 épisodes divisés en deux parties, Saison 4 dite 'Finale' : 29 épisodes divisés en trois parties de diffusion et des épisodes spéciaux de conclusion)",
        "manga_volumes": "34 tomes au total (complet, publiés en France par Pika Édition)",
        "status": "Terminé",
        "details": "Le manga de Hajime Isayama a débuté en 2009 et s'est conclu en 2021. L'adaptation animée a été réalisée par Wit Studio (saisons 1 à 3) puis par le studio MAPPA pour la saison finale, marquant l'histoire par son animation spectaculaire et son scénario implacable.",
    },
    "Demon Slayer": {
        "anime_episodes": "63 épisodes diffusés (avant la trilogie de films finaux annoncée pour adapter l'arc de la Forteresse Infinie)",
        "anime_seasons": "4 saisons (Saison 1 - Arc de sélection : 26 épisodes, Saison 2 - Arc du Train de l'Infini en 7 épisodes et Arc du Quartier des Plaisirs en 11 épisodes soit 18 épisodes, Saison 3 - Arc du Village des Forgerons : 11 épisodes, Saison 4 - Arc de l'Entraînement des Piliers : 8 épisodes)",
        "manga_volumes": "23 tomes au total (complet, publié en France par Panini Manga)",
        "status": "Manga terminé, anime en cours (fin sous forme de films)",
        "details": "Le manga de Koyoharu Gotouge s'est terminé en 2020. L'adaptation animée par le studio ufotable est mondialement acclamée pour la qualité phénoménale de ses effets visuels et de ses combats.",
    },
    "Death Note": {
        "anime_episodes": "37 épisodes au total",
        "anime_seasons": "1 saison complète (souvent divisée informellement en deux parties par les fans, séparées par le tournant scénaristique majeur de l'épisode 25)",
        "manga_volumes": "12 tomes au total (plus un tome 13 spécial contenant des guides et une histoire courte, publiés en France par Kana)",
        "status": "Terminé",
        "details": "Le manga, scénarisé par Tsugumi Ohba et dessiné par Takeshi Obata, est un chef-d'œuvre de thriller psychologique. L'anime a été produit par le studio Madhouse et réalisé par Tetsuro Araki.",
    },
    "Fullmetal Alchemist: Brotherhood": {
        "anime_episodes": "64 épisodes au total (plus 4 OAV)",
        "anime_seasons": "1 saison unique de 64 épisodes (souvent diffusée en 5 parties thématiques)",
        "manga_volumes": "27 tomes au total (complet, publiés en France par Kurokawa)",
        "status": "Terminé",
        "details": "Cette seconde adaptation animée par le studio Bones en 2009 suit fidèlement le manga original de Hiromu Arakawa, contrairement à la première série de 2003 qui avait divergé vers un scénario original.",
    },
    "Hunter x Hunter (2011)": {
        "anime_episodes": "148 épisodes au total",
        "anime_seasons": "6 saisons / arcs majeurs (Arc de l'Examen des Hunters, Arc de la Famille Zoldyck & Celestial Tower, Arc de York Shin City, Arc de Greed Island, Arc des Chimera Ants, et Arc de l'Élection du 13ème Président)",
        "manga_volumes": "38 tomes (en cours de publication en France chez Kana, sujet à de nombreuses pauses en raison des problèmes de santé de l'auteur)",
        "status": "Manga en cours (pauses fréquentes), anime terminé (s'arrêtant à la fin de l'arc de l'élection)",
        "details": "Le manga légendaire de Yoshihiro Togashi a débuté en 1998. L'adaptation animée de 2011 par le studio Madhouse est considérée comme l'un des meilleurs shonens de tous les temps.",
    },
    "My Hero Academia": {
        "anime_episodes": "159 épisodes au total (à la fin de la saison 7)",
        "anime_seasons": "7 saisons (Saison 1 : 13 épisodes, Saisons 2 à 6 : 25 épisodes chacune, Saison 7 : 21 épisodes)",
        "manga_volumes": "42 tomes parus au Japon, série terminée récemment en 2024 (publiée en France par Ki-oon)",
        "status": "Manga terminé au Japon, anime en cours de finalisation",
        "details": "Créé par Kohei Horikoshi en 2014, ce manga mélange codes des comics de super-héros et du shonen traditionnel. L'adaptation animée est produite par le studio Bones.",
    },
    "Jujutsu Kaisen": {
        "anime_episodes": "47 épisodes au total, plus le film préquel 'Jujutsu Kaisen 0'",
        "anime_seasons": "2 saisons (Saison 1 : 24 épisodes, Saison 2 : 23 épisodes couvrant les arcs Trésor Caché / Mort Prématurée et le Drame de Shibuya)",
        "manga_volumes": "28 tomes parus au Japon, manga terminé récemment en 2024 (publié en France par Ki-oon)",
        "status": "Manga terminé au Japon, anime en cours",
        "details": "L'œuvre sombre de Gege Akutami a débuté en 2018. L'anime produit par le studio MAPPA a reçu de nombreuses distinctions pour ses scènes d'action dynamiques et complexes.",
    },
    "Dragon Ball": {
        "anime_episodes": "575 épisodes pour la saga originale d'Akira Toriyama (153 pour Dragon Ball, 291 pour Dragon Ball Z, et 131 pour Dragon Ball Super)",
        "anime_seasons": "Plus de 20 saisons au total à travers les trois séries majeures",
        "manga_volumes": "42 tomes pour le manga original Dragon Ball (complet, publié par Glénat), suivis par la série Dragon Ball Super (23+ tomes en cours)",
        "status": "Manga classique terminé, suites et dérivés en cours",
        "details": "Le chef-d'œuvre d'Akira Toriyama, débuté en 1984, est le pilier fondateur du shonen moderne à l'échelle mondiale. Les adaptations de la Toei Animation ont bercé plusieurs générations.",
    },
    "Bleach": {
        "anime_episodes": "366 épisodes pour l'anime classique, plus la suite 'Bleach: Thousand-Year Blood War' (prévue en 4 parties de 13 épisodes soit 52 épisodes au total)",
        "anime_seasons": "16 saisons pour la première série, et 4 parties distinctes pour l'arc final",
        "manga_volumes": "74 tomes au total (complet, publiés en France par Glénat)",
        "status": "Manga terminé, anime de l'arc final en cours",
        "details": "Le manga de Tite Kubo, membre du fameux 'Big Three' du Jump des années 2000, se distingue par son sens du design et ses combats de sabre. L'anime est produit par le studio Pierrot.",
    },
    "Chainsaw Man": {
        "anime_episodes": "12 épisodes diffusés pour l'instant (la suite de l'arc Reze est annoncée sous forme de long-métrage de cinéma)",
        "anime_seasons": "1 saison de 12 épisodes",
        "manga_volumes": "Plus de 18 tomes parus (en cours de publication en France chez Crunchyroll)",
        "status": "Manga en cours de publication (Partie 2 dans le Jump+), anime en cours",
        "details": "L'œuvre atypique et déjantée de Tatsuki Fujimoto a commencé en 2018. La première saison animée par MAPPA en 2022 est célèbre pour avoir proposé un ending unique et différent pour chaque épisode.",
    },
    "Berserk": {
        "anime_episodes": "25 épisodes pour la série animée culte de 1997, et 24 épisodes pour la série en 3D de 2016-2017. Il existe également une trilogie de films adaptant l'arc de l'Âge d'Or",
        "anime_seasons": "1 saison pour l'anime de 1997, 2 saisons pour l'anime de 2016",
        "manga_volumes": "42 tomes parus (en cours de publication, repris par le studio Gaga et Kouji Mori après le décès tragique de l'auteur Kentaro Miura, publiés chez Glénat)",
        "status": "En cours de publication",
        "details": "Berserk est le chef-d'œuvre ultime de la dark fantasy. Le style de dessin de Kentaro Miura, d'une richesse inégalée, explique le rythme de parution lent de l'œuvre.",
    },
    "Monster": {
        "anime_episodes": "74 épisodes au total",
        "anime_seasons": "1 saison unique de 74 épisodes (sans aucun filler, adaptant fidèlement l'intégralité du récit)",
        "manga_volumes": "18 tomes au total (ou 9 tomes en édition deluxe double 'Intégrale', publiés par Kana)",
        "status": "Terminé",
        "details": "Le manga à suspense de Naoki Urasawa est un chef-d'œuvre de tension psychologique situé dans l'Allemagne post-guerre froide. L'adaptation animée de Madhouse est un modèle de fidélité absolue.",
    },
    "Neon Genesis Evangelion": {
        "anime_episodes": "26 épisodes pour la série télévisée originale de 1995, complétée par les films 'Death and Rebirth' et 'The End of Evangelion', puis par la tétralogie de films 'Rebuild of Evangelion' (1.0, 2.0, 3.0, 3.0+1.0)",
        "anime_seasons": "1 saison",
        "manga_volumes": "14 tomes au total (dessinés par Yoshiyuki Sadamoto, le character designer de la série, publiés en France par Glénat)",
        "status": "Terminé",
        "details": "Créée par Hideaki Anno et le studio Gainax, cette franchise de mécha a révolutionné l'animation jagonaise par ses thèmes psychologiques, philosophiques et religieux complexes.",
    },
    "Fairy Tail": {
        "anime_episodes": "328 épisodes pour la série principale, suivis par l'adaptation de 'Fairy Tail: 100 Years Quest' (en cours)",
        "anime_seasons": "9 saisons pour la série principale",
        "manga_volumes": "63 tomes au total (complet, publiés en France par Pika Édition), suivis de la suite '100 Years Quest'",
        "status": "Série principale terminée, suites en cours de diffusion",
        "details": "Le manga d'aventure de Hiro Mashima a rencontré un succès immense dans le monde grâce à ses personnages attachants et son univers de magie chaleureux. L'anime a été co-produit par A-1 Pictures et Bridge.",
    },
    "Tokyo Ghoul": {
        "anime_episodes": "48 épisodes au total (12 épisodes pour la saison 1, 12 pour Tokyo Ghoul √A, et 24 pour Tokyo Ghoul:re)",
        "anime_seasons": "4 saisons au total (S1, Root A, S1 de :re, S2 de :re)",
        "manga_volumes": "30 tomes au total (14 tomes pour 'Tokyo Ghoul' et 16 tomes pour la suite 'Tokyo Ghoul:re', publiés par Glénat)",
        "status": "Terminé",
        "details": "L'œuvre de Sui Ishida combine horreur, drame et action. L'adaptation animée par le studio Pierrot a été critiquée pour ses coupes budgétaires et ses libertés scénaristiques par rapport au manga, mais a grandement popularisé la licence.",
    },
    "One Punch Man": {
        "anime_episodes": "24 épisodes au total, plus plusieurs OAV (la saison 3 est en cours de production)",
        "anime_seasons": "2 saisons de 12 épisodes chacune (Saison 1 produite par Madhouse, Saison 2 produite par J.C. Staff)",
        "manga_volumes": "Plus de 30 tomes parus (en cours de publication chez Kurokawa en France)",
        "status": "En cours",
        "details": "Né d'un webmanga de l'auteur ONE, One-Punch Man a été magnifiquement redessiné par Yusuke Murata. Le combat final de la saison 1 est l'un des moments d'animation les plus cultes des années 2010.",
    },
}
