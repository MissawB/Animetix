# Japanese Manga/Anime Market Database Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the Japanese manga publishers, anime distributors, production companies, and TV networks into the Otaku knowledge base, SFT dataset generator, and DPO compiler, mirroring the French market database structure.

**Architecture:** Create a separate `japanese_market_db.py` module containing metadata dictionaries and relational QA items in French. Integrate it by updating the ChromaDB indexer, SFT compiler generators, and DPO substitution mappings.

**Tech Stack:** Python 3.12, Pytest, Django, ChromaDB, Pydantic.

---

### Task 1: Create the Japanese Market Database Module

**Files:**
- Create: [japanese_market_db.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/japanese_market_db.py)

- [ ] **Step 1: Write `japanese_market_db.py` content**
  Write the database file containing:
  *   Import `SEIYUU_PROFILES` from `songs_and_seiyuu_db.py` as `JAPANESE_VOICE_ACTORS`.
  *   `JAPANESE_MANGA_PUBLISHERS` (15 Japanese manga publishing giants).
  *   `JAPANESE_ANIME_DISTRIBUTORS` (10 major Japanese TV stations, production groups, and distributors).
  *   `JAPANESE_MARKET_RELATIONS` (40 manual French QA items).
  
  ```python
  # -*- coding: utf-8 -*-
  """
  Base de données du marché japonais du manga et de l'animation : 15 éditeurs japonais,
  10 diffuseurs/comités de production/chaînes TV au Japon,
  et 40 questions-réponses relationnelles entièrement rédigées en français.
  """
  from songs_and_seiyuu_db import SEIYUU_PROFILES as JAPANESE_VOICE_ACTORS

  JAPANESE_MANGA_PUBLISHERS = {
      "Shūeisha": {
          "definition": "Le géant absolu de l'édition de mangas au Japon, célèbre pour son magazine Weekly Shōnen Jump.",
          "origin": "Fondée en 1925 comme filiale de Shōgakukan avant de devenir indépendante.",
          "examples": "*One Piece*, *Dragon Ball*, *Naruto*, *Bleach*, *Demon Slayer*, *Jujutsu Kaisen*.",
          "impact": "Domine le marché mondial du shonen et a propulsé le manga dans l'ère de la culture de masse globale."
      },
      "Kōdansha": {
          "definition": "La plus grande maison d'édition littéraire du Japon, éditrice du Weekly Shōnen Magazine et de Bessatsu Shōnen Magazine.",
          "origin": "Fondée en 1909 par Seiji Noma, publiant à l'origine des magazines littéraires classiques.",
          "examples": "*L'Attaque des Titans*, *Fairy Tail*, *GTO*, *Vinland Saga*, *Akira*, *Ghost in the Shell*.",
          "impact": "Principal rival historique de Shūeisha, réputée pour ses œuvres seinen et shonen à forte identité artistique."
      },
      "Shōgakukan": {
          "definition": "Maison d'édition japonaise historique majeure, éditrice du magazine Weekly Shōnen Sunday.",
          "origin": "Fondée en 1922 pour publier des magazines éducatifs destinés aux écoles primaires du Japon.",
          "examples": "*Détective Conan*, *Frieren*, *Inuyasha*, *Monster*, *Ranma 1/2*, *Magi*.",
          "impact": "Pionnière de l'éducation par la bande dessinée, combinant récits d'aventures poétiques et comédies de mœurs cultes."
      },
      "Kadokawa Future Publishing": {
          "definition": "Conglomérat de divertissement japonais dominant le marché des Light Novels et de la pop-culture otaku.",
          "origin": "Fondée à Tokyo après la Seconde Guerre mondiale par Genyoshi Kadokawa en 1945.",
          "examples": "*Sword Art Online*, *Re:Zero*, *Neon Genesis Evangelion* (manga), *Overlord*.",
          "impact": "Le roi incontesté de l'adaptation transmédiatique (médiamix), reliant romans légers, mangas et animes."
      },
      "Square Enix Manga": {
          "definition": "Division d'édition de mangas de l'éditeur de jeux vidéo Square Enix, célèbre pour son mensuel Gangan.",
          "origin": "Débute ses activités d'édition en 1991 sous l'égide d'Enix avant la fusion historique avec Square.",
          "examples": "*Fullmetal Alchemist*, *Soul Eater*, *Blast of Tempest*, *My Dress-Up Darling*.",
          "impact": "A marié l'esthétique graphique du jeu de rôle (RPG) avec la narration manga de combat et de fantasy."
      },
      "Hakusensha": {
          "definition": "Maison d'édition japonaise réputée pour ses magazines de mangas shōjos et seinens de haute qualité artistique.",
          "origin": "Créée en 1973 par scission amicale du groupe de Shūeisha pour explorer des niches éditoriales ciblées.",
          "examples": "*Berserk*, *Fruits Basket*, *March Comes in Like a Lion*, *Angel Sanctuary*.",
          "impact": "Héberge le chef-d'œuvre Seinen *Berserk* et des références shōjos de romance sentimentale mondiales."
      },
      "Akita Shoten": {
          "definition": "Maison d'édition japonaise spécialisée dans les mangas d'action intenses et le magazine Weekly Shōnen Champion.",
          "origin": "Fondée en 1948 par Yasuharu Akita après avoir quitté Shūeisha.",
          "examples": "*Baki*, *Saint Seiya: The Lost Canvas*, *Yowamushi Pedal*, *Squid Girl*.",
          "impact": "Célèbre pour ses récits de furyo (délinquants lycéens) et ses sagas de combats sportifs et d'arts martiaux virils."
      },
      "Futabasha": {
          "definition": "Éditeur japonais célèbre pour ses mangas comiques grand public et ses publications seinen cultes.",
          "origin": "Fondée en 1948 à Tokyo, orientée vers les mangas humoristiques et de divertissement populaire.",
          "examples": "*Crayon Shin-chan*, *Lupin III*, *Orange*, *Our Journeys*.",
          "impact": "A édité *Lupin III*, le premier grand manga seinen d'action moderne, et le phénomène familial *Crayon Shin-chan*."
      },
      "Tokuma Shoten": {
          "definition": "Maison d'édition japonaise ayant joué un rôle historique dans la fondation et le financement du Studio Ghibli.",
          "origin": "Fondée en 1954 par Yasuyoshi Tokuma, s'étendant rapidement à l'industrie du disque et du cinéma d'animation.",
          "examples": "*Nausicaä de la Vallée du Vent* (manga), *Legend of the Galactic Heroes*, *Monster Musume*.",
          "impact": "A financé les premiers chefs-d'œuvre cinématographiques de Hayao Miyazaki et Isao Takahata."
      },
      "Houbunsha": {
          "definition": "L'éditeur pionnier du format manga à quatre cases (Yonkoma) et du magazine Manga Time Kirara.",
          "origin": "Fondée en 1950 sous le nom de Kabushiki Gaisha Houbunsha, s'affirmant comme le spécialiste du manga humoristique court.",
          "examples": "*K-ON!*, *Laid-Back Camp* (*Yuru Camp*), *Bocchi the Rock!*, *Gakkou Gurashi!*.",
          "impact": "A popularisé le sous-genre du 'CGDCT' (Cute Girls Doing Cute Things) et les mangas de tranches de vie musicales ou de plein air."
      },
      "Leed Publishing": {
          "definition": "Éditeur spécialisé dans les récits historiques réalistes (Gekiga) et les aventures de samouraïs.",
          "origin": "Créée par le mangaka pionnier Takao Saito (auteur de Golgo 13) en tant que studio d'édition indépendant.",
          "examples": "*Golgo 13*, mangas de sabre d'époque féodale de grands maîtres.",
          "impact": "Conserve le patrimoine et la rigueur esthétique du Gekiga d'action et d'espionnage classique."
      },
      "Shodensha": {
          "definition": "Maison d'édition japonaise réputée pour ses mangas Josei (destinés aux femmes adultes) et ses thématiques psychologiques.",
          "origin": "Fondée en 1970, développant un catalogue littéraire et de mangas exigeants et réalistes.",
          "examples": "*Helter Skelter*, *Piece of Cake*, *Princess Jellyfish* (variante).",
          "impact": "Aborde avec audace les questions d'identité féminine, de chirurgie esthétique et de relations sociales adultes."
      },
      "Ichijinsha": {
          "definition": "Éditeur japonais spécialisé dans les publications d'animes et mangas de type Yuri, Boys' Love et Otaku.",
          "origin": "Née en 2005 de la fusion de Studio DNA et de l'éditeur de fantasy Issaisha.",
          "examples": "*Wotakoi: Love is Hard for Otaku*, *YuruYuri*, *My Next Life as a Villainess*.",
          "impact": "Le spécialiste des comédies romantiques geeks et des relations amoureuses au sein de la sous-culture otaku."
      },
      "Mag Garden": {
          "definition": "Éditeur de mangas japonais axé sur la fantasy, l'aventure et les récits de mystères soignés.",
          "origin": "Fondée en 2001 par Yoshihiro Hosaka après une scission amicale d'éditeurs de Square Enix.",
          "examples": "*The Ancient Magus Bride*, *Aria*, *Peacemaker Kurogane*, *Tales of Symphonia* (manga).",
          "impact": "Produit des mangas de fantasy onirique et atmosphérique d'une grande beauté graphique."
      },
      "Media Factory": {
          "definition": "Marque éditoriale de Kadokawa, célèbre pour son label de Light Novels MF Bunko J et ses adaptations animées phares.",
          "origin": "Fondée en 1986 par Recruit avant d'être rachetée et intégrée dans le conglomérat Kadokawa en 2011.",
          "examples": "*No Game No Life*, *Re:Zero* (Light Novel d'origine), *Zero no Tsukaima*, *Classroom of the Elite*.",
          "impact": "A grandement favorisé l'essor mondial du genre isekai et des héros calculateurs dans les Light Novels."
      }
  }

  JAPANESE_ANIME_DISTRIBUTORS = {
      "Aniplex": {
          "definition": "La filiale de Sony Music Japan spécialisée dans la production, la planification et la distribution mondiale d'animes.",
          "origin": "Fondée à Tokyo en 1995 sous le nom de Sony Pictures Entertainment Visual Works avant de prendre son nom actuel en 2003.",
          "examples": "*Demon Slayer*, *Fate/Zero*, *Sword Art Online*, *Fullmetal Alchemist*, *Bocchi the Rock!*, *Lycoris Recoil*.",
          "impact": "S'impose comme le leader de la production d'animes d'action et détient des licences majeures à fort impact commercial international."
      },
      "Tōhō": {
          "definition": "La plus grande société de production et de distribution cinématographique du Japon, majeure pour les films d'animes.",
          "origin": "Fondée en 1932 par Ichizō Kobayashi, célèbre pour distribuer les films de Godzilla et d'animation grand public.",
          "examples": "*Your Name.*, *Le Voyage de Chihiro*, *Jujutsu Kaisen 0*, *My Hero Academia: The Movie*.",
          "impact": "Monopolise la distribution des plus grands succès au box-office cinématographique japonais de japanimation."
      },
      "Toei Animation": {
          "definition": "Le studio d'animation et distributeur historique le plus ancien et prolifique du Japon, pionnier de l'animation nationale.",
          "origin": "Fondée en 1948 sous le nom de Japan Animated Films avant d'être rachetée par la Toei en 1956.",
          "examples": "*Dragon Ball Z*, *One Piece*, *Sailor Moon*, *Saint Seiya*, *Slam Dunk*, *Digimon*.",
          "impact": "A créé l'âge d'or originel de l'animation japonaise et distribue les licences d'action shonen les plus longues au monde."
      },
      "Bandai Namco Filmworks": {
          "definition": "Le conglomérat d'animation réunissant le studio de méchas Sunrise et les divisions de distribution vidéo de Bandai.",
          "origin": " Sunrise a été fondé en 1972 par d'anciens membres d'Mushi Production pour concevoir des animés de science-fiction.",
          "examples": "*Mobile Suit Gundam*, *Code Geass*, *Love Live!*, *Cowboy Bebop*, *Gintama*.",
          "impact": "Détient le monopole absolu de l'animation de robots et de méchas de combat militaires et de science-fiction au Japon."
      },
      "Pony Canyon": {
          "definition": "Une entreprise de divertissement japonaise majeure, productrice de bandes-son culte et d'animes récents.",
          "origin": "Filiale du conglomérat de médias Fuji Media Holdings, établie en 1966 pour la musique puis l'audiovisuel.",
          "examples": "*L'Attaque des Titans*, *K-ON!*, *Clannad*, *Tokyo Revengers*.",
          "impact": "Assure des productions d'animes à fort impact musical et émotionnel et gère des éditions physiques de luxe."
      },
      "TV Tokyo": {
          "definition": "La chaîne de télévision nationale japonaise célèbre pour diffuser la plus grande quantité de séries d'animation en fin de journée.",
          "origin": "Lancée en 1964, elle s'est spécialisée dans les programmes de dessins animés pour enfants et adolescents pour se démarquer.",
          "examples": "*Naruto*, *Bleach*, *Pokémon*, *Gintama*, *Neon Genesis Evangelion*, *Fairy Tail*.",
          "impact": "Le principal diffuseur hertzien d'animes au Japon, dont la grille horaire a façonné la culture otaku contemporaine."
      },
      "Fuji TV": {
          "definition": "Chaîne de télévision commerciale japonaise majeure, célèbre pour sa case horaire d'animation d'avant-garde Noitamina.",
          "origin": "Fondée en 1957, elle diffuse historiquement des animés cultes de l'enfance et des œuvres seinen exigeantes.",
          "examples": "*Dragon Ball*, *One Piece* (diffusion courante), *Anohana*, *Psycho-Pass*, *The Promised Neverland*.",
          "impact": "Abrite la case Noitamina dédiée aux projets créatifs matures, artistiques et d'auteurs en dehors des codes classiques."
      },
      "MBS TV": {
          "definition": "Chaîne de télévision basée à Osaka (Mainichi Broadcasting System), diffuseuse historique majeure de la japanimation tardive (Late-night anime).",
          "origin": "Lancée en 1951, elle a initié les blocs de diffusion d'animes pour adultes programmés tard dans la nuit au Japon.",
          "examples": "*Code Geass*, *L'Attaque des Titans*, *Jujutsu Kaisen*, *Mobile Suit Gundam: Iron-Blooded Orphans*.",
          "impact": "Le pionnier et diffuseur principal des séries d'action intenses du créneau 'Animeism' ciblant les adolescents et adultes."
      },
      "NHK": {
          "definition": "La compagnie de télédiffusion publique nationale du Japon, diffusant des animés éducatifs, familiaux et d'envergure nationale.",
          "origin": "Fondée en 1925 comme station de radio publique, calquée sur le modèle de service public de la BBC.",
          "examples": "*L'Attaque des Titans* (saison finale/blocs d'infos), *Vinland Saga* (Saison 1), *Cardcaptor Sakura*, *Log Horizon*.",
          "impact": "Garantit des diffusions sans publicité de récits d'aventures exigeants et d'adaptations de prestige reconnues par l'État."
      },
      "Kadokawa Anime": {
          "definition": "La division de production et de distribution audiovisuelle de Kadokawa, finançant les adaptations de ses propres romans et mangas.",
          "origin": "Intégrée au sein des activités transmédias de l'éditeur Kadokawa pour contrôler la chaîne de droits de A à Z.",
          "examples": "*La Mélancolie de Haruhi Suzumiya*, *Lucky Star*, *Re:Zero*, *Konosuba*.",
          "impact": "A défini la ferveur otaku des années 2000 avec *Haruhi* et domine le segment des comédies isekai modernes."
      }
  }

  # --- 40 RELATIONS LIÉES AU MARCHÉ DU MANGA ET DE L'ANIMATION AU JAPON ---
  JAPANESE_MARKET_RELATIONS = [
      {
          "question": "Quelle maison d'édition japonaise publie le magazine hebdomadaire Weekly Shōnen Jump ?",
          "answer": "C'est la maison d'édition 'Shūeisha' qui publie le mythique 'Weekly Shōnen Jump' depuis son lancement en 1968, s'imposant comme le leader historique du manga de genre Nekketsu."
      },
      {
          "question": "Quelle filiale de Sony Music Japan produit et distribue les animés à succès Demon Slayer et Fate/Zero ?",
          "answer": "Il s'agit d' 'Aniplex', filiale de Sony spécialisée dans le financement, la planification et la distribution de licences majeures de japanimation."
      },
      {
          "question": "Quelle chaîne de télévision commerciale japonaise abrite la case d'animation d'avant-garde Noitamina ?",
          "answer": "La case horaire de prestige 'Noitamina' est diffusée par la chaîne japonaise 'Fuji TV', proposant des œuvres narratives matures comme Psycho-Pass."
      },
      {
          "question": "Quelle maison d'édition japonaise publie le magazine Weekly Shōnen Magazine, rival historique du Shōnen Jump ?",
          "answer": "Le 'Weekly Shōnen Magazine' est édité par la 'Kōdansha' depuis 1959, abritant des œuvres cultes comme Fairy Tail et GTO."
      },
      {
          "question": "Quel studio historique et distributeur produit et possède la licence de l'animé culte One Piece au Japon ?",
          "answer": "L'adaptation en animé de 'One Piece' est produite et distribuée au Japon par le studio légendaire 'Toei Animation' depuis 1999."
      },
      {
          "question": "Quelle maison d'édition historique japonaise publie le magazine Weekly Shōnen Sunday ?",
          "answer": "Le magazine 'Weekly Shōnen Sunday' est publié par la maison d'édition 'Shōgakukan' depuis mars 1959, célèbre pour héberger Détective Conan."
      },
      {
          "question": "Quelle chaîne de télévision hertzienne japonaise diffuse historiquement les séries animées Pokémon et Naruto au Japon ?",
          "answer": "C'est la chaîne nationale 'TV Tokyo' qui diffuse ces franchises phares dans ses créneaux de fin d'après-midi, façonnant la culture otaku."
      },
      {
          "question": "Quel géant du divertissement japonais détient les labels d'édition de romans légers MF Bunko J et Gagaga Bunko ?",
          "answer": "Il s'agit du conglomérat 'Kadokawa Future Publishing', qui domine l'ensemble du marché littéraire otaku et transmédia."
      },
      {
          "question": "Quelle maison d'édition publie le chef-d'œuvre Seinen Berserk de Kentaro Miura au Japon ?",
          "answer": "Le manga 'Berserk' de Kentaro Miura est publié au Japon par 'Hakusensha' au sein du magazine bimensuel Young Animal."
      },
      {
          "question": "Quelle chaîne publique de télévision japonaise a diffusé la saison finale de L'Attaque des Titans sans coupure publicitaire ?",
          "answer": "C'est la chaîne de télévision publique japonaise 'NHK' qui a diffusé la suite et fin de 'L'Attaque des Titans' sur son antenne générale."
      },
      {
          "question": "Quel conglomérat d'animation réunit le célèbre studio de robots Sunrise et les jouets Bandai au Japon ?",
          "answer": "Il s'agit de la société 'Bandai Namco Filmworks', qui détient la franchise de méchas militaires Mobile Suit Gundam."
      },
      {
          "question": "Quelle maison d'édition japonaise de jeux vidéo possède la filiale éditrice du manga Fullmetal Alchemist ?",
          "answer": "C'est le géant du jeu vidéo 'Square Enix Manga' qui a publié 'Fullmetal Alchemist' d'Hiromu Arakawa dans son mensuel Shōnen Gangan."
      },
      {
          "question": "Quel distributeur musical japonais historique produit les bandes-son et co-finance l'animé L'Attaque des Titans ?",
          "answer": "Il s'agit de la société de production 'Pony Canyon', filiale du groupe de médias Fuji Media Holdings."
      },
      {
          "question": "Quelle maison d'édition publie le manga humoristique familial Crayon Shin-chan de Yoshito Usui au Japon ?",
          "answer": "Crayon Shin-chan est publié par la maison d'édition japonaise 'Futabasha' depuis sa parution originale en 1990."
      },
      {
          "question": "Quelle maison d'édition japonaise a historiquement financé la création et le lancement du mythique Studio Ghibli ?",
          "answer": "Il s'agit de l'éditeur 'Tokuma Shoten', sous l'impulsion de son dirigeant Yasuyoshi Tokuma qui a soutenu le travail de Hayao Miyazaki."
      },
      {
          "question": "Quelle station de télévision d'Osaka (Mainichi) a popularisé le créneau tardif Animeism pour les séries animées adultes ?",
          "answer": "C'est la chaîne commerciale 'MBS TV' qui a initié les diffusions d'animes programmées tard dans la nuit pour un public de jeunes adultes."
      },
      {
          "question": "Quelle maison d'édition japonaise publie les comédies tranches de vie K-ON! et Bocchi the Rock! au format Yonkoma ?",
          "answer": "Ces mangas à quatre cases sont publiés par l'éditeur spécialisé 'Houbunsha' dans ses magazines affiliés Manga Time Kirara."
      },
      {
          "question": "Quelle maison d'édition japonaise est célèbre pour publier le manga culte de délinquant furyo Baki de Keisuke Itagaki ?",
          "answer": "Le manga de combat d'arts martiaux 'Baki' est publié par 'Akita Shoten' au sein du magazine Weekly Shōnen Champion."
      },
      {
          "question": "Quel studio et éditeur japonais fondé par Takao Saito publie et détient les droits du manga fleuve Golgo 13 ?",
          "answer": "Les droits et l'édition de 'Golgo 13' sont gérés par la maison d'édition 'Leed Publishing', préservant l'héritage du style Gekiga."
      },
      {
          "question": "Quelle maison d'édition japonaise est spécialisée dans les mangas de genre yuri et otaku comme Wotakoi ?",
          "answer": "Il s'agit de l'éditeur 'Ichijinsha', qui s'est fait une spécialité des comédies romantiques et des tranches de vie geek."
      },
      {
          "question": "Quelle maison d'édition japonaise publie le manga de fantasy acclamé The Ancient Magus Bride ?",
          "answer": "Ce manga de fantasy onirique est publié au Japon par la maison d'édition 'Mag Garden' depuis sa prépublication."
      },
      {
          "question": "Quelle maison d'édition japonaise publie le manga seinen dramatique Helter Skelter traitant de la chirurgie esthétique ?",
          "answer": "Ce drame psychologique culte de Kyoko Okazaki est publié au Japon par la maison d'édition 'Shodensha'."
      },
      {
          "question": "Quelle division de Kadokawa produit des animes adaptés de ses propres Light Novels comme Re:Zero et Konosuba ?",
          "answer": "Ces projets d'adaptation sont financés et planifiés par la division audiovisuelle de 'Kadokawa Anime'."
      },
      {
          "question": "Quelle maison d'édition publie le manga seinen d'action historique Kingdom de Yasuhisa Hara au Japon ?",
          "answer": "Le manga 'Kingdom' de Yasuhisa Hara est publié par 'Shūeisha' dans son magazine de prépublication hebdomadaire Weekly Young Jump."
      },
      {
          "question": "Quelle maison d'édition publie le shonen de football intense Blue Lock de Muneyuki Kaneshiro ?",
          "answer": "Le phénomène 'Blue Lock' est publié au Japon par 'Kōdansha' dans son magazine Weekly Shōnen Magazine."
      },
      {
          "question": "Quelle maison d'édition publie la comédie romantique Komi cherche ses mots de Tomohito Oda au Japon ?",
          "answer": "Le manga 'Komi cherche ses mots' est publié par la maison d'édition 'Shōgakukan' dans le magazine Weekly Shōnen Sunday."
      },
      {
          "question": "Quelle maison d'édition publie la comédie de dark fantasy Chainsaw Man de Tatsuki Fujimoto au Japon ?",
          "answer": "Le manga 'Chainsaw Man' est édité au Japon par 'Shūeisha' dans le Weekly Shōnen Jump pour la première partie."
      },
      {
          "question": "Quelle maison d'édition publie le manga seinen psychologique Oshi no Ko de Aka Akasaka au Japon ?",
          "answer": "Le manga de mystère et d'idols 'Oshi no Ko' est publié au Japon par 'Shūeisha' au sein du Weekly Young Jump."
      },
      {
          "question": "Quelle maison d'édition japonaise publie la tranche de vie post-fantasy Frieren au Japon ?",
          "answer": "Le manga 'Frieren' ('Sousou no Frieren') est publié au Japon par 'Shōgakukan' dans le Weekly Shōnen Sunday."
      },
      {
          "question": "Quelle maison d'édition publie le manga de dark fantasy post-apocalyptique L'Attaque des Titans au Japon ?",
          "answer": "La série 'L'Attaque des Titans' de Hajime Isayama a été publiée par 'Kōdansha' dans le magazine mensuel Bessatsu Shōnen Magazine."
      },
      {
          "question": "Quelle maison d'édition publie l'intégralité de la fresque JoJo's Bizarre Adventure au Japon ?",
          "answer": "Toutes les parties du manga 'JoJo's Bizarre Adventure' sont éditées par 'Shūeisha' dans le Weekly Shōnen Jump puis dans le mensuel Ultra Jump."
      },
      {
          "question": "Quelle maison d'édition a publié le manga cyberpunk pionnier Akira de Katsuhiro Otomo au Japon ?",
          "answer": "Le monument de science-fiction 'Akira' a été prépublié et édité au Japon par la maison d'édition 'Kōdansha'."
      },
      {
          "question": "Quelle maison d'édition a publié le chef-d'œuvre de science-fiction Ghost in the Shell de Masamune Shirow ?",
          "answer": "L'œuvre technologique 'Ghost in the Shell' a été prépubliée et éditée au Japon par 'Kōdansha' dans le Young Magazine."
      },
      {
          "question": "Quelle maison d'édition a publié le manga seinen dramatique de shogi March Comes in Like a Lion au Japon ?",
          "answer": "Cette œuvre de l'autrice Chica Umino est publiée au Japon par la maison d'édition 'Hakusensha'."
      },
      {
          "question": "Quelle maison d'édition japonaise publie le manga d'action Fullmetal Alchemist d'Hiromu Arakawa ?",
          "answer": "La saga 'Fullmetal Alchemist' d'Hiromu Arakawa est éditée au Japon par 'Square Enix Manga' dans le magazine Gangan."
      },
      {
          "question": "Quelle maison d'édition japonaise publie les mangas de type shôjo classiques comme Fruits Basket ?",
          "answer": "Le shōjo culte 'Fruits Basket' de Natsuki Takaya a été publié au Japon par la maison d'édition 'Hakusensha' dans le magazine Hana to Yume."
      },
      {
          "question": "Quelle maison d'édition publie le manga historique d'action samouraï Vagabond de Takehiko Inoue au Japon ?",
          "answer": "Le chef-d'œuvre 'Vagabond' de Takehiko Inoue est publié au Japon par la maison d'édition 'Kōdansha' dans le Weekly Morning."
      },
      {
          "question": "Quelle maison d'édition publie les Light Novels d'origine de la saga isekai Sword Art Online au Japon ?",
          "answer": "Les romans légers originaux de 'Sword Art Online' de Reki Kawahara sont édités par le label Dengeki Bunko de 'Kadokawa Future Publishing'."
      },
      {
          "question": "Quelle maison d'édition publie le manga seinen psychologique et d'horreur Tokyo Ghoul de Sui Ishida ?",
          "answer": "Le manga 'Tokyo Ghoul' a été prépublié et édité au Japon par 'Shūeisha' dans le magazine Weekly Young Jump."
      },
      {
          "question": "Quelle maison d'édition publie la comédie et tranche de vie comique Nicky Larson (City Hunter) au Japon ?",
          "answer": "La série mythique 'City Hunter' de Tsukasa Hojo a été publiée à l'origine au Japon par 'Shūeisha' dans le Weekly Shōnen Jump."
      }
  ]
  ```

- [ ] **Step 2: Commit**
  ```bash
  git add backend/pipeline/mlops/japanese_market_db.py
  git commit -m "feat(mlops): create Japanese manga/anime market database"
  ```

---

### Task 2: Integrate Database with the Indexer

**Files:**
- Modify: [index_otaku_knowledge.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/index_otaku_knowledge.py)

- [ ] **Step 1: Import Japanese market database**
  Add imports on line 38 in `index_otaku_knowledge.py`:
  ```python
  from japanese_market_db import (
      JAPANESE_VOICE_ACTORS,
      JAPANESE_MANGA_PUBLISHERS,
      JAPANESE_ANIME_DISTRIBUTORS,
      JAPANESE_MARKET_RELATIONS
  )
  ```

- [ ] **Step 2: Add compile logic for Japanese entries**
  Add compilation code on line 87 in `index_otaku_knowledge.py`:
  ```python
          # 6b. Doubleurs Japonais (Seiyuu)
          for name, details in JAPANESE_VOICE_ACTORS.items():
              text = f"Acteur de doublage japonais (Seiyuu) : {name}. Profil vocal : {details.get('definition', '')} Carrière : {details.get('origin', '')} Rôles VF/VO mythiques : {details.get('examples', '')} Impact : {details.get('impact', '')}"
              facts.append({"category": "Japanese Voice Actors (Seiyuu)", "title": name, "content": text})

          # 6c. Éditeurs Japonais de Mangas
          for name, details in JAPANESE_MANGA_PUBLISHERS.items():
              text = f"Maison d'édition de manga au Japon : {name}. Présentation : {details.get('definition', '')} Historique de fondation : {details.get('origin', '')} Titres phares du catalogue : {details.get('examples', '')} Impact sur le marché japonais : {details.get('impact', '')}"
              facts.append({"category": "Japanese Manga Publishers", "title": name, "content": text})

          # 6d. Diffuseurs & Distributeurs d'Anime au Japon
          for name, details in JAPANESE_ANIME_DISTRIBUTORS.items():
              text = f"Diffuseur et distributeur d'anime au Japon : {name}. Présentation : {details.get('definition', '')} Origine de la plateforme : {details.get('origin', '')} Catalogues et exclusivités : {details.get('examples', '')} Impact de diffusion : {details.get('impact', '')}"
              facts.append({"category": "Japanese Anime Distributors (JP)", "title": name, "content": text})
  ```
  And add `JAPANESE_MARKET_RELATIONS` to `all_relations` concatenation on line 108:
  ```python
          all_relations = (
              SONGS_AND_SEIYUU_RELATIONS + 
              AWARDS_AND_MAGAZINES_RELATIONS + 
              FRENCH_MARKET_RELATIONS + 
              JAPANESE_MARKET_RELATIONS +
              TRANSMEDIA_RELATIONS
          )
  ```

- [ ] **Step 3: Run dry-run compilation**
  Run: `python backend/pipeline/mlops/index_otaku_knowledge.py --dry-run`
  Expected: Successfully logs compiling Japanese entries and finishes without errors.

- [ ] **Step 4: Commit**
  ```bash
  git add backend/pipeline/mlops/index_otaku_knowledge.py
  git commit -m "feat(mlops): integrate Japanese market database with the semantic indexer"
  ```

---

### Task 3: Integrate Database with SFT Dataset Compiler

**Files:**
- Modify: [finetuning_dataset.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/finetuning_dataset.py)

- [ ] **Step 1: Import Japanese database variables**
  Add imports on line 149 in `finetuning_dataset.py`:
  ```python
  from japanese_market_db import (
      JAPANESE_VOICE_ACTORS,
      JAPANESE_MANGA_PUBLISHERS,
      JAPANESE_ANIME_DISTRIBUTORS,
      JAPANESE_MARKET_RELATIONS
  )
  ```

- [ ] **Step 2: Add instruction generators**
  Write profile and relational instruction generators in `finetuning_dataset.py` on line 1003 (just before `generate_french_market_relations_instructions`):
  ```python
  def generate_japanese_market_profile_instructions():
      """Génère 15 variations de Q&A pour chaque comédien (seiyū), éditeur et distributeur du marché japonais (600 instructions)."""
      instructions = []
      
      # 1. Comédiens de doublage japonais / seiyū (15 * 15 = 225 instructions)
      for actor, data in JAPANESE_VOICE_ACTORS.items():
          templates = [
              (f"Qui est '{actor}' dans le doublage japonais d'animés ?", f"Dans le doublage japonais (Seiyuu), '{actor}' est : {data['definition']}. Rôles cultes : {data['examples']}. Parcours : {data['origin']}"),
              (f"Présente-moi le parcours du doubleur japonais (seiyuu) '{actor}'.", f"Fiche de doublage - '{actor}' : {data['definition']} Carrière : {data['origin']}. Rôles en VO : {data['examples']}. Impact : {data['impact']}"),
              (f"Quels sont les rôles majeurs doublés par '{actor}' en version originale ?", f"Les doublages de '{actor}' incluent : {data['examples']}. Il/Elle est connu(e) comme : {data['definition']}"),
              (f"En tant que spécialiste des seiyuu, que peux-tu me dire sur '{actor}' ?", f"Spécialité Seiyuu - '{actor}' : {data['definition']} Origines : {data['origin']}. Ses rôles phares : {data['examples']}"),
              (f"Pourquoi le doublage de '{actor}' a-t-il tant marqué le public ?", f"Le doublage de '{actor}' est légendaire : {data['impact']} Il/Elle est reconnu(e) en tant que : {data['definition']}"),
              (f"Quels personnages célèbres ont la voix originale de '{actor}' ?", f"Les figures doublées par '{actor}' comprennent : {data['examples']}. Style vocal : {data['origin']}"),
              (f"Fais-moi une synthèse complète de la carrière de doublage de '{actor}'.", f"Synthèse Doublage - '{actor}' : {data['definition']}. Histoire : {data['origin']}. Rôles repères : {data['examples']}. Impact : {data['impact']}"),
              (f"Peux-tu analyser l'importance de '{actor}' pour la japanimation ?", f"L'importance de '{actor}' en VO est colossale. {data['impact']} Connu pour : {data['definition']}. Rôles majeurs : {data['examples']}"),
              (f"Quel a été le rôle de '{actor}' ou ses débuts dans le doublage d'animes ?", f"'{actor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Parcours : {data['origin']}"),
              (f"Donne des détails sur le timbre ou le registre de voix du seiyuu '{actor}'.", f"Le timbre et registre de '{actor}' se caractérisent ainsi : {data['definition']}. Ses rôles phares : {data['examples']}. Style : {data['impact']}"),
              (f"Explique comment '{actor}' insuffle de la personnalité à ses doublages au Japon.", f"L'interprétation de '{actor}' se distingue par son énergie : {data['impact']} Notamment à travers : {data['definition']}. Rôles repères : {data['examples']}"),
              (f"Quelles sont les séries majeures où l'on peut apprécier le doublage de '{actor}' ?", f"On l'entend dans plusieurs animés cultes : {data['examples']}. Profil : {data['definition']}"),
              (f"Décris le parcours artistique et le profil vocal de '{actor}'.", f"Parcours de '{actor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Rôles majeurs : {data['examples']}"),
              (f"Analyse l'importance historique et l'héritage du seiyuu '{actor}' pour les passionnés.", f"L'héritage de '{actor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Rôles repères : {data['examples']}"),
              (f"Qu'est-ce qui rend '{actor}' incontournable dans le paysage du doublage japonais ?", f"'{actor}' est incontournable en tant que : {data['definition']}. Ses doublages populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
          ]
          for q, a in templates:
              instructions.append({"instruction": q, "input": "", "output": a})
              
      # 2. Éditeurs de mangas au Japon (15 * 15 = 225 instructions)
      for publisher, data in JAPANESE_MANGA_PUBLISHERS.items():
          templates = [
              (f"Qui est l'éditeur japonais '{publisher}' dans le milieu du manga ?", f"Sur le marché japonais, '{publisher}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}"),
              (f"Présente-moi le profil et l'impact sur le marché de l'éditeur '{publisher}'.", f"Fiche Éditeur - '{publisher}' : {data['definition']} Création : {data['origin']}. Mangas clés : {data['examples']}. Impact : {data['impact']}"),
              (f"Quelles sont les œuvres emblématiques publiées par '{publisher}' au Japon ?", f"Les licences phares éditées par '{publisher}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}"),
              (f"En tant que spécialiste du marché du manga au Japon, que peux-tu me dire sur '{publisher}' ?", f"Marché japonais - '{publisher}' : {data['definition']} Histoire : {data['origin']}. Succès : {data['examples']}"),
              (f"Pourquoi l'éditeur '{publisher}' a-t-il rencontré un si grand succès au Japon ?", f"Le succès éditorial de '{publisher}' s'explique par sa ligne éditoriale : {data['impact']} Définition : {data['definition']}"),
              (f"Quels mangas célèbres sont publiés sous le label de '{publisher}' ?", f"Les titres édités par '{publisher}' comprennent : {data['examples']}. Démarche : {data['origin']}"),
              (f"Fais-moi une synthèse complète de l'historique de la maison d'édition '{publisher}'.", f"Synthèse Éditeur - '{publisher}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}"),
              (f"Peux-tu analyser l'importance de '{publisher}' pour la popularisation du manga ?", f"L'importance de '{publisher}' au Japon est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}"),
              (f"Quel a été le rôle de '{publisher}' dans la prépublication de mangas shonen ou seinen ?", f"'{publisher}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}"),
              (f"Donne des détails sur la ligne éditoriale ou les magazines de '{publisher}'.", f"La ligne éditoriale de '{publisher}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}"),
              (f"Explique comment '{publisher}' se démarque des autres éditeurs de mangas japonais.", f"La force de '{publisher}' réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}"),
              (f"Quels sont les mangas majeurs que l'on doit lire chez '{publisher}' ?", f"On peut lire plusieurs œuvres majeures chez cet éditeur : {data['examples']}. Profil : {data['definition']}"),
              (f"Décris le parcours d'édition et le profil de '{publisher}'.", f"Parcours de '{publisher}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}"),
              (f"Analyse l'importance historique et l'héritage de '{publisher}' pour les lecteurs.", f"L'héritage de '{publisher}' est inestimable. {data['impact']} Définition : {data['definition']}. Succès clés : {data['examples']}"),
              (f"Qu'est-ce qui rend '{publisher}' incontournable dans les librairies ?", f"'{publisher}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
          ]
          for q, a in templates:
              instructions.append({"instruction": q, "input": "", "output": a})
              
      # 3. Distributeurs et diffuseurs d'animés au Japon (10 * 15 = 150 instructions)
      for distributor, data in JAPANESE_ANIME_DISTRIBUTORS.items():
          templates = [
              (f"Qu'est-ce que le diffuseur ou distributeur japonais '{distributor}' ?", f"Sur le marché japonais, '{distributor}' est : {data['definition']}. Catalogue : {data['examples']}. Origines : {data['origin']}"),
              (f"Présente-moi le profil et l'impact sur le streaming ou la télévision de '{distributor}'.", f"Fiche Diffuseur - '{distributor}' : {data['definition']} Lancement : {data['origin']}. Animés : {data['examples']}. Impact : {data['impact']}"),
              (f"Quels sont les animés phares diffusés ou produits par '{distributor}' ?", f"Les licences majeures diffusées par '{distributor}' incluent : {data['examples']}. Il s'est imposé comme : {data['definition']}"),
              (f"En tant que spécialiste de la diffusion d'animés au Japon, que peux-tu me dire sur '{distributor}' ?", f"Diffusion Japon - '{distributor}' : {data['definition']} Contexte : {data['origin']}. Succès : {data['examples']}"),
              (f"Pourquoi le service de '{distributor}' s'est-il imposé au Japon ?", f"Le succès s'explique par sa distribution : {data['impact']} Définition : {data['definition']}"),
              (f"Quels animés célèbres sont disponibles chez '{distributor}' ?", f"Les titres diffusés par '{distributor}' comprennent : {data['examples']}. Démarche : {data['origin']}"),
              (f"Fais-moi une synthèse complète de l'histoire du diffuseur ou distributeur '{distributor}'.", f"Synthèse Diffusion - '{distributor}' : {data['definition']}. Histoire : {data['origin']}. Catalogue repère : {data['examples']}. Impact : {data['impact']}"),
              (f"Peux-tu analyser l'importance de '{distributor}' pour le marché de la japanimation ?", f"L'importance de '{distributor}' au Japon est colossale. {data['impact']} Connu pour : {data['definition']}. Succès majeurs : {data['examples']}"),
              (f"Quel a été le rôle de '{distributor}' dans le développement de l'animation ou des comités de production ?", f"'{distributor}' a joué un rôle déterminant : {data['impact']} Définition : {data['definition']}. Origines : {data['origin']}"),
              (f"Donne des détails sur le mode de fonctionnement ou l'histoire de '{distributor}'.", f"Le service de '{distributor}' se caractérise ainsi : {data['definition']}. Titres phares : {data['examples']}. Style : {data['impact']}"),
              (f"Explique comment '{distributor}' a transformé la consommation d'animés au Japon.", f"La force réside dans son catalogue : {data['impact']} Définition : {data['definition']}. Œuvres repères : {data['examples']}"),
              (f"Quels sont les animés majeurs que l'on doit regarder chez '{distributor}' ?", f"On peut regarder plusieurs œuvres majeures chez ce diffuseur : {data['examples']}. Profil : {data['definition']}"),
              (f"Décris le parcours de diffusion et le profil de '{distributor}'.", f"Parcours de '{distributor}' : {data['definition']}. Origines et évolutions : {data['origin']}. Catalogues majeurs : {data['examples']}"),
              (f"Analyse l'importance historique et l'héritage de '{distributor}' pour les passionnés.", f"L'héritage de '{distributor}' est inestimable. {data['impact']} Connu pour : {data['definition']}. Succès de diffusion : {data['examples']}"),
              (f"Qu'est-ce qui rend '{distributor}' incontournable dans le streaming ou la diffusion d'animés ?", f"'{distributor}' est incontournable en tant que : {data['definition']}. Ses séries populaires ({data['examples']}) et son impact ({data['impact']}) en font une référence absolue.")
          ]
          for q, a in templates:
              instructions.append({"instruction": q, "input": "", "output": a})
              
      return instructions

  def generate_japanese_market_relations_instructions():
      """Génère 4 variations pour chacune des 40 relations du marché japonais (160 instructions)."""
      instructions = []
      for relation in JAPANESE_MARKET_RELATIONS:
          q = relation["question"]
          a = relation["answer"]
          
          # Variations
          instructions.append({"instruction": q, "input": "", "output": a})
          instructions.append({"instruction": f"Donne l'explication et le contexte de cette question sur le marché de la japanimation au Japon : {q}", "input": "", "output": f"Explication du marché japonais : {a}"})
          q_clean = q[0].lower() + q[1:]
          instructions.append({"instruction": f"En tant que spécialiste de l'histoire du manga et de l'animation au Japon, saurais-tu me dire {q_clean}", "input": "", "output": a})
          instructions.append({"instruction": f"Analyse le contexte d'édition, de diffusion ou de production du sujet suivant : {q}", "input": "", "output": f"Analyse et contexte japonais : {a}"})
      return instructions
  ```

- [ ] **Step 3: Integrate generators in SFT compiler**
  Insert generators call and list extension inside `compile_dataset()` on line 2375:
  ```python
      # 1d2. PAYSAGE JAPONAIS - RELATIONS (160 instructions en français)
      logger.info("[INFO] Generating high-quality Japanese market relational instructions...")
      japanese_relations = generate_japanese_market_relations_instructions()
      specialized_data.extend(japanese_relations)

      # 1e2. PAYSAGE JAPONAIS - PROFILS (600 instructions en français)
      logger.info("[INFO] Generating high-quality Japanese voice actors, publishers, and distributors profile instructions...")
      japanese_profiles = generate_japanese_market_profile_instructions()
      specialized_data.extend(japanese_profiles)
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add backend/pipeline/mlops/finetuning_dataset.py
  git commit -m "feat(mlops): integrate Japanese market database with SFT compiler"
  ```

---

### Task 4: Integrate Database with DPO Dataset Compiler

**Files:**
- Modify: [dpo_dataset_compiler.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/dpo_dataset_compiler.py)

- [ ] **Step 1: Import Japanese publishers and distributors**
  Modify imports on lines 150-157 in `dpo_dataset_compiler.py` to import Japanese databases:
  ```python
  try:
      from french_market_db import FRENCH_VOICE_ACTORS, FRENCH_MANGA_PUBLISHERS, FRENCH_ANIME_DISTRIBUTORS
  except ImportError:
      try:
          from backend.pipeline.mlops.french_market_db import FRENCH_VOICE_ACTORS, FRENCH_MANGA_PUBLISHERS, FRENCH_ANIME_DISTRIBUTORS
      except ImportError:
          FRENCH_VOICE_ACTORS = {}
          FRENCH_MANGA_PUBLISHERS = {}
          FRENCH_ANIME_DISTRIBUTORS = {}

  try:
      from japanese_market_db import JAPANESE_MANGA_PUBLISHERS, JAPANESE_ANIME_DISTRIBUTORS
  except ImportError:
      try:
          from backend.pipeline.mlops.japanese_market_db import JAPANESE_MANGA_PUBLISHERS, JAPANESE_ANIME_DISTRIBUTORS
      except ImportError:
          JAPANESE_MANGA_PUBLISHERS = {}
          JAPANESE_ANIME_DISTRIBUTORS = {}
  ```

- [ ] **Step 2: Append Japanese entities to replacement lists**
  Add Japanese publishers and distributors on lines 168-174 in `dpo_dataset_compiler.py`:
  ```python
  PUBLISHERS_LIST = list(FRENCH_MANGA_PUBLISHERS.keys()) + list(JAPANESE_MANGA_PUBLISHERS.keys()) if (FRENCH_MANGA_PUBLISHERS or JAPANESE_MANGA_PUBLISHERS) else [
      "Glénat Manga", "Kana", "Pika Édition", "Kurokawa", "Ki-oon", "Delcourt/Tonkam", "Soleil Manga", "Akata", "Meian"
  ]

  DISTRIBUTORS_LIST = list(FRENCH_ANIME_DISTRIBUTORS.keys()) + list(JAPANESE_ANIME_DISTRIBUTORS.keys()) if (FRENCH_ANIME_DISTRIBUTORS or JAPANESE_ANIME_DISTRIBUTORS) else [
      "Crunchyroll France", "ADN", "Netflix France", "Prime Video Channels", "Disney+ France", "Wakanim"
  ]
  ```

- [ ] **Step 3: Setup related groups for Japanese publishers and distributors**
  Add groups in `RELATED_ENTITIES_MAP` setup around line 340 of `dpo_dataset_compiler.py`:
  ```python
  # Setup Japanese publishers groups
  JAPANESE_PUBLISHERS_LIST = list(JAPANESE_MANGA_PUBLISHERS.keys())
  for jp_pub in JAPANESE_PUBLISHERS_LIST:
      RELATED_ENTITIES_MAP[jp_pub] = [p for p in JAPANESE_PUBLISHERS_LIST if p != jp_pub]

  # Setup Japanese distributors groups
  JAPANESE_DISTRIBUTORS_LIST = list(JAPANESE_ANIME_DISTRIBUTORS.keys())
  for jp_dist in JAPANESE_DISTRIBUTORS_LIST:
      RELATED_ENTITIES_MAP[jp_dist] = [d for d in JAPANESE_DISTRIBUTORS_LIST if d != jp_dist]
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add backend/pipeline/mlops/dpo_dataset_compiler.py
  git commit -m "feat(mlops): integrate Japanese market database with DPO dataset compiler"
  ```

---

### Task 5: Implement Unit Tests and Verify Data Generation

**Files:**
- Modify/Create: [test_japanese_market.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/mlops/test_japanese_market.py)

- [ ] **Step 1: Write `test_japanese_market.py`**
  Add unit tests verifying imports, generators output length, and correct formatting:
  ```python
  import pytest
  import os
  import sys

  def test_japanese_market_imports():
      from backend.pipeline.mlops.japanese_market_db import (
          JAPANESE_VOICE_ACTORS,
          JAPANESE_MANGA_PUBLISHERS,
          JAPANESE_ANIME_DISTRIBUTORS,
          JAPANESE_MARKET_RELATIONS
      )
      assert len(JAPANESE_VOICE_ACTORS) == 15
      assert len(JAPANESE_MANGA_PUBLISHERS) == 15
      assert len(JAPANESE_ANIME_DISTRIBUTORS) == 10
      assert len(JAPANESE_MARKET_RELATIONS) == 40

  def test_sft_japanese_generators():
      from backend.pipeline.mlops.finetuning_dataset import (
          generate_japanese_market_profile_instructions,
          generate_japanese_market_relations_instructions
      )
      
      profiles = generate_japanese_market_profile_instructions()
      relations = generate_japanese_market_relations_instructions()
      
      assert len(profiles) == (15 * 15 + 15 * 15 + 10 * 15)  # 600
      assert len(relations) == 160  # 40 * 4
      
      # Sample validation
      assert "Shūeisha" in profiles[225]["instruction"] or "Shūeisha" in profiles[225]["output"]
      assert "Aniplex" in relations[4]["instruction"] or "Aniplex" in relations[4]["output"]
  ```

- [ ] **Step 2: Run pytest to verify passes**
  Run: `.venv\Scripts\pytest tests/mlops/test_japanese_market.py -v`
  Expected: PASS

- [ ] **Step 3: Run full SFT local dry-run**
  Verify the generation pipeline works:
  ```powershell
  python backend/pipeline/mlops/finetuning_dataset.py --help
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add tests/mlops/test_japanese_market.py
  git commit -m "test(mlops): add unit tests for Japanese market database generators"
  ```
