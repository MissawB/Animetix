import chromadb
from chromadb.config import Settings
import os
import logging

# Logger
logger = logging.getLogger("animetix." + __name__)

# Détection robuste de la racine du projet
# __file__ is at backend/pipeline/chroma_client.py
# parent is backend/pipeline, parent.parent is src, parent.parent.parent is Double_scenario_Project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")

class ChromaManager:
    def __init__(self):
        # En production (HF Spaces), on utilise le client HTTP car Chroma tourne en service séparé via Supervisor
        # En local, on peut rester sur PersistentClient
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        # Authentification ChromaDB
        auth_provider = os.getenv("CHROMA_CLIENT_AUTH_PROVIDER")
        auth_credentials = os.getenv("CHROMA_CLIENT_AUTH_CREDENTIALS")
        
        settings = Settings()
        if auth_provider and auth_credentials:
            settings = Settings(
                chroma_client_auth_provider=auth_provider,
                chroma_client_auth_credentials=auth_credentials
            )

        try:
            # On tente de se connecter au serveur HTTP (lancé par Supervisor ou Docker)
            self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port, settings=settings)
            # Test de connexion simple
            self.client.heartbeat()
            logger.info(f"[OK] Connected to ChromaDB Server at {chroma_host}:{chroma_port}")
        except Exception:
            # Fallback sur le client persistant si le serveur n'est pas joignable (ex: exécution d'un script seul)
            logger.info(f"[INFO] ChromaDB Server not found, falling back to PersistentClient at {CHROMA_PATH}")
            os.makedirs(CHROMA_PATH, exist_ok=True)
            self.client = chromadb.PersistentClient(path=CHROMA_PATH)

    def get_collection(self, name):
        """Récupère ou crée une collection."""
        return self.client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    def get_all_ids(self, collection_name):
        """Récupère tous les IDs d'une collection de manière sécurisée (pagination) pour éviter 'too many SQL variables'."""
        collection = self.get_collection(collection_name)
        all_ids = set()
        limit = 10000
        offset = 0
        
        while True:
            # On demande uniquement les IDs (include=[]) pour la performance
            results = collection.get(limit=limit, offset=offset, include=[])
            batch_ids = results.get('ids', [])
            if not batch_ids:
                break
            all_ids.update(batch_ids)
            offset += limit
            
        return all_ids

    def add_to_collection(self, collection_name, ids, embeddings, metadatas):
        """Ajoute des données à une collection de manière efficace."""
        collection = self.get_collection(collection_name)
        
        # ChromaDB supporte l'ajout par lots
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            collection.add(
                ids=ids[i:end],
                embeddings=embeddings[i:end].tolist() if hasattr(embeddings, 'tolist') else embeddings[i:end],
                metadatas=metadatas[i:end]
            )
        logger.info(f"✅ Added {len(ids)} items to Chroma collection '{collection_name}'")

    def query_collection(self, collection_name, query_texts=None, query_embeddings=None, n_results=10):
        """Recherche dans une collection avec support hybride."""
        collection = self.get_collection(collection_name)
        
        if query_texts:
            # Recherche hybride automatique si des textes sont fournis
            return collection.query(
                query_texts=query_texts,
                n_results=n_results
            )
        else:
            return collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results
            )

# Instance globale pour usage facile
chroma_manager = ChromaManager()
