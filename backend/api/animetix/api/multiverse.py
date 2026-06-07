from rest_framework.views import APIView
from rest_framework.response import Response
from dependency_injector.wiring import inject, Provide
from ..containers import Container

class MultiverseGalleryView(APIView):
    @inject
    def __init__(
        self, 
        neo4j_manager=Provide[Container.persistence.graph_persistence_port],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.neo4j_manager = neo4j_manager

    def get(self, request):
        query = """
        MATCH (m:Media {is_synthetic: true})-[:BELONGS_TO]->(g:Genre)
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(m)
        RETURN m, g, collect(c) as characters
        """
        results = self.neo4j_manager.execute_query(query)
        
        nodes = []
        links = []
        genres_added = set()
        universes_added = set()
        
        for record in results:
            media = record.get('m')
            genre = record.get('g')
            characters = record.get('characters', [])
            
            if not media or not genre:
                continue

            genre_name = genre.get('name')
            genre_id = f"genre_{genre_name}"
            
            if genre_id not in genres_added:
                nodes.append({
                    "id": genre_id,
                    "name": genre_name,
                    "type": "genre",
                    "val": 15
                })
                genres_added.add(genre_id)
            
            universe_name = media.get('name') or media.get('title')
            if universe_name not in universes_added:
                nodes.append({
                    "id": universe_name,
                    "name": universe_name,
                    "type": "universe",
                    "val": 10,
                    "metadata": {
                        "description": media.get('description'),
                        "cosmology": media.get('cosmology'),
                        "characters": [c.get('name') for c in characters]
                    }
                })
                universes_added.add(universe_name)
                
                links.append({
                    "source": universe_name,
                    "target": genre_id
                })
                
        return Response({
            "nodes": nodes,
            "links": links
        })
