# -*- coding: utf-8 -*-
"""
Base de données exhaustive de 30 concepts métas (15 artistes Anisong et 15 Seiyuu)
et de 40 relations d'openings/endings et de doublage rédigées manuellement en français.
"""

ANIME_SONGS_AND_SINGERS = {
    "LiSA": {
        "definition": "Chanteuse pop-rock japonaise surnommée la 'Reine des Anisongs', réputée pour ses performances vocales puissantes et énergiques.",
        "origin": "Débute sa carrière solo en 2011 chez Aniplex après avoir chanté pour le groupe fictif Girls Dead Monster dans l'animé *Angel Beats!*.",
        "examples": "*Gurenge* et *Homura* (*Demon Slayer*), *Crossing Field* (*Sword Art Online*), *Oath Sign* (*Fate/Zero*).",
        "impact": "A popularisé les openings de rock énergique moderne, décrochant des records historiques de ventes et de streams mondiaux."
    },
    "Aimer": {
        "definition": "Chanteuse japonaise dotée d'une voix suave, rauque et mélancolique unique, très prisée pour les ballades dramatiques et les génériques épiques.",
        "origin": "Adopte son nom de scène en référence au verbe français 'aimer' après avoir temporairement perdu sa voix à l'adolescence.",
        "examples": "*Zankyou Sanka* (*Demon Slayer*), *Brave Shine* (*Fate/stay night: UBW*), *Last Stardust*, *Spark-Again* (*Fire Force*).",
        "impact": "Crée une atmosphère mystérieuse et émotionnelle intense, indispensable aux moments forts et climax des grandes séries d'action."
    },
    "YOASOBI": {
        "definition": "Duo de J-Pop composé du producteur musical Ayase (faisant ses débuts sur Vocaloid) et de la chanteuse Ikura, célèbre pour ses chansons inspirées de nouvelles littéraires.",
        "origin": "Formé en 2019 par la société Sony Music pour adapter des récits écrits en morceaux de musique pop rythmés.",
        "examples": "*Idol* (*Oshi no Ko*), *Yūsha* (*Frieren*), *Kaibutsu* (*Beastars*), *Gunjō*.",
        "impact": "A propulsé l'anisong au sommet des classements Billboard mondiaux grâce au titre ultra-populaire *Idol*."
    },
    "Asian Kung-Fu Generation": {
        "definition": "Groupe de rock alternatif japonais légendaire (surnommé AKFG) ayant marqué toute la génération des animés des années 2000.",
        "origin": "Formé en 1996 à Yokohama, caractérisé par des riffs de guitare intenses et des textes mélancoliques engagés.",
        "examples": "*Haruka Kanata* (*Naruto*), *Rewrite* (*Fullmetal Alchemist*), *After Dark* (*Bleach*), *Re:Re:* (*Erased*).",
        "impact": "Icône incontournable du rock d'animé, apportant une crédibilité et une énergie de rock indépendant aux shonens cultes."
    },
    "RADWIMPS": {
        "definition": "Groupe de rock alternatif japonais acclamé pour ses compositions orchestrales et mélodiques majestueuses.",
        "origin": "Formé en 2001, devenu mondialement célèbre pour sa collaboration fusionnelle exclusive avec le réalisateur Makoto Shinkai.",
        "examples": "*Zenzenzense* et *Sparkle* (*Your Name.*), *Grand Escape* (*Les Enfants du Temps*), *Suzume* (*Suzume*).",
        "impact": "A redéfini le rôle de la bande-son dans le cinéma d'animation japonais en composant des morceaux porteurs de l'émotion visuelle."
    },
    "Kenshi Yonezu": {
        "definition": "Auteur-compositeur-interprète de J-Pop de génie (ancien producteur de Vocaloid sous le pseudonyme Hachi), figure artistique majeure de sa génération.",
        "origin": "Commence à publier ses créations originales autoproduites sur Nico Nico Douga avant d'exploser dans les charts sous son vrai nom.",
        "examples": "*KICK BACK* (*Chainsaw Man*), *Peace Sign* (*My Hero Academia*), *Uchiage Hanabi* (*Fireworks*), *Chikyūgi* (*Le Garçon et le Héron*).",
        "impact": "Insuffle une créativité excentrique et une complexité rythmique de premier ordre aux openings de shonens majeurs."
    },
    "TK from Ling Tosite Sigure": {
        "definition": "Chanteur et guitariste du groupe de rock progressif Ling Tosite Sigure, célèbre pour sa voix suraiguë, ses cris intenses et son jeu de guitare complexe.",
        "origin": "Projet solo initié par Toru Kitajima en marge de son groupe de rock agressif et expérimental.",
        "examples": "*unravel* (*Tokyo Ghoul*), *Katharsis* (*Tokyo Ghoul:re*), *Signal* (*91 Days*).",
        "impact": "Interprète de l'opening *unravel*, devenu l'un des hymnes les plus célèbres, parodiés et vibrants de la culture otaku mondiale."
    },
    "FLOW": {
        "definition": "Groupe de rock alternatif japonais réputé pour ses génériques d'action survoltables et ses refrains fédérateurs de combats d'animes.",
        "origin": "Formé en 1998 par deux frères, mariant rock énergique, punk et touches de hip-hop mélodique.",
        "examples": "*GO!!!* et *Sign* (*Naruto*), *Colors* et *World End* (*Code Geass*), *Hero* (*Dragon Ball Z Battle of Gods*).",
        "impact": "Le groupe le plus représentatif de la ferveur shonen des années 2000, réchauffant l'ambiance de toutes les conventions occidentales."
    },
    "Linked Horizon": {
        "definition": "Projet musical symphonique dirigé par le compositeur Revo, réputé pour ses orchestrations militaires, épiques et grandioses.",
        "origin": "Extension du groupe originel Sound Horizon créée spécifiquement pour collaborer avec d'autres médias de fantasy.",
        "examples": "*Guren no Yumiya*, *Jiyuu no Tsubasa* et *Shinzou wo Sasageyo!* (*L'Attaque des Titans*).",
        "impact": "A composé les hymnes patriotiques cultes de *L'Attaque des Titans*, marquant l'identité sonore absolue de la série."
    },
    "Myth & Roid": {
        "definition": "Projet de musique contemporaine alternant rock industriel, électro sombre et arrangements symphoniques épiques.",
        "origin": "Fondé en 2015 par le producteur Tom-H@ck pour proposer une esthétique sonore sombre et avant-gardiste aux animés de fantasy.",
        "examples": "*VORACITY* (*Overlord*), *STYX HELIX* et *Paradisus-Paradoxum* (*Re:Zero*), *JINGO JUNGLE* (*Saga of Tanya the Evil*).",
        "impact": "Apporte une ambiance psychologique, torturée et fantastique intense aux œuvres de dark fantasy contemporaines."
    },
    "Supercell": {
        "definition": "Groupe de musique et d'illustration indépendant dirigé par le compositeur ryo, pionnier de l'utilisation de Vocaloid et de chanteurs invités.",
        "origin": "Formé en 2007 par ryo avec des artistes de la plateforme d'illustrations Pixiv pour diffuser leurs créations originales.",
        "examples": "*Kimi no Shiranai Monogatari* (*Bakemonogatari*), *My Dearest* (*Guilty Crown*), *The Bravery* (*Magi*).",
        "impact": "A révélé de superbes talents vocaux (comme Yanagi Nagi ou Chelly) et a structuré l'anisong pop-mélancolique moderne."
    },
    "Kana-Boon": {
        "definition": "Groupe de rock alternatif japonais réputé pour ses rythmiques de batterie ultra-rapides et ses voix claires et énergiques.",
        "origin": "Formé en 2008 à Osaka, ils connaissent un succès foudroyant grâce à leur collaboration avec la franchise Naruto.",
        "examples": "*Silhouette* (*Naruto Shippuden*), *Baton Road* (*Boruto*), *Fighter* (*Gundam Iron-Blooded Orphans*).",
        "impact": "Interprète de l'opening *Silhouette*, unanimement considéré comme l'un des openings de shonens les plus nostalgiques et parfaits."
    },
    "Eve": {
        "definition": "Chanteur et compositeur de J-Pop indépendant issu de la communauté 'Utaite' (repreneurs de chansons sur Nico Nico Douga).",
        "origin": "Débute comme repreneur de chansons de Vocaloid en 2009 avant de composer ses propres albums et d'écrire pour la télévision.",
        "examples": "*Kaikai Kitan* (*Jujutsu Kaisen*), *Bokurano* (*My Hero Academia*), *Ao no Sumika* (variante).",
        "impact": "Incorpore une esthétique visuelle mystique et une rythmique nerveuse idéale pour les animés d'exorcisme modernes."
    },
    "Official Hige Dandism": {
        "definition": "Groupe de pop-rock japonais (surnommé Higedan) caractérisé par un piano dynamique et la voix de tête claire de son chanteur.",
        "origin": "Formé en 2012, ils s'imposent comme l'un des groupes majeurs de la J-Pop contemporaine.",
        "examples": "*Cry Baby* (*Tokyo Revengers*), *Mixed Nuts* (*Spy x Family*), *White Noise* (*Tokyo Revengers*).",
        "impact": "Célèbre pour les variations de tons et de rythmes complexes de *Cry Baby*, collant à l'ambiance dramatique des sauts temporels."
    },
    "ClariS": {
        "definition": "Duo de J-Pop féminin réputé pour ses voix douces en harmonie parfaite et ses visages longtemps restés secrets et représentés en illustrations.",
        "origin": "Formé en 2009 par deux lycéennes (Clara et Alice) publiant des reprises sur Nico Nico Douga.",
        "examples": "*Connect* (*Puella Magi Madoka Magica*), *Irony* (*Oreimo*), *Click* (*Nisekoi*), *ALIVE* (*Lycoris Recoil*).",
        "impact": "Iconise les chansons douces et nostalgiques de shojos, d'animes de magie ou de tranches de vie lycéennes."
    }
}

SEIYUU_PROFILES = {
    "Hiroshi Kamiya": {
        "definition": "L'un des doubleurs les plus influents, primés et respectés du Japon, réputé pour son intonation pince-sans-rire et son charisme vocal.",
        "origin": "Né en 1975 à Matsudo, il rejoint la prestigieuse agence Aoni Production pour prêter sa voix aux héros les plus complexes.",
        "examples": "*Levi Ackerman* (*L'Attaque des Titans*), *Koyomi Araragi* (*Monogatari*), *Saiki Kusuo* (*Saiki Kusuo no Psi-nan*), *Izaya Orihara* (*Durarara!!*).",
        "impact": "Donne un sang-froid assassin ou un débit de parole humoristique d'une fluidité légendaire aux personnages cultes."
    },
    "Yuki Kaji": {
        "definition": "Doubleur vedette acclamé pour sa capacité exceptionnelle à retranscrire la rage, le désespoir, le cri viscéral et la détermination.",
        "origin": "Né en 1985, il s'est imposé comme la voix incontournable des protagonistes shonen tourmentés des années 2010.",
        "examples": "*Eren Jaeger* (*L'Attaque des Titans*), *Shoto Todoroki* (*My Hero Academia*), *Meliodas* (*Seven Deadly Sins*), *Issei Hyoudou* (*High School DxD*).",
        "impact": "A incarné la folie vengeresse et l'évolution dramatique traumatisante d'Eren Jaeger de manière magistrale."
    },
    "Rie Takahashi": {
        "definition": "Doubleuse et chanteuse de premier plan, célèbre pour son timbre espiègle, énergique et d'une grande douceur affective.",
        "origin": "Né en 1994, elle intègre l'agence 81 Produce après avoir remporté un concours de jeunes talents.",
        "examples": "*Megumin* (*Konosuba*), *Emilia* (*Re:Zero*), *Ai Hoshino* (*Oshi no Ko*), *Takagi* (*Karakai Jouzu no Takagi-san*).",
        "impact": "Voix de personnages cultes de type magiciennes extravagantes (le sortilège 'Explosion!' de Megumin) ou d'idols légendaires."
    },
    "Mamoru Miyano": {
        "definition": "Doubleur, chanteur et acteur de légende réputé pour ses intonations théâtrales extravagantes et ses rires machiavéliques mythiques.",
        "origin": "Né en 1983, il commence le théâtre dès l'enfance avant de devenir la voix incontournable des génies calculateurs.",
        "examples": "*Light Yagami* (*Death Note*), *Rintarou Okabe* (*Steins;Gate*), *Chrollo Lucilfer* (*Hunter x Hunter*), *Dazai Osamu* (*Bungou Stray Dogs*).",
        "impact": "A immortalisé les rires démentiels et les monologues machiavéliques parfaits de Light Yagami et du savant fou Okabe."
    },
    "Kana Hanazawa": {
        "definition": "L'une des doubleuses les plus prolifiques et adorées de l'histoire du Japon, célèbre pour sa voix aérienne d'une douceur angélique.",
        "origin": "Né en 1989 à Tokyo, elle débute à la télévision dès l'enfance avant de s'imposer comme la voix féminine la plus demandée du secteur.",
        "examples": "*Mayuri Shiina* (*Steins;Gate* - le fameux 'Tutturu~'), *Nadeko Sengoku* (*Monogatari*), *Mitsuri Kanroji* (*Demon Slayer*), *Kanade Tachibana* (*Angel Beats!*).",
        "impact": "Son interprétation de Nadeko Sengoku et la chanson *Renai Circulation* ont marqué durablement la pop-culture otaku."
    },
    "Natsuki Hanae": {
        "definition": "Doubleur contemporain de premier plan réputé pour sa voix claire, sensible, sincère et sa grande polyvalence dramatique.",
        "origin": "Né en 1991, il commence sa carrière en 2011 et explose mondialement en prêtant sa voix aux héros les plus protecteurs et tragiques.",
        "examples": "*Tanjiro Kamado* (*Demon Slayer*), *Ken Kaneki* (*Tokyo Ghoul*), *Kousei Arima* (*Your Lie in April*), *Falco Grice* (*L'Attaque des Titans*).",
        "impact": "A incarné la bonté d'âme de Tanjiro et la descente aux enfers psychologique tragique de Ken Kaneki avec brio."
    },
    "Yoshitsugu Matsuoka": {
        "definition": "Doubleur renommé pour ses rôles de héros de fantasy solitaires, de duellistes et sa capacité à monter dans des aigus intenses.",
        "origin": "Né en 1986 à Hokkaido, il rejoint l'agence I'm Enterprise pour prêter sa voix aux protagonistes masculins d'action.",
        "examples": "*Kirito* (*Sword Art Online*), *Inosuke Hashibira* (*Demon Slayer*), *Soma Yukihira* (*Food Wars!*), *Petelgeuse Romanee-Conti* (*Re:Zero*).",
        "impact": "Voix iconique de Kirito (SAO) et du sauvage Inosuke, démontrant un grand écart vocal impressionnant (héros calme vs démon hurlant)."
    },
    "Saori Hayami": {
        "definition": "Doubleuse d'exception saluée pour sa voix de velours d'une élégance et d'une douceur apaisantes, capable d'une intensité folle.",
        "origin": "Né en 1991 à Tokyo, elle intègre l'industrie très jeune et se distingue par la noblesse et le sang-froid de ses personnages.",
        "examples": "*Shinobu Kocho* (*Demon Slayer*), *Yor Forger* (*Spy x Family*), *Shoko Nishimiya* (*A Silent Voice*), *Yukino Yukinoshita* (*Oregairu*).",
        "impact": "Incarne avec brio des personnages féminins forts, doux en apparence mais dotés d'un mystère ou d'une puissance martiale cachée."
    },
    "Jun Fukuyama": {
        "definition": "Doubleur charismatique renommé pour ses intonations impériales, théâtrales et d'un grand charisme de commandant.",
        "origin": "Né en 1978 à Hiroshima, il s'est imposé comme une voix majeure de domaine grâce à son ton majestueux.",
        "examples": "*Lelouch vi Britannia* (*Code Geass*), *Koro-sensei* (*Assassination Classroom*), *King* (*Seven Deadly Sins*), *Kraft Lawrence* (*Spice and Wolf*).",
        "impact": "A immortalisé l'autorité suprême et les ordres théâtraux absolus de Lelouch vi Britannia dans la révolte de la Zone 11."
    },
    "Megumi Ogata": {
        "definition": "Doubleuse et chanteuse légendaire, célèbre pour son talent incomparable à prêter sa voix à des personnages masculins androgynes profonds.",
        "origin": "Né en 1965 à Tokyo, elle a brisé les barrières de genre dans le doublage dans les années 90.",
        "examples": "*Shinji Ikari* (*Neon Genesis Evangelion*), *Kurama* (*YuYu Hakusho*), *Yugi Muto* (*Yu-Gi-Oh!*), *Yuta Okkotsu* (*Jujutsu Kaisen 0*).",
        "impact": "Doubleuse historique de Shinji Ikari, transcendant les doutes psychologiques et la détresse émotionnelle adolescente."
    },
    "Rie Kugimiya": {
        "definition": "Doubleuse emblématique sacrée par les fans comme la 'Reine des Tsundere', réputée pour ses voix aiguës, colériques et adorables.",
        "origin": "Né en 1979 à Kumamoto, son timbre vocal unique a défini tout l'âge d'or des comédies romantiques des années 2000.",
        "examples": "*Taiga Aisaka* (*Toradora!*), *Alphonse Elric* (*Fullmetal Alchemist*), *Shana* (*Shakugan no Shana*), *Happy* (*Fairy Tail*).",
        "impact": "A popularisé les archétypes tsundere à l'international, marquant les répliques colériques phares des héroïnes de poche."
    },
    "Kenjiro Tsuda": {
        "definition": "Doubleur et réalisateur à la voix de basse rauque, ténébreuse, caressante et d'un magnétisme absolu inimitable.",
        "origin": "Né en 1971 à Osaka, sa voix unique et reconnaissable dès les premières syllabes l'a imposé comme un doubleur culte.",
        "examples": "*Kento Nanami* (*Jujutsu Kaisen*), *Overhaul* (*My Hero Academia*), *Seto Kaiba* (*Yu-Gi-Oh!*), *Tatsu* (*La Voie du tablier*).",
        "impact": "Donne un calme stoïque et une mélancolie adulte marquante à ses personnages (comme le culte Kento Nanami)."
    },
    "Yuichi Nakamura": {
        "definition": "Doubleur charismatique renommé pour ses rôles de mentors puissants, décontractés et d'une assurance insolente indéboulonnable.",
        "origin": "Né en 1980 à Kagawa, sa voix grave et posée s'est imposée pour doubler les figures d'autorité protectrices.",
        "examples": "*Satoru Gojo* (*Jujutsu Kaisen*), *Gray Fullbuster* (*Fairy Tail*), *Bruno Bucciarati* (*JoJo's Bizarre Adventure*), *Oreki Houtarou* (*Hyouka*).",
        "impact": "Prête sa voix de mentor surpuissant à Satoru Gojo, renforçant son attitude insolente et détendue face aux fléaux."
    },
    "Takahiro Sakurai": {
        "definition": "Doubleur renommé pour ses voix calmes, posées, élégantes et parfois ambiguës ou manipulatrices.",
        "origin": "Né en 1974 à Aichi, il intègre l'industrie et prête sa voix à des personnages de premier plan d'une grande complexité morale.",
        "examples": "*Suguru Geto* (*Jujutsu Kaisen*), *Reigen Arataka* (*Mob Psycho 100*), *Giyu Tomioka* (*Demon Slayer*), *Griffith* (*Berserk* - trilogie/récent).",
        "impact": "Donne une douceur mélancolique ou un charisme inquiétant aux personnages à double facette (Geto, Griffith)."
    },
    "Maaya Sakamoto": {
        "definition": "Doubleuse, chanteuse et actrice de comédie musicale de premier ordre, célèbre pour son élégance vocale et ses rôles d'une grande noblesse.",
        "origin": "Né en 1980, elle débute très jeune dans l'animation sous la tutelle de la compositrice Yoko Kanno.",
        "examples": "*Shinobu Oshino* (*Monogatari*), *Shiki Ryougi* (*The Garden of Sinners*), *Ciel Phantomhive* (*Black Butler*), *Motoko Kusanagi* (*Ghost in the Shell Arise*).",
        "impact": "Interprète de la noble et mystérieuse Shiki Ryougi, insufflant une poésie et une force morale froides à ses personnages."
    }
}

# --- 40 RELATIONS TRANSMÉDIAS LIÉES AUX CHANSONS D'ANIMES ET AUX SEIYUU ---
SONGS_AND_SEIYUU_RELATIONS = [
    {
        "question": "Qui double le personnage charismatique de Levi Ackerman dans l'anime L'Attaque des Titans ?",
        "answer": "Le personnage légendaire de Levi Ackerman est doublé par le célèbre seiyuu 'Hiroshi Kamiya', réputé pour prêter sa voix froide, tranchante et autoritaire au soldat le plus fort de l'humanité."
    },
    {
        "question": "Quelle chanteuse de pop-rock japonaise interprète l'opening Gurenge de l'anime Demon Slayer ?",
        "answer": "Il s'agit de la chanteuse 'LiSA'. Son titre 'Gurenge' est devenu un succès planétaire historique, marquant l'identité musicale forte du début de la quête de Tanjiro."
    },
    {
        "question": "Quel seiyuu prête sa voix au protagoniste tourmenté Eren Jaeger dans L'Attaque des Titans ?",
        "answer": "Le personnage d'Eren Jaeger est doublé de manière magistrale par 'Yuki Kaji', acclamé par les fans pour ses cris viscéraux de rage et de désespoir absolus."
    },
    {
        "question": "Quel duo musical japonais interprète l'opening mondialement célèbre Idol pour l'anime Oshi no Ko ?",
        "answer": "L'opening 'Idol' est interprété par le duo phénomène de J-Pop 'YOASOBI' (composé d'Ayase et d'Ikura). Le titre a brisé tous les records de streams mondiaux en 2023."
    },
    {
        "question": "Quel seiyuu double le mentor surpuissant et décontracté Satoru Gojo dans Jujutsu Kaisen ?",
        "answer": "Satoru Gojo est doublé par le talentueux et charismatique seiyuu 'Yuichi Nakamura', dont la voix grave et assurée colle parfaitement à l'insolence décontractée du plus fort des exorcistes."
    },
    {
        "question": "Quel groupe de rock alternatif japonais est célèbre pour l'opening légendaire Silhouette dans Naruto Shippuden ?",
        "answer": "Il s'agit du groupe 'Kana-Boon'. Leur titre 'Silhouette' est considéré comme l'un des génériques de shonens les plus parfaits et nostalgiques de l'histoire de la japanimation."
    },
    {
        "question": "Quelle doubleuse japonaise prête sa voix au personnage de Megumin, la magicienne explosive de Konosuba ?",
        "answer": "Megumin est doublée par la talentueuse 'Rie Takahashi', célèbre pour ses incantations pleines d'énergie et de folie comique avant de déclencher sa magie d'explosion."
    },
    {
        "question": "Quel artiste de J-Pop, ancien producteur de Vocaloid, interprète l'opening KICK BACK de Chainsaw Man ?",
        "answer": "L'opening rythmé et chaotique 'KICK BACK' est composé et interprété par le génial 'Kenshi Yonezu', qui insuffle une folie et une énergie brute idéales pour l'univers de Denji."
    },
    {
        "question": "Quel seiyuu légendaire prête sa voix à Light Yagami dans l'anime policier culte Death Note ?",
        "answer": "Light Yagami est doublé de manière immortelle par 'Mamoru Miyano', acclamé mondialement pour ses rires diaboliques glaçants et ses monologues de complexe divin sous l'identité de Kira."
    },
    {
        "question": "Quelle chanteuse dotée d'une voix rauque et douce interprète l'opening Brave Shine de Fate/stay night: Unlimited Blade Works ?",
        "answer": "L'opening 'Brave Shine' est interprété de manière vibrante par la chanteuse 'Aimer', apportant sa mélancolie et son intensité vocale aux duels héroïques de Shirou et d'Archer."
    },
    {
        "question": "Quel seiyuu double le stoïque et adorable Kento Nanami, l'exorciste de classe classe dans Jujutsu Kaisen ?",
        "answer": "Kento Nanami est doublé par le légendaire 'Kenjiro Tsuda', dont la voix de basse rauque et magnétique exprime parfaitement la maturité lasse et le professionnalisme héroïque du personnage."
    },
    {
        "question": "Quel groupe de rock japonais interprète l'opening mythique unravel pour l'anime Tokyo Ghoul ?",
        "answer": "L'opening 'unravel' est interprété par 'TK from Ling Tosite Sigure'. Sa voix suraiguë et ses envolées progressives tortueuses collent parfaitement à la détresse psychologique de Ken Kaneki."
    },
    {
        "question": "Quelle doubleuse et chanteuse emblématique prête sa voix à Mayuri Shiina dans Steins;Gate et Nadeko Sengoku dans Monogatari ?",
        "answer": "Il s'agit de la célèbre 'Kana Hanazawa'. Sa voix d'une douceur aérienne incomparable a donné vie au fameux salut 'Tutturu~' de Mayuri et à la chanson culte 'Renai Circulation'."
    },
    {
        "question": "Quel projet musical de Revo compose et interprète l'opening historique Guren no Yumiya de L'Attaque des Titans ?",
        "answer": "L'opening épique et orchestral 'Guren no Yumiya' est composé et interprété par 'Linked Horizon', dont les chœurs allemands et les trompettes de guerre ont marqué le début de la série."
    },
    {
        "question": "Quel seiyuu prête sa voix au protagoniste Tanjiro Kamado dans l'anime Demon Slayer ?",
        "answer": "Le courageux et bienveillant Tanjiro Kamado est doublé par 'Natsuki Hanae', acclamé pour sa voix claire, droite et sa capacité à exprimer la dévotion fraternelle absolue."
    },
    {
        "question": "Quel groupe de rock alternatif est célèbre pour l'opening Rewrite de l'adaptation de 2003 de Fullmetal Alchemist ?",
        "answer": "L'opening énergique 'Rewrite' est interprété par le groupe de rock alternatif de référence 'Asian Kung-Fu Generation'."
    },
    {
        "question": "Quelle doubleuse est surnommée la 'Reine des Tsundere' pour ses rôles de Taiga Aisaka (Toradora!) et d'Alphonse Elric (Fullmetal Alchemist) ?",
        "answer": "Il s'agit de 'Rie Kugimiya'. Son timbre vocal aigu et ses réactions de colère mignonnes ont défini l'archétype tsundere de toute une décennie d'animation."
    },
    {
        "question": "Quel groupe de rock est célèbre pour l'opening rythmé GO!!! de l'anime Naruto ?",
        "answer": "L'opening énergique et festif 'GO!!!' (Fighting Dreamers) est interprété par le groupe 'FLOW', devenu le groupe symbole des openings de combats épiques des années 2000."
    },
    {
        "question": "Quelle doubleuse de premier ordre double le personnage masculin androgyne Shinji Ikari dans Neon Genesis Evangelion ?",
        "answer": "Le complexe et fragile Shinji Ikari est doublé de manière historique par la doubleuse légendaire 'Megumi Ogata', traduisant à la perfection les conflits psychologiques et l'angoisse du pilote de l'EVA-01."
    },
    {
        "question": "Quel groupe de rock alternatif japonais compose l'intégralité de la bande-son poétique du film d'animation Your Name de Makoto Shinkai ?",
        "answer": "La bande-son magistrale de 'Your Name.' (incluant les titres 'Zenzenzense' et 'Sparkle') est entièrement composée et interprétée par le groupe 'RADWIMPS'."
    },
    {
        "question": "Quel seiyuu double le commanditaire théâtral Lelouch vi Britannia dans l'anime de méchas Code Geass ?",
        "answer": "Lelouch vi Britannia est doublé de manière impériale par 'Jun Fukuyama', dont le ton théâtral majestueux et l'autorité naturelle ont donné tout son relief au leader des Chevaliers Noirs."
    },
    {
        "question": "Quel projet musical de Tom-H@ck interprète le générique de fin STYX HELIX pour l'anime Re:Zero ?",
        "answer": "Le générique de fin mélancolique et envoûtant 'STYX HELIX' est interprété par le groupe 'Myth & Roid'."
    },
    {
        "question": "Quelle doubleuse d'exception prête sa voix douce et élégante à Yor Forger dans Spy x Family et Shinobu Kocho dans Demon Slayer ?",
        "answer": "Il s'agit de l'acclamée 'Saori Hayami', réputée pour sa voix d'une infinie douceur dissimulant une force martiale redoutable ou une facette d'assassin."
    },
    {
        "question": "Quel chanteur et compositeur de J-Pop interprète le générique Kaikai Kitan de la première saison de Jujutsu Kaisen ?",
        "answer": "L'opening rythmé 'Kaikai Kitan' est composé et interprété par l'artiste 'Eve', dont l'esthétique sonore mystique colle parfaitement à l'univers d'exorcisme de la série."
    },
    {
        "question": "Quel seiyuu double l'excentrique mais génial Reigen Arataka dans l'anime Mob Psycho 100 ?",
        "answer": "Le mentor charlatan mais profondément humain Reigen Arataka est doublé par 'Takahiro Sakurai', dont le ton calme et manipulateur amuse et touche les spectateurs."
    },
    {
        "question": "Quel groupe de J-Pop interprète le générique Cry Baby pour l'anime temporel Tokyo Revengers ?",
        "answer": "L'opening rythmé au piano 'Cry Baby' est interprété par le groupe 'Official Hige Dandism', collant à l'atmosphère dramatique et urbaine de la série."
    },
    {
        "question": "Quel seiyuu double le héros de jeu vidéo Kirito (Kazuto Kirigaya) dans Sword Art Online ?",
        "answer": "L'épéiste noir Kirito est doublé par 'Yoshitsugu Matsuoka', devenu la voix emblématique des héros de fantasy et des combattants solitaires."
    },
    {
        "question": "Quel duo féminin interprète le légendaire opening Connect pour l'anime de dark magical girl Puella Magi Madoka Magica ?",
        "answer": "L'opening doux et faussement joyeux 'Connect' est interprété par le duo 'ClariS', contrastant de manière saisissante avec la noirceur dramatique de la série."
    },
    {
        "question": "Quelle doubleuse légendaire double la mystérieuse Shiki Ryougi dans la série de films The Garden of Sinners ?",
        "answer": "Shiki Ryougi est doublée de manière noble et froide par 'Maaya Sakamoto', insufflant sa force de caractère et son élégance vocale au personnage."
    },
    {
        "question": "Quel groupe de rock alternatif interprète l'opening nostalgique Re:Re: pour l'adaptation animée du manga Erased ?",
        "answer": "L'opening 'Re:Re:' est interprété par le groupe 'Asian Kung-Fu Generation', apportant son rock mélancolique au thriller temporel."
    },
    {
        "question": "Qui double le démon sauvage Inosuke Hashibira dans l'anime Demon Slayer ?",
        "answer": "Le personnage d'Inosuke Hashibira est doublé de manière survoltée par 'Yoshitsugu Matsuoka', qui s'époumone sous le masque de sanglier pour rendre le personnage drôle et sauvage."
    },
    {
        "question": "Quel seiyuu prête sa voix au rival orgueilleux Seto Kaiba dans la série d'origine Yu-Gi-Oh! ?",
        "answer": "Le président Seto Kaiba est doublé par 'Kenjiro Tsuda', dont la voix grave et insolente a immortalisé les répliques méprisantes du duelliste légendaire."
    },
    {
        "question": "Quelle doubleuse et chanteuse vedette double la légendaire idol de pop Ai Hoshino dans l'anime Oshi no Ko ?",
        "answer": "Le personnage brillant d'Ai Hoshino est doublé par 'Rie Takahashi', qui interprète également les chansons en direct de l'héroïne."
    },
    {
        "question": "Quel hymne militaire orchestral de Linked Horizon sert d'opening à la saison 2 de L'Attaque des Titans ?",
        "answer": "L'opening martial et légendaire est 'Shinzou wo Sasageyo!' ('Offrez vos cœurs !'), hymne de ralliement culte pour tous les fans de la franchise."
    },
    {
        "question": "Quelle doubleuse prête sa voix au mystérieux vampire de 500 ans Shinobu Oshino dans la franchise Monogatari du studio Shaft ?",
        "answer": "Shinobu Oshino est doublée par la talentueuse 'Maaya Sakamoto', exprimant la fierté royale et la mélancolie séculaire de la vampire déchue."
    },
    {
        "question": "Quel groupe pop-rock interprète l'opening rythmé Crossing Field pour la première saison de Sword Art Online ?",
        "answer": "L'opening ultra-populaire 'Crossing Field' est chanté de manière dynamique par 'LiSA', devenant l'un des hymnes du renouveau du genre isekai."
    },
    {
        "question": "Quel seiyuu double le démon Suguru Geto dans la saison 2 de Jujutsu Kaisen et le film Jujutsu Kaisen 0 ?",
        "answer": "Le personnage tragique de Suguru Geto est doublé par 'Takahiro Sakurai', dont la voix douce et posée exprime parfaitement le glissement du personnage vers l'extrémisme."
    },
    {
        "question": "Quel groupe de J-Pop interprète le générique de fin Mixed Nuts pour l'anime de comédie Spy x Family ?",
        "answer": "L'opening rythmé et joyeux 'Mixed Nuts' est interprété par le groupe acclamé 'Official Hige Dandism'."
    },
    {
        "question": "Qui double le personnage de Rintarou Okabe (savant fou Okarin) dans le chef-d'œuvre de science-fiction Steins;Gate ?",
        "answer": "Rintarou Okabe est doublé de manière inoubliable par 'Mamoru Miyano', qui alterne gags de paranoïa loufoque sous l'identité de Kyouma Hououin et détresse psychologique absolue face aux boucles temporelles."
    },
    {
        "question": "Quel groupe de rock symphonique et lyrique de ryo interprète Kimi no Shiranai Monogatari, ending culte de Bakemonogatari ?",
        "answer": "L'ending mélancolique et poétique 'Kimi no Shiranai Monogatari' est interprété par le groupe 'Supercell', avec la voix invitée de Yanagi Nagi."
    }
]
