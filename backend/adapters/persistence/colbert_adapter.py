# -*- coding: utf-8 -*-
"""
Late Interaction ColBERT Adapter for Animetix.
Calculates token-level MaxSim similarity scores between query and documents.
"""

import logging  # noqa: E402
import numpy as np  # noqa: E402
from typing import List, Dict  # noqa: E402

logger = logging.getLogger("animetix.colbert")


class LateInteractionColBERTAdapter:
    def __init__(
        self, model_name: str = "colbert-ir/colbertv2.0", dimension: int = 128
    ):
        self.model_name = model_name
        self.dimension = dimension
        self._tokenizer = None
        self._model = None
        self._initialized = False

    def _lazy_init(self):
        """Initialise paresseusement les modèles Hugging Face."""
        if self._initialized:
            return
        try:
            from transformers import AutoTokenizer, AutoModel  # noqa: E402

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, revision="main"
            )  # nosec B615
            self._model = AutoModel.from_pretrained(self.model_name, revision="main")  # nosec B615
            self._initialized = True
            logger.info(
                f"ColBERT Adapter initialized successfully with model {self.model_name}."
            )
        except Exception as e:
            logger.warning(
                f"Could not load Hugging Face ColBERT model '{self.model_name}' offline/online ({e}). "
                f"Falling back to deterministic token-level vector simulation."
            )
            self._tokenizer = None
            self._model = None
            self._initialized = True

    def tokenize_and_embed(self, text: str) -> np.ndarray:
        """
        Extrait les embeddings au niveau des jetons (tokens).
        Retourne un tenseur numpy de forme (N_tokens, dimension).
        """
        self._lazy_init()

        # Mode Hugging Face Réel
        if self._model and self._tokenizer:
            try:
                import torch  # noqa: E402

                inputs = self._tokenizer(
                    text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
                )
                with torch.no_grad():
                    outputs = self._model(**inputs)
                # Les embeddings des tokens se trouvent dans les états cachés de la dernière couche
                token_embeddings = outputs.last_hidden_state[0].cpu().numpy()

                # Projection/Tranchage à la dimension cible
                if token_embeddings.shape[1] != self.dimension:
                    # Projection simple via SVD ou tranchage deterministe
                    token_embeddings = token_embeddings[:, : self.dimension]

                # Normalisation L2 pour chaque vecteur de token
                norms = np.linalg.norm(token_embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1e-12
                return token_embeddings / norms
            except Exception as e:
                logger.error(f"Error during real ColBERT embedding generation: {e}")

        # Mode Simulée Déterministe (sans dépendances lourdes / mode test / mode hors-ligne)
        words = text.split()
        if not words:
            words = ["empty"]

        embeddings = []
        for word in words:
            # Génération d'un vecteur déterministe basé sur le hachage du mot
            np.random.seed(abs(hash(word)) % (2**31 - 1))
            vec = np.random.randn(self.dimension)
            vec /= np.linalg.norm(vec) + 1e-12
            embeddings.append(vec)

        return np.array(embeddings)

    def calculate_maxsim(
        self, query_embeddings: np.ndarray, doc_embeddings: np.ndarray
    ) -> float:
        """
        Calcule l'interaction tardive MaxSim entre les tenseurs de jetons.
        Formule : Sum_i ( Max_j ( Query_i . Doc_j ) )
        """
        # query_embeddings : (L_q, D)
        # doc_embeddings : (L_d, D)
        if query_embeddings.size == 0 or doc_embeddings.size == 0:
            return 0.0

        # Matrice de similarité cosinus entre tous les couples de tokens (L_q, L_d)
        similarity_matrix = np.dot(query_embeddings, doc_embeddings.T)

        # Pour chaque token de la requête, on prend la similarité maximale dans le document
        max_similarities = np.max(similarity_matrix, axis=1)

        # Somme de ces similarités maximales
        return float(np.sum(max_similarities))

    def rank_documents(
        self, query: str, documents: List[Dict], text_field: str = "description"
    ) -> List[Dict]:
        """
        Classe une liste de documents par rapport à une requête en utilisant MaxSim.
        """
        if not documents:
            return []

        query_embeddings = self.tokenize_and_embed(query)
        ranked_docs = []

        for doc in documents:
            doc_text = doc.get(text_field, doc.get("title", ""))
            doc_embeddings = self.tokenize_and_embed(doc_text)

            score = self.calculate_maxsim(query_embeddings, doc_embeddings)

            # Duplication pour ne pas altérer l'original
            doc_copy = dict(doc)
            doc_copy["colbert_score"] = score
            ranked_docs.append(doc_copy)

        # Tri descendant par score ColBERT
        ranked_docs.sort(key=lambda x: x["colbert_score"], reverse=True)
        return ranked_docs
