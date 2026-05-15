import os
import chromadb
from dagster import ConfigurableResource
from typing import Optional, Set, List, Dict
from neo4j import GraphDatabase

class ChromaResource(ConfigurableResource):
    host: str = "localhost"
    port: int = 8000
    persist_path: str = "data/chroma_db"

    def get_client(self):
        try:
            client = chromadb.HttpClient(host=self.host, port=self.port)
            client.heartbeat()
            return client
        except Exception:
            return chromadb.PersistentClient(path=self.persist_path)

    def get_collection(self, name: str):
        client = self.get_client()
        return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

class Neo4jResource(ConfigurableResource):
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"

    def get_driver(self):
        return GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def execute_query(self, query: str, parameters: Optional[Dict] = None):
        driver = self.get_driver()
        with driver.session() as session:
            return session.run(query, parameters).data()
        driver.close()
