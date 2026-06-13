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
        "origin": "Sunrise a été fondé en 1972 par d'anciens membres d'Mushi Production pour concevoir des animés de science-fiction.",
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
        "answer": "C'est la chaîne commerciale 'MBS TV' qui a ainsi initié les diffusions d'animes programmées tard dans la nuit pour un public de jeunes adultes."
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
        "question": "Quelle maison d'édition japonaise publie l'animé d'alchimie Fullmetal Alchemist d'Hiromu Arakawa ?",
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
        "answer": "Le manga 'Tokyo Ghoul' a été prépublié et éditée au Japon par 'Shūeisha' dans le magazine Weekly Young Jump."
    },
    {
        "question": "Quelle maison d'édition publie la comédie de détective Nicky Larson (City Hunter) au Japon ?",
        "answer": "La série mythique 'City Hunter' de Tsukasa Hojo a été publiée à l'origine au Japon par 'Shūeisha' dans le Weekly Shōnen Jump."
    }
]
