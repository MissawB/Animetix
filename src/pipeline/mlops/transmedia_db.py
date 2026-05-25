# -*- coding: utf-8 -*-
"""
Base de données de 100 relations transmédia distinctes reliant la pop-culture japonaise,
les jeux vidéo, le cinéma hollywoodien et les inspirations culturelles majeures.
"""

TRANSMEDIA_RELATIONS = [
    # --- GROUPE A: JEUX VIDÉO <-> ANIME/MANGA (35 relations) ---
    {
        "question": "Comment s'appelle le jeu vidéo se déroulant dans le futur qui a donné naissance à une superbe adaptation en animé par le studio Trigger ?",
        "answer": "Le jeu vidéo est 'Cyberpunk 2077'. Il a été adapté sous forme de série animée sous le titre 'Cyberpunk: Edgerunners' par le studio japonais Trigger. Cette série acclamée a grandement relancé l'intérêt et la popularité du jeu de CD Projekt Red."
    },
    {
        "question": "Quelle série d'animation acclamée de Netflix, réalisée par le studio français Fortiche, adapte l'univers d'un célèbre jeu vidéo de type MOBA ?",
        "answer": "La série d'animation est 'Arcane'. Elle adapte avec brio l'univers et l'histoire des personnages du très populaire jeu vidéo de type MOBA 'League of Legends' développé par Riot Games."
    },
    {
        "question": "De quel jeu vidéo gothique de Konami s'inspire la série animée à succès de Netflix ?",
        "answer": "La série animée s'inspire de la légendaire franchise de jeux vidéo d'action-plateforme gothique 'Castlevania' éditée par Konami, en se basant principalement sur le jeu 'Castlevania III: Dracula's Curse'."
    },
    {
        "question": "Quel animé de science-fiction post-apocalyptique produit par A-1 Pictures adapte fidèlement le jeu de rôle d'action de Yoko Taro ?",
        "answer": "L'animé est 'NieR:Automata Ver1.1a'. Il s'agit de l'adaptation directe du chef-d'œuvre de jeu vidéo d'action-RPG 'NieR: Automata' conçu par le réalisateur Yoko Taro et développé par PlatinumGames."
    },
    {
        "question": "Quel animé de 2018 adapte fidèlement l'intrigue et le style visuel du jeu de rôle Persona 5 d'Atlus ?",
        "answer": "L'animé est 'Persona 5: The Animation'. Il adapte l'histoire du jeu de rôle acclamé 'Persona 5' développé par Atlus, en suivant le protagoniste Ren Amamiya et son groupe de 'Voleurs Fantômes de Cœurs'."
    },
    {
        "question": "De quel jeu de rôle d'Atlus s'inspire l'animé culte Persona 4: The Animation ?",
        "answer": "Il s'inspire du célèbre jeu vidéo de rôle et de simulation sociale 'Persona 4' développé par Atlus, se déroulant dans la petite ville rurale d'Inaba en proie à des meurtres mystérieux."
    },
    {
        "question": "Sous quelle forme cinématographique a été adaptée l'histoire du jeu vidéo Persona 3 d'Atlus ?",
        "answer": "L'intrigue du jeu vidéo 'Persona 3' a été adaptée sous la forme d'une série de quatre films d'animation cinématographiques intitulés 'Persona 3 The Movie', sortis entre 2013 et 2016."
    },
    {
        "question": "Quel célèbre animé de science-fiction et de voyage dans le temps est l'adaptation directe d'un Visual Novel de science-fiction édité par 5pb. et Nitroplus ?",
        "answer": "L'animé est 'Steins;Gate'. Il s'agit de l'adaptation magistrale du jeu vidéo de type Visual Novel éponyme 'Steins;Gate', largement considéré comme l'un des meilleurs récits de science-fiction temporelle de l'histoire du jeu vidéo."
    },
    {
        "question": "Quel animé dramatique et extrêmement émouvant de Kyoto Animation est l'adaptation d'un Visual Novel de Key ?",
        "answer": "L'animé est 'Clannad' (et sa suite marquante 'Clannad: After Story'). Il adapte le célèbre jeu de type Visual Novel dramatique 'Clannad' développé par le studio Key."
    },
    {
        "question": "De quel jeu vidéo de type Visual Novel de Type-Moon s'inspirent les séries animées Fate/stay night ?",
        "answer": "Elles s'inspirent du Visual Novel à succès 'Fate/stay night' créé par le studio Type-Moon, qui a donné naissance à la gigantesque franchise multimédia 'Fate' centrée sur la guerre du Saint-Graal."
    },
    {
        "question": "Quel animé de 2019 adapte l'arc de Babylone du très populaire jeu de rôle mobile de Type-Moon ?",
        "answer": "L'animé est 'Fate/Grand Order: Absolute Demonic Front: Babylonia'. Il adapte le chapitre 'Babylone' du jeu de rôle mobile à succès 'Fate/Grand Order'."
    },
    {
        "question": "Quelle franchise multimédia colossale a débuté comme un jeu de rôle sur Game Boy avant de donner l'un des animés les plus longs de l'histoire ?",
        "answer": "Il s'agit de la franchise 'Pokémon' (Pocket Monsters). Elle a commencé par les jeux vidéo 'Pokémon Vert et Rouge' sur Game Boy en 1996 avant de donner naissance à la série animée historique suivant les aventures de Sacha (Ash Ketchum)."
    },
    {
        "question": "Quel animé court de quatre épisodes adapte fidèlement l'intrigue originale des jeux vidéo Pokémon Rouge et Bleu ?",
        "answer": "L'animé est 'Pokémon Origins' (Pokémon: Les Origines). Contrairement à la série principale, il adapte fidèlement l'aventure originale du dresseur Red des jeux Game Boy 'Pokémon Rouge et Bleu'."
    },
    {
        "question": "Quel manga et animé culte de fantasy s'inspire directement de la franchise de jeux de rôle Dragon Quest de Square Enix ?",
        "answer": "Il s'agit de 'Dragon Quest: The Adventure of Dai' (connu en France sous le nom de 'Fly'). L'œuvre a été créée pour s'inscrire officiellement dans l'univers de la franchise de jeux de rôle 'Dragon Quest'."
    },
    {
        "question": "Quel film en images de synthèse de 2005 sert de suite directe aux événements du jeu vidéo légendaire Final Fantasy VII ?",
        "answer": "Le film est 'Final Fantasy VII: Advent Children'. Réalisé par Tetsuya Nomura, ce film en images de synthèse prolonge l'histoire du jeu de rôle légendaire de Square Enix deux ans après sa conclusion."
    },
    {
        "question": "Quelle série animée de cinq épisodes sert de préquelle et d'introduction aux personnages du jeu vidéo Final Fantasy XV ?",
        "answer": "La série est 'Brotherhood: Final Fantasy XV'. Elle explore la jeunesse et les liens d'amitié unissant Noctis à ses trois compagnons de route avant les événements du jeu vidéo de Square Enix."
    },
    {
        "question": "Quel film d'animation en images de synthèse de Netflix s'inscrit dans l'univers de la franchise de jeux vidéo de chasse aux monstres Monster Hunter ?",
        "answer": "Le film est 'Monster Hunter: Legends of the Guild'. Produit par 3D animators, il adapte l'univers de chasse de la célèbre franchise de jeux vidéo 'Monster Hunter' de Capcom."
    },
    {
        "question": "Quelle série animée de Netflix adapte l'univers du jeu de type MOBA Dota 2 développé par Valve ?",
        "answer": "La série est 'DOTA: Dragon's Blood'. Produite par Studio Mir, elle développe l'histoire et l'univers fantastique entourant les héros du jeu vidéo de stratégie en arène 'Dota 2'."
    },
    {
        "question": "Quelle série d'animation de Netflix adapte l'univers et le scénario du jeu de rôle d'action de fantasy Dragon's Dogma de Capcom ?",
        "answer": "La série est 'Dragon's Dogma'. Elle adapte l'intrigue du jeu de rôle éponyme de Capcom, en suivant la quête de vengeance d'un insurgé ('Arisen') dont le cœur a été volé par un dragon."
    },
    {
        "question": "Quel animé de 2022 adapte l'univers et l'intrigue du jeu d'action classique Shenmue de Sega ?",
        "answer": "L'animé est 'Shenmue the Animation'. Produit par Telecom Animation Film, il transpose l'histoire de vengeance martiale de Ryo Hazuki issue du jeu vidéo culte 'Shenmue' de Yu Suzuki."
    },
    {
        "question": "Quelle série animée de Netflix prolonge l'histoire de la célèbre aventurière de jeux vidéo Lara Croft ?",
        "answer": "La série est 'Tomb Raider: The Legend of Lara Croft'. Elle sert de pont narratif entre la trilogie de jeux vidéo de survie ('Survivor Trilogy') développée par Crystal Dynamics et les jeux originaux."
    },
    {
        "question": "Quel animé de Netflix adapte l'histoire du tournoi de combat et de la rivalité familiale de la franchise de jeux de combat Tekken ?",
        "answer": "L'animé est 'Tekken: Bloodline'. Il se concentre sur l'entraînement de Jin Kazama sous la tutelle de son grand-père Heihachi Mishima, adaptant principalement l'intrigue du jeu vidéo de combat mythique 'Tekken 3'."
    },
    {
        "question": "Quelle série d'animation en cours de production par Netflix adapte l'univers de chasse aux démons stylisée de Devil May Cry de Capcom ?",
        "answer": "La série est 'Devil May Cry'. Produite par Studio Mir et le showrunner Adi Shankar, elle adapte la franchise culte de jeux d'action hack'n'slash 'Devil May Cry' centrée sur le personnage de Dante."
    },
    {
        "question": "Quel film d'animation japonais mythique de 1994 a adapté pour la première fois le jeu vidéo de combat légendaire Street Fighter II ?",
        "answer": "Le film est 'Street Fighter II: The Animated Movie'. Réalisé par Gisaburo Sugii, ce film culte a posé les bases de l'animation de combat et a influencé les animations futures des jeux de Capcom."
    },
    {
        "question": "Quelle série animée japonaise de 1995 transpose de manière libre les aventures de Ryu et Ken de Street Fighter II ?",
        "answer": "La série est 'Street Fighter II V'. Elle suit le voyage d'apprentissage des jeunes Ryu et Ken à travers le monde pour perfectionner leurs techniques de combat."
    },
    {
        "question": "Quel animé transpose en animation l'univers et les personnages du jeu vidéo de rôle mobile japonais Granblue Fantasy de Cygames ?",
        "answer": "L'animé est 'Granblue Fantasy: The Animation'. Il transpose l'aventure fantastique aérienne du jeu mobile à succès de Cygames."
    },
    {
        "question": "Quel animé de 2019 personnifie les navires de guerre historiques sous forme de filles d'animes, adaptant le jeu de tir mobile éponyme ?",
        "answer": "L'animé est 'Azur Lane'. Il s'agit de l'adaptation du jeu vidéo mobile chinois à succès qui met en scène des jeunes filles anthropomorphes représentant des cuirassés réels."
    },
    {
        "question": "Quelle collaboration d'animation très attendue a été annoncée entre le studio d'élite ufotable et le jeu de rôle à succès mondial Genshin Impact ?",
        "answer": "Il s'agit du projet d'animation officiel 'Genshin Impact' produit en collaboration par le studio ufotable (connu pour *Demon Slayer*) et le développeur MiHoYo."
    },
    {
        "question": "Quel animé de science-fiction dystopique adapte le jeu mobile tactique de type tower defense Arknights ?",
        "answer": "L'animé est 'Arknights: Prelude to Dawn'. Il adapte l'univers post-apocalyptique sombre et les combats tactiques du jeu mobile éponyme."
    },
    {
        "question": "De quelle franchise de jeux vidéo de tir de science-fiction de Microsoft s'inspire le film d'animation anthologique Halo Legends ?",
        "answer": "Il s'inspire de la célèbre franchise de jeux vidéo de science-fiction 'Halo'. Le film réunit plusieurs studios d'animation japonais célèbres pour raconter différentes histoires de cet univers."
    },
    {
        "question": "Quel film d'animation en images de synthèse de 2012 s'inscrit dans l'univers de science-fiction spatiale du jeu Mass Effect de Bioware ?",
        "answer": "Le film est 'Mass Effect: Paragon Lost'. Produit par Production I.G, il sert de préquelle centré sur le personnage de James Vega avant les événements du jeu vidéo de science-fiction 'Mass Effect 3'."
    },
    {
        "question": "Quel animé de 2013 transpose le jeu vidéo d'enquête et de meurtre lycéen d'épouvante Danganronpa de Spike Chunsoft ?",
        "answer": "L'animé est 'Danganronpa: The Animation'. Il adapte le premier jeu vidéo de type Visual Novel et d'enquête criminelle 'Danganronpa: Trigger Happy Havoc'."
    },
    {
        "question": "Quel animé de 2016 adapte l'univers d'enquêtes judiciaires et de duels de prétoires de la franchise de jeux vidéo Ace Attorney de Capcom ?",
        "answer": "L'animé est 'Ace Attorney' (Gyakuten Saiban). Il transpose fidèlement les procès théâtraux et les enquêtes du célèbre avocat Phoenix Wright des jeux Nintendo DS."
    },
    {
        "question": "Quel animé de ufotable adapte les jeux vidéo de rôle d'action de la célèbre franchise Tales of de Bandai Namco ?",
        "answer": "L'animé est 'Tales of Zestiria the X'. Réalisé par le studio d'élite ufotable, il offre une adaptation visuellement splendide du jeu vidéo de rôle 'Tales of Zestiria'."
    },
    {
        "question": "Quelle série d'OAV adapte le jeu vidéo de rôle culte de la GameCube Tales of Symphonia ?",
        "answer": "Il s'agit de la série d'OAV 'Tales of Symphonia the Animation', qui adapte le jeu vidéo de rôle légendaire de Bandai Namco se déroulant dans le monde de Sylvarant."
    },

    # --- GROUPE B: HOLLYWOOD / LIVE-ACTION <-> MANGA/ANIME (25 relations) ---
    {
        "question": "Quel film de science-fiction avec Tom Cruise en personnage principal est l'adaptation d'un light novel japonais ?",
        "answer": "Le film de science-fiction avec Tom Cruise est 'Edge of Tomorrow'. Il s'agit de l'adaptation du light novel japonais de science-fiction 'All You Need Is Kill' écrit par Hiroshi Sakurazaka."
    },
    {
        "question": "Quel film hollywoodien de science-fiction réalisé par Robert Rodriguez et produit par James Cameron est l'adaptation directe d'un manga cyberpunk culte ?",
        "answer": "Le film est 'Alita: Battle Angel'. Il s'agit de l'adaptation cinématographique en prise de vue réelle du chef-d'œuvre de manga cyberpunk 'Gunnm' (connu en Occident sous le nom de *Battle Angel Alita*) de Yukito Kishiro."
    },
    {
        "question": "Quel film hollywoodien en prise de vue réelle avec Scarlett Johansson est l'adaptation d'un manga cyberpunk légendaire ?",
        "answer": "Le film est 'Ghost in the Shell' (2017). Il adapte en prise de vue réelle l'univers cyberpunk révolutionnaire du manga original de Masamune Shirow et du film d'animation culte de Mamoru Oshii de 1995."
    },
    {
        "question": "Quel film hollywoodien de 2009 en prise de vue réelle est universellement considéré par les fans comme l'une des pires adaptations d'animes de tous les temps ?",
        "answer": "Le film est 'Dragonball Evolution'. Réalisé par James Wong, cette adaptation américaine en prise de vue réelle a été rejetée massivement par la critique et les fans pour sa totale infidélité au manga légendaire 'Dragon Ball' d'Akira Toriyama."
    },
    {
        "question": "Quel film hollywoodien de Netflix de 2017 en prise de vue réelle adapte de manière très controversée le thriller psychologique culte de Tsugumi Ohba ?",
        "answer": "Le film est 'Death Note'. Réalisé par Adam Wingard pour Netflix, cette adaptation américaine transpose l'action à Seattle et a suscité de vifs débats en s'écartant du duel psychologique original entre Light et L."
    },
    {
        "question": "Quel film hollywoodien en prise de vue réelle réalisé par les sœurs Wachowski est l'adaptation d'un grand classique de la japanimation des années 60 ?",
        "answer": "Le film est 'Speed Racer' (2008). Réalisé par les créatrices de Matrix, il s'agit de l'adaptation cinématographique ultra-stylisée visuellement du classique de manga et d'animé automobile 'Mach GoGoGo' créé par Tatsuo Yoshida."
    },
    {
        "question": "Quelle adaptation en série en prise de vue réelle de Netflix de 2023, supervisée par l'auteur Eiichiro Oda lui-même, a rencontré un immense succès mondial ?",
        "answer": "La série est 'One Piece' de Netflix. Contrairement aux précédentes tentatives d'adaptations occidentales, cette version en prise de vue réelle a été saluée par les fans et les critiques pour son respect de l'univers et de l'énergie du manga original."
    },
    {
        "question": "Quel film hollywoodien de 2010 réalisé par M. Night Shyamalan est l'adaptation ratée en prise de vue réelle d'une célèbre série animée occidentale influencée par les animés japonais ?",
        "answer": "Le film est 'The Last Airbender' (Le Dernier Maître de l'air). Il s'agit de l'adaptation en prise de vue réelle de la série animée culte 'Avatar: The Last Airbender' (Avatar: Le Dernier Maître de l'air)."
    },
    {
        "question": "Quelle série en prise de vue réelle produite par Netflix en 2024 adapte à nouveau l'univers d'Avatar: The Last Airbender ?",
        "answer": "Il s'agit de la série de fantasy en prise de vue réelle 'Avatar: The Last Airbender' produite par Netflix, qui propose une adaptation fidèle et spectaculaire de la série d'animation originale."
    },
    {
        "question": "Quelle série japonaise en prise de vue réelle de Netflix de 2023 adapte le manga de combat surnaturel des années 90 de Yoshihiro Togashi ?",
        "answer": "La série est 'Yu Yu Hakusho'. Produite par Netflix en prise de vue réelle, elle transpose les combats de détectives spirituels du célèbre manga de l'auteur de *Hunter x Hunter*."
    },
    {
        "question": "Quelle série en prise de vue réelle de Netflix de 2021 a adapté de manière très débattue l'animé de science-fiction spatial légendaire de Shinichiro Watanabe ?",
        "answer": "La série est 'Cowboy Bebop' de Netflix. Cette version en prise de vue réelle a été annulée après une seule saison en raison des critiques des fans face aux libertés prises par rapport à l'animé original."
    },
    {
        "question": "Quel film en prise de vue réelle produit par Warner Bros Japan en 2018 adapte l'arc du shinigami suppléant du manga culte de Tite Kubo ?",
        "answer": "Le film est 'Bleach'. Cette adaptation japonaise en prise de vue réelle transpose fidèlement le début du manga, en se concentrant sur la transformation d'Ichigo Kurosaki en Shinigami."
    },
    {
        "question": "Quelle série de films japonais en prise de vue réelle est largement saluée par les fans comme l'une des meilleures adaptations de mangas de samouraïs de l'histoire ?",
        "answer": "Il s'agit de la saga de films 'Rurouni Kenshin' (Kenshin le Vagabond) mettant en vedette l'acteur Takeru Satoh. Ces films sont acclamés pour la fidélité de leur intrigue et la chorégraphie spectaculaire de leurs combats de sabre."
    },
    {
        "question": "Quel film japonais en prise de vue réelle de 2019 adapte les batailles de l'époque des Royaumes Combattants du manga historique de Yasuhisa Hara ?",
        "answer": "Le film est 'Kingdom'. Réalisé par Shinsuke Sato, il propose une adaptation en prise de vue réelle épique et spectaculaire du célèbre manga militaire historique éponyme."
    },
    {
        "question": "Quelle comédie japonaise en prise de vue réelle adapte à la perfection l'humour parodique absurde du manga de Hideaki Sorachi ?",
        "answer": "Il s'agit des films en prise de vue réelle 'Gintama' réalisés par Yuichi Fukuda, acclamés pour leur capacité à retranscrire fidèlement l'humour méta et les gags déjantés de l'œuvre originale."
    },
    {
        "question": "De quel manga japonais de Garon Tsuchiya s'inspire le film coréen légendaire de vengeance de Park Chan-wook ?",
        "answer": "Il s'inspire du manga japonais 'Old Boy' (Oldboy) écrit par Garon Tsuchiya et illustré par Nobuaki Minegishi, qui raconte la séquestration inexpliquée d'un homme durant de nombreuses années."
    },
    {
        "question": "Quel réalisateur hollywoodien a réalisé en 2013 un remake américain en prise de vue réelle du film coréen culte Oldboy ?",
        "answer": "Le remake américain a été réalisé par Spike Lee, mettant en vedette Josh Brolin dans le rôle principal adapté du manga japonais original 'Old Boy'."
    },
    {
        "question": "Quel film japonais délirant en prise de vue réelle de 2008 transpose le manga comique sur le death metal et la pop de Kiminori Wakasugi ?",
        "answer": "Le film est 'Detroit Metal City' (DMC). Il met en scène l'acteur Kenichi Matsuyama incarnant un jeune homme doux forcé de jouer le leader maquillé et agressif d'un groupe de death metal."
    },
    {
        "question": "Sous quelle forme de films en deux parties a été adaptée en prise de vue réelle l'œuvre tragique L'Attaque des Titans en 2015 ?",
        "answer": "Elle a été adaptée sous la forme de deux films japonais en prise de vue réelle intitulés 'Attack on Titan' réalisés par Shinji Higuchi, qui ont suscité des avis mitigés pour leurs importants écarts scénaristiques."
    },
    {
        "question": "Quel réalisateur japonais de films d'action cultes a réalisé l'adaptation en prise de vue réelle du manga JoJo's Bizarre Adventure en 2017 ?",
        "answer": "L'adaptation a été réalisée par le célèbre réalisateur Takashi Miike sous le titre 'JoJo's Bizarre Adventure: Diamond Is Unbreakable Chapter I', adaptant la quatrième partie du manga."
    },
    {
        "question": "Quel réalisateur japonais a réalisé en 2012 le film en prise de vue réelle Ace Attorney basé sur la franchise de Capcom ?",
        "answer": "Le film a été réalisé par Takashi Miike, proposant une adaptation très théâtrale et colorée reproduisant fidèlement les coiffures et expressions cultes du jeu vidéo original."
    },
    {
        "question": "Quel film japonais de 2014 en prise de vue réelle a adapté les aventures du gentleman cambrioleur Lupin III créé par Monkey Punch ?",
        "answer": "Le film est 'Lupin the 3rd' (Lupin III) réalisé par Ryuhei Kitamura, qui met en scène les célèbres cambriolages de la bande de Lupin en prise de vue réelle."
    },
    {
        "question": "Quel film dramatique japonais en prise de vue réelle de 2005 adapte à la perfection le manga musical de Ai Yazawa ?",
        "answer": "Le film est 'Nana'. Il met en scène les actrices Mika Nakashima et Aoi Miyazaki incarnant les deux colocataires aux personnalités opposées, capturant l'esthétique punk-rock et l'émotion du manga culte."
    },
    {
        "question": "Quel film japonais en prise de vue réelle adapte le manga de dessin et de duels éditoriaux des auteurs de Death Note ?",
        "answer": "Le film est 'Bakuman' (2015). Il retrace la carrière de deux lycéens cherchant à publier leur manga dans le prestigieux magazine *Weekly Shonen Jump*."
    },
    {
        "question": "Quel film de science-fiction japonais en prise de vue réelle de 2010 adapte le classique d'animation spatiale Space Battleship Yamato de Leiji Matsumoto ?",
        "answer": "Le film est 'Space Battleship Yamato' réalisé par Takashi Yamazaki, offrant une adaptation spectaculaire avec d'importants effets visuels spatiaux."
    },

    # --- GROUPE C: INSPIRATIONS CULTURELLES & PARALLELES (20 relations) ---
    {
        "question": "Quel type de jeux vidéo extrêmement populaire et étant une part importante des FPS modernes est grandement inspiré par un manga au titre éponyme ?",
        "answer": "Il s'agit du genre 'Battle Royale' (Fortnite, PUBG, Apex Legends). Il tire son nom et son concept de survie en arène fermée où les participants s'entretuent jusqu'au dernier survivant du célèbre roman et manga 'Battle Royale' de Koushun Takami."
    },
    {
        "question": "Quel plan de dérapage à moto ultra-culte d'un film d'animation japonais de 1988 est constamment reproduit en hommage dans le cinéma et les jeux vidéo occidentaux ?",
        "answer": "Il s'agit de la célèbre scène de freinage en dérapage latéral de la moto rouge de Kaneda dans le film chef-d'œuvre 'Akira' réalisé par Katsuhiro Otomo. Cet angle de caméra iconique a été imité dans *Matrix*, *Cyberpunk 2077*, *Ready Player One* ou encore *Spider-Man: Into the Spider-Verse*."
    },
    {
        "question": "De quel chef-d'œuvre d'animation de science-fiction japonais de Katsuhiro Otomo s'inspirent les créateurs de la série Stranger Things pour les pouvoirs d'Eleven ?",
        "answer": "Ils s'inspirent directement du film d'animation 'Akira'. L'histoire d'enfants cobayes dotés de pouvoirs psychiques démesurés élevés dans un laboratoire secret (comme Eleven et Tetsuo/Kaneda) est un hommage direct à l'œuvre d'Otomo."
    },
    {
        "question": "Quel film de science-fiction de Christopher Nolan est directement influencé par le film d'animation japonais Paprika de Satoshi Kon ?",
        "answer": "Le film est 'Inception' (2010). Christopher Nolan a reconnu l'influence majeure du chef-d'œuvre d'animation psychédélique 'Paprika' de Satoshi Kon, notamment pour l'idée d'un appareil permettant d'entrer dans les rêves et plusieurs scènes visuelles (comme le couloir d'hôtel en rotation)."
    },
    {
        "question": "Quelle scène de baignoire angoissante du film culte Requiem for a Dream de Darren Aronofsky est tirée d'un film d'animation japonais ?",
        "answer": "Elle est tirée directement du thriller psychologique d'animation 'Perfect Blue' de Satoshi Kon. Pour pouvoir reproduire fidèlement cette scène de détresse sous l'eau à l'identique dans son film en prise de vue réelle, le réalisateur Darren Aronofsky en avait acheté les droits de reproduction officiels."
    },
    {
        "question": "Quel thriller psychologique hollywoodien oscarisé avec Natalie Portman est grandement inspiré par Perfect Blue de Satoshi Kon ?",
        "answer": "Le film est 'Black Swan' de Darren Aronofsky. Il partage d'immenses similitudes thématiques et visuelles avec 'Perfect Blue', explorant les hallucinations, la paranoïa, et la perte de repères d'une artiste face à son double psychologique."
    },
    {
        "question": "Quel classique d'animation de Disney a fait l'objet d'une longue controverse concernant ses ressemblances troublantes avec la série animée Le Roi Léo d'Osamu Tezuka ?",
        "answer": "Il s'agit du film 'Le Roi Lion' (The Lion King, 1994) de Disney. Il a suscité une vive controverse internationale en raison de ses similitudes thématiques, de personnages (Kimba/Simba) et de plans de caméra identiques avec le chef-d'œuvre 'Le Roi Léo' (Jungle Taitei) créé par le père du manga Osamu Tezuka."
    },
    {
        "question": "Quel animé de Hayao Miyazaki a influencé les thèmes écologiques et la création des célèbres créatures de transport 'Chocobos' dans la franchise de jeux vidéo Final Fantasy ?",
        "answer": "Il s'agit de 'Nausicaä de la Vallée du Vent' (Nausicaä of the Valley of the Wind). Le créateur de *Final Fantasy*, Hironobu Sakaguchi, a reconnu s'être grandement inspiré de l'esthétique et des valeurs écologiques de Nausicaä, y compris les oiseaux de monture géants qui ont inspiré le design des mythiques Chocobos."
    },
    {
        "question": "Quel film de science-fiction hollywoodien géant réalisé par Guillermo del Toro rend un hommage direct aux animés de mechas combattant des monstres géants ?",
        "answer": "Le film est 'Pacific Rim' (2013). Guillermo del Toro l'a conçu comme une lettre d'amour monumentale aux animés de robots géants ('mechas') et de monstres géants ('kaijus') japonais, s'inspirant ouvertement d'œuvres comme *Neon Genesis Evangelion* ou *Mazinger Z*."
    },
    {
        "question": "Quel animé de mechas révolutionnaire a instauré en 1979 le genre du 'Real Robot', transformant les robots géants magiques en armes militaires réalistes ?",
        "answer": "Il s'agit de 'Mobile Suit Gundam' (1979) réalisé par Yoshiyuki Tomino. Cette série a marqué un tournant historique en rejetant les super-pouvoirs des super-robots au profit d'une approche de science-fiction militaire réaliste et technologique."
    },
    {
        "question": "Quelles influences majeures de japanimation ont revendiqué les sœurs Wachowski pour la création de la trilogie cinématographique Matrix ?",
        "answer": "Elles ont cité le manga et film cyberpunk culte 'Ghost in the Shell' de Mamoru Oshii comme leur principale source d'inspiration, reprenant directement le concept de câble branché à la base du cou, la pluie de codes numériques verts et plusieurs plans iconiques."
    },
    {
        "question": "Quel univers cinématographique post-apocalyptique occidental a directement inspiré le manga culte Ken le Survivant ?",
        "answer": "L'univers est celui de la saga de films d'action australiens 'Mad Max' (particulièrement *Mad Max 2*). Le mangaka Tetsuo Hara s'en est grandement inspiré pour concevoir le monde désertique dévasté et les gangs de motards punks de 'Hokuto no Ken' (Fist of the North Star)."
    },
    {
        "question": "Quel chef-d'œuvre de film de science-fiction de Ridley Scott a servi d'influence visuelle absolue pour le cyberpunk de Ghost in the Shell ?",
        "answer": "Il s'agit de 'Blade Runner' (1982). L'esthétique de métropole étouffante saturée de néons et d'écrans publicitaires géants a directement inspiré Masamune Shirow pour son écriture cyberpunk."
    },
    {
        "question": "Quel créateur de jeux vidéo légendaire s'est inspiré de Blade Runner pour concevoir le jeu d'aventure Snatcher en 1988 ?",
        "answer": "Il s'agit de Hideo Kojima (le créateur de *Metal Gear*). Son jeu d'aventure cyber-thriller 'Snatcher' rend de vibrants hommages à l'univers de 'Blade Runner' et au film d'animation 'Akira'."
    },
    {
        "question": "Quel jeu d'aventure cyberpunk culte de Hideo Kojima de 1988 combine d'importantes influences de science-fiction occidentale et d'animation japonaise ?",
        "answer": "Le jeu est 'Snatcher'. Véritable lettre d'amour à la science-fiction, il s'inspire ouvertement des androïdes de 'Blade Runner' et des technologies d'anticipation de 'Akira'."
    },
    {
        "question": "De quelle manière les effets visuels de Matrix ont-ils influencé la japanimation au début des années 2000 ?",
        "answer": "La trilogie *Matrix* a popularisé des techniques de ralentis extrêmes et de caméras circulaires (Bullet Time) qui ont été immédiatement réadoptées et stylisées dans des séries comme 'Ghost in the Shell: Stand Alone Complex' ou des scènes d'action de studios comme Madhouse."
    },
    {
        "question": "Quelle saga cinématographique de science-fiction américaine de George Lucas a grandement influencé la création spatiale et les combats de sabre laser dans Mobile Suit Gundam ?",
        "answer": "Il s'agit de la saga 'Star Wars'. L'idée des sabres thermiques (Beam Sabers) et la dimension d'empire galactique affrontant une alliance rebelle dans *Gundam* sont des clins d'œil directs à Star Wars."
    },
    {
        "question": "Quel film d'horreur spatiale de Ridley Scott a directement servi d'inspiration esthétique et thématique à Nintendo pour concevoir sa saga de jeux vidéo Metroid ?",
        "answer": "Le film est 'Alien' (1979). La franchise 'Metroid' en tire son atmosphère de solitude spatiale oppressante, les monstres parasites extra-terrestres, et le design biomécanique, allant jusqu'à nommer le principal antagoniste de l'héroïne Samus Aran, 'Ridley', en hommage au réalisateur."
    },
    {
        "question": "Quelle franchise de jeux vidéo de science-fiction de Nintendo met en scène une chasseuse de primes solitaire et s'inspire du film d'horreur Alien ?",
        "answer": "La franchise est 'Metroid'. L'héroïne Samus Aran explore des planètes isolées infestées de créatures extraterrestres menaçantes calquées sur l'esthétique du xénomorphe de Ridley Scott."
    },
    {
        "question": "Quelle mythologie d'horreur littéraire de H.P. Lovecraft est régulièrement reprise sous forme de parodies mignonnes ou d'entités magiques dans la japanimation ?",
        "answer": "Il s'agit du 'Mythe de Cthulhu'. Il a inspiré l'animé comique parodique 'Haiyore! Nyaruko-san' (où les divinités cosmiques sont des filles d'animes) ainsi que les aspects mystiques et de folie de la classe Foreigner dans la franchise *Fate*."
    },

    # --- GROUPE D: ANIME/MANGA <-> NOVEL/BOOK BRIDGES (20 relations) ---
    {
        "question": "Quel light novel et animé culte a popularisé à l'extrême en 2012 le concept de réalité virtuelle et de personnages piégés dans un jeu vidéo de type MMORPG ?",
        "answer": "Il s'agit de 'Sword Art Online' (SAO) écrit par Reki Kawahara. Cette œuvre a agi comme le pionnier absolu qui a déclenché l'immense tendance contemporaine du genre Isekai et des intrigues de mondes virtuels."
    },
    {
        "question": "Quel animé de fantasy et d'Isekai acclamé se distingue par son approche réaliste de l'économie, de la politique et des mécanismes internes d'un MMORPG ?",
        "answer": "L'animé est 'Log Horizon' écrit par Mamare Touno. Contrairement aux autres Isekai, il se concentre sur l'organisation sociale et politique de milliers de joueurs soudainement piégés dans le jeu vidéo 'Elder Tale'."
    },
    {
        "question": "Quel animé de fantasy met en scène un chef de guilde squelettique surpuissant piégé dans son propre jeu vidéo en ligne après sa fermeture ?",
        "answer": "Il s'agit de 'Overlord' adapté des light novels de Kugane Maruyama. Le protagoniste Ainz Ooal Gown doit y régner sur ses serviteurs PNJs maléfiques tout en découvrant ce nouveau monde."
    },
    {
        "question": "Quel animé d'Isekai et de stratégie met en scène un frère et une sœur joueurs d'élite transportés dans un monde où tout conflit se résout par des jeux de société ?",
        "answer": "L'animé est 'No Game No Life' adapté des light novels de Yuu Kamiya. Les deux protagonistes Sora et Shiro cherchent à y conquérir le trône mondial en utilisant leur génie tactique lors de duels ludiques."
    },
    {
        "question": "Quel est le titre du light novel original écrit par Hiroshi Sakurazaka qui a servi de base au film hollywoodien Edge of Tomorrow ?",
        "answer": "Le titre original est 'All You Need Is Kill'. Ce court roman de science-fiction publié en 2004 met en scène un soldat piégé dans une boucle temporelle lors d'une invasion extraterrestre."
    },
    {
        "question": "Quel mangaka de génie, célèbre pour avoir illustré Death Note, a réalisé l'adaptation en manga officielle de All You Need Is Kill ?",
        "answer": "L'adaptation en manga a été illustrée par Takeshi Obata, le célèbre dessinateur de *Death Note* et *Bakuman*, offrant un style graphique spectaculaire à l'histoire originale."
    },
    {
        "question": "Quel animé humoristique de Netflix met en scène un terrifiant chef yakuza légendaire devenu un mari au foyer dévoué ?",
        "answer": "L'animé est 'La Voie du tablier' (Gokushufudou). Il s'agit de l'adaptation du manga comique éponyme mettant en scène Tatsu, 'le Dragon immortel', qui applique la rigueur et les codes des yakuzas aux tâches ménagères."
    },
    {
        "question": "Quel manga de survie en arène urbaine a été adapté par Netflix en une série en prise de vue réelle japonaise au succès planétaire ?",
        "answer": "Le manga est 'Alice in Borderland' (Imawa no Kuni no Arisu) de Haro Aso. L'adaptation en prise de vue réelle de Netflix est devenue l'une des séries japonaises les plus regardées dans le monde."
    },
    {
        "question": "Quel chef-d'œuvre de manga d'horreur de Hitoshi Iwaaki a inspiré une récente adaptation en série live-action sud-coréenne sur Netflix en 2024 ?",
        "answer": "Le manga est 'Parasyte' (Kiseijuu). Il a inspiré l'adaptation en prise de vue réelle coréenne 'Parasyte: The Grey' réalisée par Yeon Sang-ho, qui se déroule dans le même univers d'invasion parasitaire."
    },
    {
        "question": "Quel roman classique de science-fiction de Sakyo Komatsu a été adapté en un magnifique animé tragique de Netflix par le réalisateur Masaaki Yuasa ?",
        "answer": "Le roman est 'La Submersion du Japon' (Nihon Chinmotsu). Il a été adapté sous la forme de l'animé 'Japan Sinks: 2020' par le réalisateur Masaaki Yuasa."
    },
    {
        "question": "Quel animé policier et historique de 2007 se déroulant à New York durant la Prohibition adapte les light novels chorégraphiés de Ryohgo Narita ?",
        "answer": "L'animé est 'Baccano!'. Il propose un récit non-linéaire spectaculaire et choral mêlant mafieux, alchimistes et créatures immortelles à bord d'un train transcontinental."
    },
    {
        "question": "Quel animé urbain fantastique se déroulant dans le quartier d'Ikebukuro à Tokyo est l'adaptation de light novels de Ryohgo Narita ?",
        "answer": "L'animé est 'Durarara!!'. Il explore les destins croisés de gangs de couleurs, de forums de discussion en ligne secrets, et d'une motarde sans tête issue du folklore irlandais."
    },
    {
        "question": "Quelle série de light novels de Nisio Isin, réputée pour ses dialogues brillants et l'animation expérimentale de Shaft, débute par Bakemonogatari ?",
        "answer": "Il s'agit de la franchise 'Monogatari Series'. Elle débute par les light novels 'Bakemonogatari' et suit les enquêtes surnaturelles de Koyomi Araragi aidant des jeunes filles en proie à des esprits folkloriques."
    },
    {
        "question": "Quel animé historique de 12 épisodes de Nisio Isin se distingue par sa quête de 12 sabres légendaires et son style d'animation minimaliste unique ?",
        "answer": "L'animé est 'Katanagatari'. Adapté des light novels éponymes de Nisio Isin, il suit le voyage de l'épéiste sans sabre Shichika Yasuri et de la stratège Togame."
    },
    {
        "question": "Quelle franchise de light novels de fantasy des années 90 associant magie destructrice et comédie a défini le genre de l'animé fantastique de cette décennie ?",
        "answer": "Il s'agit de 'Slayers' écrit par Hajime Kanzaka. Menée par la magicienne Lina Inverse, cette œuvre culte a posé les bases de la fantasy comique dans l'animation."
    },
    {
        "question": "Quel light novel de dark fantasy explore de manière brutale et psychologique les boucles de réincarnation douloureuse d'un protagoniste ordinaire dans un autre monde ?",
        "answer": "Il s'agit de 'Re:Zero - Starting Life in Another World' écrit par Tappei Nagatsuki. L'œuvre est célèbre pour le pouvoir du protagoniste Subaru Natsuki de remonter le temps en mourant."
    },
    {
        "question": "Quel light novel axé sur la construction de nation fantastique met en scène un homme réincarné sous la forme d'un slime doté de compétences divines d'assimilation ?",
        "answer": "Il s'agit de 'That Time I Got Reincarnated as a Slime' (Moi, quand je me réincarne en Slime) de Fuse, suivant la création de la Fédération de Tempest par le slime Rimuru."
    },
    {
        "question": "Quel célèbre web novel coréen (Manhwa) mettant en scène le chasseur Sung Jin-woo a été adapté en un animé à succès mondial en 2024 ?",
        "answer": "Il s'agit de 'Solo Leveling' (Na Honjaman Level Up) écrit par Chugong. L'animé retrace l'ascension du chasseur le plus faible de l'humanité obtenant le pouvoir unique de 'monter de niveau'."
    },
    {
        "question": "Quel light novel de fantasy explore la rédemption difficile d'un héros convoqué pour porter l'arme de protection la plus méprisée de son nouveau monde ?",
        "answer": "Il s'agit de 'The Rising of the Shield Hero' (Tate no Yuusha no Nariagari) écrit par Aneko Yusagi, axé sur le combat de Naofumi Iwatani pour laver son honneur."
    },
    {
        "question": "Quel light novel pionnier est considéré par les fans comme le père fondateur du renouveau contemporain du genre Isekai en retraçant la vie entière d'un slacker réincarné ?",
        "answer": "Il s'agit de 'Mushoku Tensei: Jobless Reincarnation' (Mushoku Tensei: Isekai Ittara Honki Dasu) écrit par Rifujin na Magonote, qui a fixé la majorité des codes et clichés de l'Isekai moderne."
    }
]
