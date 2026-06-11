import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

_client: chromadb.Client = None
_model: SentenceTransformer = None


def _get_client() -> chromadb.Client:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_or_create_collection(name: str) -> chromadb.Collection:
    return _get_client().get_or_create_collection(name=name)


def add_documents(collection_name: str, documents: List[str], metadatas: List[Dict], ids: List[str]) -> None:
    collection = get_or_create_collection(collection_name)
    model = _get_model()
    embeddings = model.encode(documents).tolist()
    collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)


def query(collection_name: str, query_text: str, n_results: int = 3) -> List[Dict]:
    collection = get_or_create_collection(collection_name)
    model = _get_model()
    embedding = model.encode([query_text]).tolist()
    results = collection.query(query_embeddings=embedding, n_results=n_results, include=["documents", "metadatas", "distances"])

    items = []
    for i in range(len(results["documents"][0])):
        items.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "score": 1 - results["distances"][0][i],
        })
    return items


def collection_exists_and_populated(collection_name: str) -> bool:
    try:
        col = _get_client().get_collection(name=collection_name)
        return col.count() > 0
    except Exception:
        return False
