import logging
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from core.domain.services.llm_service import LLMService
from core.ports.graph_persistence_port import GraphPersistencePort

logger = logging.getLogger("animetix.mlops.graph_community_partitioner")

# ── Tunables ──────────────────────────────────────────────────────────────────
# The map used to be capped so hard it could never show more than a handful of
# works: the source query had a `LIMIT 100`, communities were just node labels,
# and each kept only its first 10 entities (first word only). These bounds are
# the real, generous limits — sized for an offline nightly job, not a request.
MAX_MEDIA = 5000  # safety valve on the graph pull (was a hard LIMIT 100)
MAX_COMMUNITIES = 30  # bounds the number of LLM summary calls
MAX_ENTITIES_PER_COMMUNITY = (
    40  # front shows 7 landmarks / 12 chips; keep the rest for weight
)
MIN_COMMUNITY_SIZE = 2
# An attribute shared by more works than this is too generic to be a useful link
# (e.g. a mega-genre): linking on it would fuse everything into one blob and also
# blow up the edge count. Skipping it sharpens the communities.
GENERIC_ATTR_THRESHOLD = 80

# Genres AniList (vocabulaire contrôlé) : base des noms de communautés, bien plus
# lisibles que les tags bruts.
GENRE_VOCAB = {
    "Action",
    "Adventure",
    "Comedy",
    "Drama",
    "Ecchi",
    "Fantasy",
    "Horror",
    "Mahou Shoujo",
    "Mecha",
    "Music",
    "Mystery",
    "Psychological",
    "Romance",
    "Sci-Fi",
    "Slice of Life",
    "Sports",
    "Supernatural",
    "Thriller",
}
# Tags démographiques / de casting / de format : peu descriptifs, ils font de
# mauvais noms de cluster — écartés du nom ET des puces de thèmes.
THEME_NOISE = {
    "Male Protagonist",
    "Female Protagonist",
    "Primarily Male Cast",
    "Primarily Female Cast",
    "Primarily Teen Cast",
    "Primarily Adult Cast",
    "Primarily Child Cast",
    "Ensemble Cast",
    "Heterosexual",
    "Nudity",
}


class GraphCommunityPartitioner:
    """
    Service MLOps responsable du partitionnement du graphe Neo4j en communautés
    thématiques, de la génération de résumés conceptuels par LLM et de leur
    indexation pour la recherche sémantique de communautés.

    Le partitionnement réel est fait par détection de communautés de Louvain
    (networkx) sur une projection « œuvre ↔ œuvre » reliant les Media qui
    partagent des attributs (studio, thème, auteur, saga). Trois niveaux de repli
    garantissent qu'une carte est toujours produite : Louvain → regroupement par
    label → communautés d'exemple.
    """

    def __init__(
        self, neo4j_manager: Optional[GraphPersistencePort], llm_service: LLMService
    ):
        self.neo4j_manager = neo4j_manager
        self.llm_service = llm_service
        self.communities: List[Dict[str, Any]] = []

    def run_partitioning(self) -> List[Dict[str, Any]]:
        """Partitionne le graphe et retourne les communautés vectorisables."""
        if not self.neo4j_manager:
            logger.warning("⚠️ Neo4j Manager indisponible — communautés d'exemple.")
            return self._generate_mock_communities()

        # 1) Vrai partitionnement (Louvain) sur la projection des œuvres.
        try:
            communities = self._detect_communities_louvain()
            if communities:
                logger.info(
                    "✅ GraphRAG: %d communautés détectées (Louvain).", len(communities)
                )
                self.communities = communities
                return communities
            logger.info("Louvain n'a produit aucune communauté — repli par label.")
        except Exception as e:
            logger.error("❌ Partitionnement Louvain échoué (%s) — repli par label.", e)

        # 2) Repli : regroupement par type de nœud, mais SANS les anciens plafonds.
        try:
            communities = self._detect_communities_by_label()
            if communities:
                logger.info(
                    "✅ GraphRAG: %d communautés (regroupement par label).",
                    len(communities),
                )
                self.communities = communities
                return communities
        except Exception as e:
            logger.error(
                "❌ Regroupement par label échoué (%s) — communautés d'exemple.", e
            )

        # 3) Dernier repli : communautés d'exemple de haute fidélité.
        return self._generate_mock_communities()

    # ── Louvain ───────────────────────────────────────────────────────────────
    def _detect_communities_louvain(self) -> List[Dict[str, Any]]:
        import networkx as nx
        from networkx.algorithms.community import louvain_communities

        cypher = f"""
        MATCH (m:Media)
        OPTIONAL MATCH (m)-[:PRODUCED_BY]->(s:Studio)
        OPTIONAL MATCH (m)-[:HAS_THEME]->(t:MicroTag)
        OPTIONAL MATCH (m)-[:CREATED_BY]->(p:Person)
        OPTIONAL MATCH (sg:Saga)-[:CONTAINS_MEDIA]->(m)
        WITH m,
             collect(DISTINCT s.name) AS studios,
             collect(DISTINCT t.name) AS themes,
             collect(DISTINCT p.name) AS people,
             collect(DISTINCT sg.name) AS sagas
        RETURN m.title AS title, m.popularity AS popularity,
               m.title_english AS title_english, m.title_native AS title_native,
               m.image_url AS image_url, studios, themes, people, sagas
        LIMIT {MAX_MEDIA}
        """
        # Garanti non-None : run_partitioning() court-circuite vers les communautés
        # d'exemple quand neo4j_manager est absent avant d'appeler cette méthode.
        assert self.neo4j_manager is not None
        rows = [r for r in self.neo4j_manager.execute_query(cypher) if r.get("title")]
        if len(rows) < MIN_COMMUNITY_SIZE:
            return []

        # Index attribut -> œuvres, œuvre -> attributs, popularité et titres
        # alternatifs par œuvre (tri par popularité + affichage multi-titres).
        attr_index: dict[str, list[str]] = defaultdict(list)
        media_attrs: dict[str, list[str]] = {}
        media_pop: dict[str, float] = {}
        media_meta: dict[str, dict[str, Any]] = {}
        for row in rows:
            title = row["title"]
            media_pop[title] = row.get("popularity") or 0
            media_meta[title] = {
                "title": title,
                "title_english": row.get("title_english"),
                "title_native": row.get("title_native"),
                "image_url": row.get("image_url"),
            }
            attrs: list[str] = []
            for key, prefix in (
                ("studios", "studio"),
                ("themes", "theme"),
                ("people", "person"),
                ("sagas", "saga"),
            ):
                for value in row.get(key) or []:
                    if value:
                        tag = f"{prefix}:{value}"
                        attrs.append(tag)
                        attr_index[tag].append(title)
            media_attrs[title] = attrs

        # Projection : deux œuvres sont reliées si elles partagent un attribut
        # (pondéré par le nombre d'attributs communs). On saute les attributs
        # trop rares (aucun lien) ou trop génériques (fusionnent tout).
        graph = nx.Graph()
        graph.add_nodes_from(media_attrs)
        for members in attr_index.values():
            uniq = list(dict.fromkeys(members))
            if len(uniq) < 2 or len(uniq) > GENERIC_ATTR_THRESHOLD:
                continue
            for i in range(len(uniq)):
                for j in range(i + 1, len(uniq)):
                    a, b = uniq[i], uniq[j]
                    if graph.has_edge(a, b):
                        graph[a][b]["weight"] += 1
                    else:
                        graph.add_edge(a, b, weight=1)

        if graph.number_of_edges() == 0:
            return []

        parts = [
            part
            for part in louvain_communities(graph, weight="weight", seed=42)
            if len(part) >= MIN_COMMUNITY_SIZE
        ]
        parts.sort(key=len, reverse=True)
        parts = parts[:MAX_COMMUNITIES]

        communities: List[Dict[str, Any]] = []
        used_names: set[str] = set()
        for i, members in enumerate(parts):
            theme_counts: Counter = Counter()
            for title in members:
                for attr in media_attrs.get(title, []):
                    if attr.startswith("theme:"):
                        theme_counts[attr[len("theme:") :]] += 1
            # On classe les thèmes en écartant les tags démographiques peu parlants,
            # et en plaçant les GENRES d'abord : un nom « Action & Aventure » est
            # bien plus lisible que « Male Protagonist & Heterosexual ».
            ranked = [t for t, _ in theme_counts.most_common() if t not in THEME_NOISE]
            ranked = [t for t in ranked if t in GENRE_VOCAB] + [
                t for t in ranked if t not in GENRE_VOCAB
            ]
            top_themes = ranked[:8]
            # Nom = 2 genres dominants, étendu à un 3e en cas de collision (plutôt
            # qu'un « #5 » opaque).
            name = None
            for k in (2, 3):
                candidate = (
                    "Communauté " + " & ".join(ranked[:k])
                    if ranked
                    else f"Communauté {i + 1}"
                )
                if candidate not in used_names:
                    name = candidate
                    break
            if name is None:
                base = (
                    "Communauté " + " & ".join(ranked[:2])
                    if ranked
                    else f"Communauté {i + 1}"
                )
                suffix = 2
                while f"{base} ({suffix})" in used_names:
                    suffix += 1
                name = f"{base} ({suffix})"
            used_names.add(name)
            # Œuvres triées par popularité décroissante, dédupliquées par titre.
            ordered = sorted(
                dict.fromkeys(members), key=lambda t: (-(media_pop.get(t) or 0), t)
            )[:MAX_ENTITIES_PER_COMMUNITY]
            # Chaque œuvre porte ses titres alternatifs (original + anglais) pour
            # un affichage enrichi côté UI ; le résumé n'a besoin que des titres.
            entities = [media_meta.get(t, {"title": t}) for t in ordered]
            communities.append(
                {
                    "id": f"community_{i}",
                    "name": name,
                    # Les tags/genres qui définissent le regroupement (mis en avant côté UI).
                    "themes": top_themes,
                    "summary": self._summarize(name, ordered, theme_counts),
                    "entities": entities,
                }
            )
        return communities

    # ── Repli : regroupement par label (déplafonné) ─────────────────────────────
    def _detect_communities_by_label(self) -> List[Dict[str, Any]]:
        cypher = f"""
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n.name AS entity_name, labels(n)[0] AS type,
               m.name AS connected_entity, type(r) AS relationship
        LIMIT {MAX_MEDIA}
        """
        # Garanti non-None : cf. la garde dans run_partitioning().
        assert self.neo4j_manager is not None
        nodes = self.neo4j_manager.execute_query(cypher)
        if not nodes:
            return []

        groups: dict[str, list[str]] = defaultdict(list)
        for item in nodes:
            name = item.get("entity_name")
            if name:
                groups[item.get("type", "General")].append(name)

        communities: List[Dict[str, Any]] = []
        for i, (label, names) in enumerate(list(groups.items())[:MAX_COMMUNITIES]):
            entities = list(dict.fromkeys(names))[:MAX_ENTITIES_PER_COMMUNITY]
            name = f"Communauté {label}"
            communities.append(
                {
                    "id": f"community_{i}",
                    "name": name,
                    "themes": [label],
                    "summary": self._summarize(name, entities, Counter()),
                    "entities": entities,
                }
            )
        return communities

    # ── Résumé LLM (avec repli déterministe) ────────────────────────────────────
    def _summarize(
        self, name: str, entities: List[str], theme_counts: "Counter"
    ) -> str:
        top_themes = [t for t, _ in theme_counts.most_common(6)]
        works = ", ".join(entities[:20])
        # Les œuvres sont affichées en chips et les thèmes mis en avant à part :
        # le résumé de repli ne les répète pas, il ne dit que ce qui les relie.
        deterministic = f"{name} regroupe {len(entities)} œuvres proches" + (
            f" autour de : {', '.join(top_themes)}." if top_themes else "."
        )
        try:
            prompt = (
                f"Rédige un court résumé (2-3 phrases, grand public) du groupe d'œuvres "
                f"« {name} », en expliquant ce qu'elles ont en commun.\n"
                f"Œuvres : {works}\n"
                + (
                    f"Thèmes dominants : {', '.join(top_themes)}\n"
                    if top_themes
                    else ""
                )
            )
            system_prompt = (
                "Tu es un guide d'anime et de manga clair et accessible. "
                "Évite le jargon technique."
            )
            raw = self.llm_service.generate(prompt, system_prompt, use_slm=True)
            summary = raw if isinstance(raw, str) else str(raw or "")
            # Le SLM local fuit parfois des balises de raisonnement (<think>…</think>),
            # parfois tronquées. On les retire et on rejette une sortie trop courte
            # (« Heter, </think> ») au profit du résumé déterministe.
            summary = re.sub(r"(?is)<think>.*?</think>", " ", summary)
            summary = re.sub(r"</?think>", " ", summary, flags=re.IGNORECASE)
            summary = re.sub(r"\s+", " ", summary).strip()
            # Rejette aussi les sorties dégénérées (« Magic Magic Magic… ») : un
            # texte sain a un ratio de mots uniques élevé.
            words = summary.split()
            degenerate = (
                bool(words) and len({w.lower() for w in words}) / len(words) < 0.4
            )
            return deterministic if (len(summary) < 25 or degenerate) else summary
        except Exception as e:
            logger.warning("Résumé LLM indisponible pour %s (%s).", name, e)
            return deterministic

    def search_communities(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Recherche sémantique simple de communautés proches d'une requête."""
        if not self.communities:
            self.run_partitioning()

        results = []
        q_lower = query.lower()
        for community in self.communities:
            score = 0.0
            if any(term in q_lower for term in community["name"].lower().split()):
                score += 0.5
            if any(term in q_lower for term in community["summary"].lower().split()):
                score += 0.3
            if score > 0.0:
                results.append((score, community))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def _generate_mock_communities(self) -> List[Dict[str, Any]]:
        """Communautés d'exemple de haute fidélité (dev / graphe indisponible)."""
        logger.info("📦 Génération des communautés thématiques d'exemple.")
        self.communities = [
            {
                "id": "community_dark_fantasy",
                "name": "Communauté Dark Fantasy & Seinen",
                "summary": "Les chefs-d'œuvre sombres et adultes du seinen : lutte existentielle, esthétique gothique et dilemmes moraux profonds.",
                "entities": [
                    "Berserk",
                    "Tokyo Ghoul",
                    "Vinland Saga",
                    "Vagabond",
                    "Monster",
                    "Claymore",
                    "Attack on Titan",
                ],
            },
            {
                "id": "community_shonen_jump",
                "name": "Communauté Shōnen Jump",
                "summary": "Les grandes sérialisations d'action du Weekly Shōnen Jump : amitié, effort et systèmes de combat complexes.",
                "entities": [
                    "One Piece",
                    "Naruto",
                    "Bleach",
                    "Dragon Ball",
                    "Hunter x Hunter",
                    "My Hero Academia",
                    "Jujutsu Kaisen",
                    "Demon Slayer",
                ],
            },
            {
                "id": "community_isekai",
                "name": "Communauté Isekai",
                "summary": "Des héros transportés dans un autre monde, souvent inspiré du jeu de rôle : aventure, progression et second départ.",
                "entities": [
                    "Mushoku Tensei",
                    "Re:Zero",
                    "Konosuba",
                    "Overlord",
                    "That Time I Got Reincarnated as a Slime",
                    "Sword Art Online",
                ],
            },
            {
                "id": "community_mecha_scifi",
                "name": "Communauté Mecha & Science-Fiction",
                "summary": "Robots géants, guerres spatiales et grandes questions sur l'humanité et la technologie.",
                "entities": [
                    "Gundam",
                    "Neon Genesis Evangelion",
                    "Code Geass",
                    "Ghost in the Shell",
                    "Gurren Lagann",
                    "86 Eighty-Six",
                ],
            },
            {
                "id": "community_slice_of_life",
                "name": "Communauté Tranche de vie",
                "summary": "Le quotidien en douceur : amitié, passions et petits bonheurs, sans grand enjeu dramatique.",
                "entities": [
                    "K-On!",
                    "Yuru Camp",
                    "A Silent Voice",
                    "Barakamon",
                    "Non Non Biyori",
                ],
            },
            {
                "id": "community_sports",
                "name": "Communauté Sport",
                "summary": "Dépassement de soi, esprit d'équipe et matchs à couper le souffle.",
                "entities": [
                    "Haikyuu!!",
                    "Kuroko no Basket",
                    "Blue Lock",
                    "Slam Dunk",
                    "Ace of Diamond",
                ],
            },
            {
                "id": "community_romance",
                "name": "Communauté Romance & École",
                "summary": "Histoires de cœur, comédies romantiques et vie lycéenne.",
                "entities": [
                    "Horimiya",
                    "Toradora!",
                    "Your Lie in April",
                    "Kaguya-sama: Love is War",
                    "Fruits Basket",
                ],
            },
        ]
        # Thèmes du regroupement, dérivés du nom (mis en avant côté UI).
        for community in self.communities:
            community.setdefault(
                "themes", community["name"].replace("Communauté ", "").split(" & ")
            )
        return self.communities
