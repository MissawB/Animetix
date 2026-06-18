# -*- coding: utf-8 -*-
"""
Base de données exhaustive de 30 concepts métas (15 magazines de prépublication et 15 awards)
et de 40 relations industrielles et de récompenses rédigées manuellement en français.
"""

SERIALIZATION_MAGAZINES = {
    "Weekly Shōnen Jump": {
        "definition": "Le magazine hebdomadaire de prépublication de mangas Shonen le plus célèbre et le plus vendu de l'histoire du Japon, édité par la Shūeisha depuis 1968.",
        "origin": "Lancé le 2 juillet 1968 par Shūeisha pour concurrencer le Weekly Shōnen Magazine de Kōdansha.",
        "examples": "*One Piece*, *Dragon Ball*, *Naruto*, *Bleach*, *Hunter x Hunter*, *Demon Slayer*, *Jujutsu Kaisen*.",
        "impact": "A défini les codes universels du genre 'Nekketsu' à travers sa devise éditoriale historique : Amitié, Effort, Victoire.",
    },
    "Weekly Shōnen Magazine": {
        "definition": "Magazine hebdomadaire de prépublication de mangas Shonen publié par la Kōdansha depuis 1959, principal rival historique du Weekly Shōnen Jump.",
        "origin": "Lancé le 17 mars 1959 par Kōdansha au même moment que le Weekly Shōnen Sunday.",
        "examples": "*Fairy Tail*, *Hajime no Ippo*, *Seven Deadly Sins*, *Tokyo Revengers*, *GTO (Great Teacher Onizuka)*.",
        "impact": "Propose historiquement des récits Shonen légèrement plus matures, réalistes ou axés sur le sport et le drame social.",
    },
    "Weekly Shōnen Sunday": {
        "definition": "Magazine hebdomadaire de prépublication de mangas Shonen historique publié par la Shōgakukan depuis 1959.",
        "origin": "Lancé le 17 mars 1959 par Shōgakukan pour célébrer l'avènement de l'ère du manga de divertissement hebdomadaire.",
        "examples": "*Détective Conan*, *Inuyasha*, *Frieren*, *Magi: The Labyrinth of Magic*, *Ranma 1/2*.",
        "impact": "Reconnu pour ses récits mettant l'accent sur les comédies romantiques pures, la tranche de vie et les aventures poétiques.",
    },
    "Bessatsu Shōnen Magazine": {
        "definition": "Magazine mensuel de prépublication de mangas Shonen publié par la Kōdansha, célèbre pour ses intrigues sombres et fantastiques.",
        "origin": "Lancé en septembre 2009 en tant que spin-off mensuel du Weekly Shōnen Magazine.",
        "examples": "*L'Attaque des Titans* (*Shingeki no Kyojin*), *The Heroic Legend of Arslan*, *Sankarea*.",
        "impact": "Héberge des œuvres shonen hors-normes et psychologiques, souvent trop sombres ou complexes pour le rythme hebdomadaire.",
    },
    "Weekly Young Jump": {
        "definition": "Magazine hebdomadaire de prépublication de type Seinen (jeunes adultes) publié par la Shūeisha depuis 1979.",
        "origin": "Créé en 1979 par Shūeisha pour conserver son lectorat vieillissant issu du Weekly Shōnen Jump.",
        "examples": "*Kingdom*, *Tokyo Ghoul*, *Oshi no Ko*, *Kaguya-sama: Love is War*, *Golden Kamui*, *Elfen Lied*.",
        "impact": "Mêle habilement récits historiques d'envergure, thrillers psychologiques violents et comédies romantiques sophistiquées.",
    },
    "Young Animal": {
        "definition": "Magazine bimensuel de prépublication de mangas Seinen publié par l'éditeur Hakusensha depuis 1992.",
        "origin": "Lancé en 1992 en remplacement du magazine *Animal House* créé en 1989.",
        "examples": "*Berserk*, *March Comes in Like a Lion* (*3-gatsu no Lion*), *Detroit Metal City*.",
        "impact": "Célèbre pour avoir hébergé le monument de la dark fantasy *Berserk*, affirmant une liberté artistique et graphique totale.",
    },
    "Weekly Young Magazine": {
        "definition": "Magazine hebdomadaire de prépublication de mangas Seinen édité par Kōdansha depuis 1980.",
        "origin": "Lancé en 1980 par Kōdansha pour s'imposer sur le marché grandissant de la bande dessinée pour adultes.",
        "examples": "*Akira*, *Ghost in the Shell*, *Initial D*, *Prison School*, *Chobits*.",
        "impact": "Pionnier des récits cyberpunk, de science-fiction dystopique et de thrillers urbains réalistes.",
    },
    "Monthly Afternoon": {
        "definition": "Magazine mensuel de prépublication de mangas Seinen édité par Kōdansha, renommé pour sa liberté de ton et son prestige artistique.",
        "origin": "Lancé en 1986 par Kōdansha, il propose un rythme mensuel permettant des planches d'une richesse graphique extrême.",
        "examples": "*Vinland Saga*, *L'Ère des Cristaux* (*Houseki no Kuni*), *Parasyte*, *Blue Period*, *Mushishi*.",
        "impact": "Considéré comme l'élite littéraire et artistique du Seinen, récompensant des récits lents, philosophiques et novateurs.",
    },
    "Big Comic Spirits": {
        "definition": "Magazine hebdomadaire de prépublication de mangas Seinen publié par Shōgakukan depuis 1980.",
        "origin": "Créé en 1980 par Shōgakukan pour cibler les étudiants et jeunes professionnels masculins.",
        "examples": "*20th Century Boys*, *Maison Ikkoku*, *Bonne nuit Punpun* (*Oyasumi Punpun*), *I Am a Hero*.",
        "impact": "Reconnu pour ses drames sociaux contemporains poignants, ses satires politiques et ses thrillers psychologiques majeurs.",
    },
    "Ultra Jump": {
        "definition": "Magazine mensuel de prépublication de mangas Seinen publié par Shūeisha, caractérisé par sa créativité graphique et pop.",
        "origin": "Créé en 1999 par Shūeisha, devenant un magazine mensuel autonome réputé.",
        "examples": "*JoJo's Bizarre Adventure* (Partie 7: *Steel Ball Run*, Partie 8: *Jojolion*, Partie 9: *The JOJOLands*).",
        "impact": "Offre un écrin haut de gamme aux designs extravagants et aux structures narratives complexes d'auteurs phares.",
    },
    "Monthly Shōnen Gangan": {
        "definition": "Magazine mensuel de prépublication de mangas Shonen édité par Square Enix depuis 1991.",
        "origin": "Lancé par Enix (avant la fusion avec Square) en 1991 pour pénétrer le marché du manga.",
        "examples": "*Fullmetal Alchemist*, *Soul Eater*, *Blast of Tempest*, *Guilty Crown*.",
        "impact": "Se distingue par un style graphique hérité de l'esthétique des jeux de rôle (JRPG) et de la fantasy d'action stylisée.",
    },
    "Comic Ran": {
        "definition": "Magazine mensuel de mangas historiques publié par l'éditeur Leed, axé sur les récits de samouraïs et le genre Gekiga.",
        "origin": "Spécialisé dans les récits 'Jidaigeki' (drame d'époque) et le réalisme historique.",
        "examples": "Mangas de sabre traditionnels, adaptations de chroniques féodales.",
        "impact": "Préserve l'art graphique traditionnel et exigeant du Gekiga historique pour un lectorat de passionnés d'histoire féodale.",
    },
    "Sho-Comi": {
        "definition": "Magazine bimensuel de prépublication de mangas Shōjo publié par Shōgakukan depuis 1968, axé sur la romance lycéenne moderne.",
        "origin": "Lancé en 1968 sous le nom de *Shōjo Comic* avant de prendre son diminutif officiel.",
        "examples": "*Fushigi Yugi*, *Tsubaki-chou Lonely Planet* (variante), récits de romance scolaire contemporaine.",
        "impact": "Modélise les codes esthétiques et les fantasmes amoureux adolescents pour des générations de jeunes lectrices japonaises.",
    },
    "Monthly Comic Ryū": {
        "definition": "Magazine mensuel Seinen édité par Tokuma Shoten, réputé pour ses récits de fantasy originaux et de sous-cultures.",
        "origin": "Relancé en 2006 par Tokuma Shoten pour explorer des genres hybrides de science-fiction et de comédie fantastique.",
        "examples": "*Monster Musume*, *Alice & Zouroku*, *Legend of the Galactic Heroes* (récent).",
        "impact": "Héberge des récits de niche uniques explorant la fantasy hybride et les relations d'espèces fantastiques.",
    },
    "Ribon": {
        "definition": "Magazine mensuel de mangas Shōjo historique publié par Shūeisha depuis 1955, ciblant les jeunes filles du primaire et collège.",
        "origin": "Lancé le 3 août 1955 pour offrir des histoires douces, éducatives et romantiques aux jeunes filles.",
        "examples": "*Chibi Maruko-chan*, *Marmalade Boy*, *Gals!*, *Ultra Maniac*.",
        "impact": "L'un des trois piliers historiques du Shōjo manga, ayant initié les tropes de romances d'enfance les plus purs.",
    },
}

POP_CULTURE_AWARDS = {
    "Prix Shōgakukan": {
        "definition": "L'un des prix de manga les plus anciens, les plus respectés et les plus prestigieux du Japon, décerné par Shōgakukan depuis 1955.",
        "origin": "Créé en 1955 pour célébrer le centenaire de la fondation de Shōgakukan et encourager la qualité artistique des bandes dessinées.",
        "examples": "Lauréats célèbres : *Frieren*, *Komi cherche ses mots*, *Inuyasha*, *Monster*, *Slam Dunk*.",
        "impact": "Offre une reconnaissance institutionnelle suprême et propulse les ventes nationales des mangas primés.",
    },
    "Prix du manga Kōdansha": {
        "definition": "Prix annuel prestigieux parrainé par l'éditeur Kōdansha, récompensant les meilleures œuvres publiées l'année précédente.",
        "origin": "Fondé en 1977 pour célébrer le talent artistique des dessinateurs et scénaristes dans différentes catégories démographiques.",
        "examples": "Lauréats : *Blue Lock*, *Oshi no Ko*, *Tokyo Revengers*, *L'Attaque des Titans*, *Vinland Saga*.",
        "impact": "Récompense l'excellence narrative et le dynamisme éditorial à travers trois prix phares (Shonen, Shōjo, Général).",
    },
    "Prix culturel Osamu Tezuka": {
        "definition": "Prix culturel suprême du manga au Japon parrainé par le journal Asahi Shimbun en hommage au 'Dieu du Manga' Osamu Tezuka.",
        "origin": "Créé en 1997 à Tokyo par le quotidien de référence Asahi Shimbun pour distinguer des mangas d'une immense valeur littéraire.",
        "examples": "Lauréats : *Pluto*, *Monster*, *March Comes in Like a Lion*, *Golden Kamui*, *Land of the Lustrous*.",
        "impact": "Considéré comme le 'Goncourt du Manga', il salue l'innovation graphique, l'écriture complexe et l'apport philosophique.",
    },
    "Manga Taishō": {
        "definition": "Prix annuel japonais fondé en 2008 par des comités de libraires pour récompenser les œuvres récentes de moins de 8 volumes.",
        "origin": "Créé en 2008 pour promouvoir les mangas émergents et conseiller directement les lecteurs en magasin.",
        "examples": "Lauréats historiques : *Frieren*, *Golden Kamui*, *Blue Period*, *Chihayafuru*, *Beastars*.",
        "impact": "Le prix le plus influent pour lancer la popularité d'une série émergente et déclencher de futures adaptations animées.",
    },
    "Oscar du meilleur film d'animation": {
        "definition": "La plus haute distinction cinématographique mondiale attribuée par l'Académie des Oscars aux États-Unis, récompensant les longs-métrages d'animation.",
        "origin": "Catégorie créée en 2001 aux Oscars pour honorer spécifiquement l'art de l'animation à long-métrage.",
        "examples": "Seul animé japonais lauréat : *Le Voyage de Chihiro* de Hayao Miyazaki en 2003 (nommés célèbres : *Le Conte de la princesse Kaguya*, *Le Vent se lève*).",
        "impact": "Consacre le cinéma d'animation japonais comme un égal artistique majeur face aux géants hollywoodiens (Disney/Pixar).",
    },
    "Crunchyroll Anime Awards": {
        "definition": "Cérémonie annuelle mondiale de récompenses fondée par la plateforme de streaming Crunchyroll pour célébrer les meilleures séries animées.",
        "origin": "Lancé en 2017 avec un système de vote mixte mêlant un jury international d'experts et le vote du public mondial en ligne.",
        "examples": "Lauréats de l'Anime de l'Année : *Jujutsu Kaisen*, *Demon Slayer*, *Cyberpunk: Edgerunners*, *L'Attaque des Titans*.",
        "impact": "Le plus grand indicateur de la popularité internationale des productions de japanimation auprès du public occidental moderne.",
    },
    "Tokyo Anime Award Festival": {
        "definition": "TAAF - Festival et cérémonie annuelle prestigieuse de l'industrie récompensant l'excellence technique et artistique des animés à Tokyo.",
        "origin": "Issu de la section animation de la foire Tokyo International Anime Fair créée en 2002, devenu indépendant en 2014.",
        "examples": "Lauréats de l'Anime de l'Année : *Spy x Family*, *Oshi no Ko*, *Demon Slayer*, *Keep Your Hands Off Eizouken!*.",
        "impact": "Représente la reconnaissance suprême des professionnels et créateurs de l'industrie de l'animation japonaise à Tokyo.",
    },
    "Japan Media Arts Festival": {
        "definition": "Prix national prestigieux décerné par l'Agence pour les Affaires culturelles du gouvernement japonais pour honorer les chefs-d'œuvre artistiques.",
        "origin": "Établi en 1997 à Tokyo pour promouvoir et encourager l'innovation dans les domaines artistiques, médiatiques et technologiques.",
        "examples": "Lauréats du Grand Prix Manga : *Monster*, *Vagabond*, *L'Ère des Cristaux*, *Les Enfants de la mer*.",
        "impact": "Le label d'excellence étatique ultime au Japon, célébrant la valeur patrimoniale et culturelle d'une œuvre.",
    },
    "Prix Harvey": {
        "definition": "Prestigieux prix de bande dessinée américain récompensant l'excellence artistique, doté d'une catégorie dédiée au meilleur manga depuis 2018.",
        "origin": "Créé en 1988 aux États-Unis en hommage au légendaire dessinateur et scénariste Harvey Kurtzman.",
        "examples": "Lauréats du Meilleur Manga : *Chainsaw Man*, *L'Attaque des Titans*, *My Hero Academia*, *Witch Hat Atelier*.",
        "impact": "Marque la reconnaissance critique nord-américaine de la supériorité scénaristique et formelle des mangas japonais récents.",
    },
    "Prix Eisner": {
        "definition": "Les Eisner Awards sont considérés comme les 'Oscars' de la bande dessinée américaine, couronnant régulièrement les maîtres du manga.",
        "origin": "Créés en 1988 aux États-Unis en mémoire du dessinateur pionnier Will Eisner.",
        "examples": "Mangakas intronisés ou récompensés : Junji Ito, Naoki Urasawa, Shigeru Mizuki, Rumiko Takahashi.",
        "impact": "Consacre définitivement un auteur de manga dans le panthéon mondial du neuvième art et de l'illustration graphique.",
    },
    "Festival d'Angoulême": {
        "definition": "Le Festival international de la bande dessinée d'Angoulême est le plus grand événement de BD d'Europe, récompensant des mangas d'exception.",
        "origin": "Fondé en 1974 en France, récompensant des œuvres internationales de toutes origines géographiques.",
        "examples": "Lauréats et hommages majeurs : Jiro Taniguchi (*Quartier Lointain*), Katsuhiro Otomo, Ryoichi Ikegami, Shigeru Mizuki.",
        "impact": "Assure la consécration intellectuelle critique européenne du manga en tant qu'œuvre littéraire et picturale d'avant-garde.",
    },
    "Prix Seiun": {
        "definition": "Le plus ancien et le plus important prix de science-fiction au Japon, récompensant les meilleures œuvres spéculatives de l'année précédente.",
        "origin": "Créé en 1970 sur le modèle du Prix Hugo américain lors de la convention nationale de science-fiction du Japon.",
        "examples": "Lauréats : *Neon Genesis Evangelion*, *Nausicaä de la Vallée du Vent*, *Planetes*, *Astra Lost in Space*.",
        "impact": "La plus haute distinction pour les récits d'anticipation, de hard science-fiction et de conquête spatiale en manga et animé.",
    },
    "Japan Cartoonists Association Award": {
        "definition": "Prix national d'excellence parrainé par l'Association des caricaturistes du Japon pour récompenser les contributions culturelles exceptionnelles.",
        "origin": "Créé en 1972 pour honorer le talent des artistes et préserver le patrimoine de l'illustration graphique nationale.",
        "examples": "Grands Prix : *One Piece*, *Golgo 13*, *Asadora!* de Naoki Urasawa.",
        "impact": "Récompense la longévité artistique, la rigueur technique et le rôle sociétal majeur d'un créateur au Japon.",
    },
    "Shogakukan Light Novel Award": {
        "definition": "Concours de manuscrits et prix annuel de l'éditeur Shōgakukan pour découvrir de nouveaux talents d'écriture dans le Light Novel.",
        "origin": "Lancé en 2006 pour alimenter les collections de romans légers de l'éditeur (Gagaga Bunko).",
        "examples": "*Oregairu* (My Teen Romantic Comedy SNAFU), *Shimoneta*.",
        "impact": "Le canal le plus compétitif du Japon pour faire publier son premier roman léger et obtenir une future adaptation animée.",
    },
    "Tezuka Award & Akatsuka Award": {
        "definition": "Concours de mangas semestriels légendaires organisés par le Weekly Shōnen Jump pour lancer les futurs génies du Shonen et de l'humour.",
        "origin": "Créés en 1971 par Shūeisha, parrainés par Osamu Tezuka (action) et Fujio Akatsuka (humour gag).",
        "examples": "Lauréats ou mentionnés célèbres : Akira Toriyama, Eiichiro Oda, Masashi Kishimoto, Yoshihiro Togashi.",
        "impact": "Le rite de passage ultime pour devenir dessinateur professionnel sous contrat avec l'écurie prestigieuse du Shōnen Jump.",
    },
}

# --- 40 RELATIONS TRANSMÉDIAS ET MÉTA LIÉES AUX MAGAZINES ET AWARDS ---
AWARDS_AND_MAGAZINES_RELATIONS = [
    {
        "question": "Dans quel magazine a été prépublié le manga de dark fantasy Berserk de Kentaro Miura ?",
        "answer": "Le manga culte 'Berserk' de Kentaro Miura a été prépublié dans le magazine bimensuel de type Seinen 'Young Animal' édité par Hakusensha, depuis son lancement en 1992 jusqu'à la disparition de l'auteur.",
    },
    {
        "question": "Quel manga emblématique a été prépublié dans le Bessatsu Shōnen Magazine de Kōdansha de 2009 à 2021 ?",
        "answer": "Il s'agit de 'L'Attaque des Titans' ('Shingeki no Kyojin') de Hajime Isayama. C'est l'œuvre emblématique du Bessatsu Shōnen Magazine, dont le succès colossal a grandement développé la renommée du mensuel.",
    },
    {
        "question": "Quelle prestigieuse récompense cinématographique Hayao Miyazaki a-t-il obtenue pour Le Voyage de Chihiro en 2003 ?",
        "answer": "Hayao Miyazaki a remporté l'Oscar du meilleur film d'animation en 2003 pour 'Le Voyage de Chihiro' (Studio Ghibli). Ce film historique reste à ce jour le seul long-métrage d'animation japonais de l'histoire à avoir décroché cette statuette dorée.",
    },
    {
        "question": "Quel manga de Naoki Urasawa a remporté le tout premier Grand Prix du Prix culturel Osamu Tezuka en 1997 ?",
        "answer": "Le manga qui a décroché ce tout premier grand prix prestigieux est 'Monster' de Naoki Urasawa, récompensé pour son écriture dramatique et psychologique d'une profondeur littéraire inédite en manga.",
    },
    {
        "question": "Dans quel magazine hebdomadaire est prépubliée l'œuvre phare One Piece de Eiichiro Oda depuis 1997 ?",
        "answer": "Le chef-d'œuvre 'One Piece' de Eiichiro Oda est prépublié de manière hebdomadaire dans le 'Weekly Shōnen Jump' édité par Shūeisha, s'imposant comme le pilier absolu et le roi incontesté de l'histoire du magazine.",
    },
    {
        "question": "Quel prestigieux prix de bande dessinée américain Chainsaw Man de Tatsuki Fujimoto a-t-il remporté en 2021 et 2022 ?",
        "answer": "Le manga 'Chainsaw Man' de Tatsuki Fujimoto a remporté le prestigieux Prix Harvey du meilleur manga deux années consécutives (2021 et 2022), consacrant l'écriture imprévisible et novatrice de l'auteur aux États-Unis.",
    },
    {
        "question": "Dans quel mensuel prestigieux est prépublié le manga historique Vinland Saga de Makoto Yukimura depuis décembre 2005 ?",
        "answer": "Le manga 'Vinland Saga' est prépublié dans le prestigieux magazine mensuel 'Monthly Afternoon' édité par Kōdansha. Bien qu'il ait commencé brièvement dans le Weekly Shōnen Magazine, son rythme et sa maturité graphique ont justifié ce passage en mensuel Seinen.",
    },
    {
        "question": "Quel manga de combat tactique de Square Enix a été prépublié dans le Monthly Shōnen Gangan de 2001 à 2010 ?",
        "answer": "Il s'agit de 'Fullmetal Alchemist' d'Hiromu Arakawa. Ce chef-d'œuvre absolu de fantasy est le manga le plus vendu et le plus emblématique de l'histoire du magazine 'Monthly Shōnen Gangan'.",
    },
    {
        "question": "Quel célèbre manga d'enquête policière de Gosho Aoyama est le pilier absolu du magazine Weekly Shōnen Sunday depuis 1994 ?",
        "answer": "Il s'agit du manga 'Détective Conan' de Gosho Aoyama. C'est l'œuvre la plus longue et la plus populaire du 'Weekly Shōnen Sunday' édité par Shōgakukan.",
    },
    {
        "question": "Quel manga récent a remporté le 14ème Manga Taishō en 2021, s'imposant comme la nouvelle révélation Shonen ?",
        "answer": "Le manga lauréat du Manga Taishō 2021 est 'Frieren' ('Sousou no Frieren') écrit par Kanehito Yamada et dessiné par Tsukasa Abe, prépublié dans le Weekly Shōnen Sunday.",
    },
    {
        "question": "Quel manga illustré par Takeshi Obata et écrit par Tsugumi Ohba explore la vie des mangakas et les coulisses de la Shueisha ?",
        "answer": "Il s'agit de 'Bakuman'. Ce manga exceptionnel décrit avec réalisme et précision le quotidien exigeant des dessinateurs et le système de votes et de prépublication au sein du prestigieux 'Weekly Shōnen Jump'.",
    },
    {
        "question": "Quelle série de science-fiction spatiale de Makoto Yukimura a remporté le Prix Seiun de la meilleure bande dessinée en 2002 ?",
        "answer": "Le manga lauréat est 'Planetes', œuvre acclamée pour son réalisme scientifique et son traitement philosophique de la conquête spatiale et du traitement des débris en orbite.",
    },
    {
        "question": "Quel manga dramatique de Chica Umino, prépublié dans le magazine Young Animal, a remporté le Prix culturel Osamu Tezuka en 2014 ?",
        "answer": "Il s'agit de 'March Comes in Like a Lion' ('3-gatsu no Lion'). Ce chef-d'œuvre traitant de la solitude, de la résilience et du jeu de Shogi a remporté le Grand Prix culturel Osamu Tezuka.",
    },
    {
        "question": "Dans quel magazine hebdomadaire Seinen de Shueisha est prépubliée l'œuvre Oshi no Ko écrite par Aka Akasaka ?",
        "answer": "Le manga 'Oshi no Ko', illustré par Mengo Yokoyari et scénarisé par Aka Akasaka, est prépublié dans le 'Weekly Young Jump' de Shūeisha depuis avril 2020.",
    },
    {
        "question": "Quel magazine de Kōdansha a accueilli des œuvres cyberpunk cultes comme Akira de Katsuhiro Otomo et Ghost in the Shell de Masamune Shirow ?",
        "answer": "Il s'agit du 'Weekly Young Magazine' de Kōdansha. Ce magazine Seinen s'est imposé comme le berceau historique de la science-fiction cyberpunk et réaliste des années 80.",
    },
    {
        "question": "Quel manga d'investigation de Naoki Urasawa réinterprétant Astro Boy d'Osamu Tezuka a remporté le Grand Prix culturel Tezuka en 2005 ?",
        "answer": "Il s'agit de 'Pluto'. Ce thriller psychologique et d'anticipation robotique a été unanimement salué par la critique internationale pour son génie scénaristique et son hommage respectueux.",
    },
    {
        "question": "Quel manga de boxe fleuve de George Morikawa est prépublié dans le Weekly Shōnen Magazine de Kōdansha depuis 1989 ?",
        "answer": "Il s'agit de 'Hajime no Ippo'. Cette série légendaire sur la boxe compte plus de 130 volumes et représente l'un des records absolus de longévité du 'Weekly Shōnen Magazine'.",
    },
    {
        "question": "Quel dessinateur et auteur d'horreur japonais a été récompensé de multiples Prix Eisner aux États-Unis pour ses œuvres angoissantes ?",
        "answer": "Il s'agit du maître de l'horreur 'Junji Ito'. Ses œuvres comme 'Spirale', 'Remina' ou ses anthologies ont décroché plusieurs Prix Eisner, consacrant son style visuel horrifique unique au monde.",
    },
    {
        "question": "Quel festival de bande dessinée européen de premier plan a décerné un prix spécial du cinquantenaire à l'auteur de thriller Naoki Urasawa en 2023 ?",
        "answer": "Il s'agit du prestigieux 'Festival international de la bande dessinée d'Angoulême' en France, réaffirmant le statut d'auteur littéraire majeur de Naoki Urasawa à l'échelle européenne.",
    },
    {
        "question": "Dans quel magazine mensuel de prépublication Seinen de Shueisha est éditée la suite de JoJo's Bizarre Adventure, Steel Ball Run ?",
        "answer": "La partie 7 de JoJo's Bizarre Adventure, 'Steel Ball Run', a été prépubliée dans le magazine mensuel 'Ultra Jump' de Shūeisha. Ce changement de rythme a permis à Hirohiko Araki de passer d'un format shonen hebdomadaire à un format Seinen mensuel plus complexe graphiquement.",
    },
    {
        "question": "Quel concours semestriel organisé par Shueisha a révélé des génies du manga comme Akira Toriyama ou Masashi Kishimoto ?",
        "answer": "Il s'agit du légendaire 'Prix Tezuka' ('Tezuka Award'), organisé depuis 1971 par la rédaction du Weekly Shōnen Jump pour dénicher les nouveaux auteurs de shonen d'action et d'aventure.",
    },
    {
        "question": "Quel manga de dark fantasy sur les démons de Koyoharu Gotouge a brisé tous les records de vente au sein du Weekly Shōnen Jump ?",
        "answer": "Il s'agit de 'Demon Slayer' ('Kimetsu no Yaiba'). Prépublié de 2016 à 2020 dans le Weekly Shōnen Jump, ce manga est devenu un véritable phénomène sociétal mondial.",
    },
    {
        "question": "Quel manga d'action historique de Yasuhisa Hara se déroulant durant la période des Royaumes combattants de Chine est le pilier du magazine Weekly Young Jump ?",
        "answer": "Il s'agit du manga 'Kingdom'. Cette fresque militaire épique est prépubliée dans le 'Weekly Young Jump' de Shūeisha depuis 2006.",
    },
    {
        "question": "Quel manga de football de Muneyuki Kaneshiro et Yusuke Nomura a remporté le 45ème Prix du manga Kōdansha dans la catégorie Shōnen en 2021 ?",
        "answer": "Il s'agit du manga de sport intense 'Blue Lock', prépublié dans le Weekly Shōnen Magazine de Kōdansha.",
    },
    {
        "question": "Quel manga de romance lycéenne drôle de Tomohito Oda a remporté le 67ème Prix Shōgakukan dans la catégorie Catégorie Générale en 2022 ?",
        "answer": "Le manga récompensé est 'Komi cherche ses mots' ('Komi-san wa, Komyushou desu.'), prépublié dans le magazine Weekly Shōnen Sunday.",
    },
    {
        "question": "Dans quel magazine de type Shōjo de l'éditeur Shueisha a été prépublié le manga classique Chibi Maruko-chan de Momoko Sakura ?",
        "answer": "Le manga culte 'Chibi Maruko-chan' a été prépublié dans le célèbre mensuel Shōjo 'Ribon' de Shūeisha, s'imposant comme l'une des œuvres les plus populaires de l'histoire du magazine.",
    },
    {
        "question": "Quelle série animée de ufotable a remporté le prix prestigieux de l'Anime de l'Année aux Tokyo Anime Award Festival en 2020 et 2022 ?",
        "answer": "Il s'agit de la franchise 'Demon Slayer' ('Kimetsu no Yaiba'), récompensée par l'industrie japonaise à Tokyo pour l'excellence spectaculaire de sa production technique et de son animation.",
    },
    {
        "question": "Quel célèbre manga d'aventures et d'alchimie d'Hiromu Arakawa a remporté le 49ème Prix Shōgakukan dans la catégorie Shonen en 2004 ?",
        "answer": "Le manga lauréat est 'Fullmetal Alchemist', prépublié dans le mensuel Gangan de Square Enix et acclamé mondialement pour son scénario sans faille.",
    },
    {
        "question": "Dans quel magazine de prépublication de type Shōjo a débuté la série fantastique Fushigi Yugi de Yuu Watase ?",
        "answer": "Il s'agit du magazine bimensuel 'Sho-Comi' de Shōgakukan, réputé pour héberger des romances intenses mariant drame historique et sentiments adolescents.",
    },
    {
        "question": "Quel prestigieux prix national d'art médiatique du gouvernement japonais a récompensé Vagabond de Takehiko Inoue du Grand Prix de la division Manga en 2000 ?",
        "answer": "Il s'agit du Grand Prix du 'Japan Media Arts Festival', réaffirmant le statut d'œuvre d'art picturale suprême du manga de Takehiko Inoue.",
    },
    {
        "question": "Quel manga parodique de super-héros dessiné par Yusuke Murata et scénarisé par ONE a été adapté en un animé acclamé par le studio Madhouse ?",
        "answer": "Il s'agit de 'One Punch Man'. Cette œuvre culte de combat humoristique est publiée en ligne sur le portail affilié au magazine Seinen Tonari no Young Jump de Shūeisha.",
    },
    {
        "question": "Quel prix prestigieux de science-fiction au Japon la série de combat spatial Astra Lost in Space de Kenta Shinohara a-t-elle remportée en 2020 ?",
        "answer": "Le manga a remporté le 'Prix Seiun' de la meilleure bande dessinée de science-fiction, saluant la structure narrative parfaite de son intrigue et son dénouement à suspense.",
    },
    {
        "question": "Quelle série d'animation acclamée de CD Projekt Red réalisée par Trigger a remporté le titre suprême d'Anime de l'Année aux Crunchyroll Anime Awards en 2023 ?",
        "answer": "Il s'agit de la série cyberpunk 'Cyberpunk: Edgerunners' réalisée par Hiroyuki Imaishi au sein du studio japonais Trigger.",
    },
    {
        "question": "Quel manga culte explorant le jeu de Go par le dessinateur Takeshi Obata a remporté le Prix de la nouveauté du Prix culturel Tezuka en 2003 ?",
        "answer": "Le manga lauréat est 'Hikaru no Go', scénarisé par Yumi Hotta, crédité pour avoir suscité une ferveur nationale et relancé la pratique du Go chez les jeunes au Japon.",
    },
    {
        "question": "Dans quel magazine hebdomadaire Shonen de Kodansha est prépublié le manga de fantasy de Hiro Mashima, Fairy Tail ?",
        "answer": "Le manga à succès 'Fairy Tail' a été prépublié dans le magazine 'Weekly Shōnen Magazine' de Kōdansha de 2006 à 2017.",
    },
    {
        "question": "Quel auteur pionnier de mangas qualifié de 'Dieu du Manga' a donné son nom à la plus haute distinction de valeur littéraire de bande dessinée au Japon ?",
        "answer": "Il s'agit de 'Osamu Tezuka', créateur de chefs-d'œuvre fondateurs comme Astro Boy ou Black Jack, honoré à travers le prestigieux Prix culturel Osamu Tezuka parrainé par l'Asahi Shimbun.",
    },
    {
        "question": "Quel manga récent de science-fiction fantastique de Kaiu Shirai et Posuka Demizu a remporté le 63ème Prix Shōgakukan dans la catégorie Shonen en 2018 ?",
        "answer": "Il s'agit de 'The Promised Neverland' ('Yakusoku no Neverland'), prépublié dans le Weekly Shōnen Jump et acclamé pour son atmosphère angoissante de thriller d'évasion.",
    },
    {
        "question": "Dans quel magazine Seinen mensuel de Kodansha est prépublié le chef-d'œuvre philosophique de science-fiction Parasyte de Hitoshi Iwaaki ?",
        "answer": "Le manga culte 'Parasyte' ('Kiseijuu') a été prépublié dans le prestigieux magazine mensuel 'Monthly Afternoon' de Kōdansha.",
    },
    {
        "question": "Quel auteur de dark fantasy a créé le manga culte Berserk au sein du magazine Young Animal d'Hakusensha ?",
        "answer": "Il s'agit du légendaire 'Kentaro Miura', dont le décès prématuré en 2021 a bouleversé l'ensemble de la communauté mondiale de la japanimation.",
    },
    {
        "question": "Quel manga culte mêlant comédie romantique et paranormal par Rumiko Takahashi a été prépublié dans le magazine Weekly Shōnen Sunday ?",
        "answer": "Il s'agit de 'Ranma 1/2', prépublié dans le 'Weekly Shōnen Sunday' de Shōgakukan de 1987 à 1996, s'imposant comme une référence absolue d'humour burlesque.",
    },
]
