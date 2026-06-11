"""
Indexes the knowledge base into ChromaDB.
Run once (or re-run to refresh): python -m rag.indexer
"""
import json
import os
from typing import List
from rag.chroma_store import add_documents, collection_exists_and_populated

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
GUIDELINES_COLLECTION = "brand_guidelines"
CAMPAIGNS_COLLECTION = "example_campaigns"


def _chunk_markdown(text: str, chunk_size: int = 400) -> List[str]:
    """Split markdown into overlapping chunks by section, then by size."""
    sections = []
    current = []
    for line in text.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    chunks = []
    for section in sections:
        words = section.split()
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i: i + chunk_size]))
    return [c for c in chunks if c]


def index_brand_guidelines(force: bool = False) -> None:
    if not force and collection_exists_and_populated(GUIDELINES_COLLECTION):
        print(f"[indexer] '{GUIDELINES_COLLECTION}' already indexed — skipping.")
        return

    path = os.path.join(KB_PATH, "brand_guidelines.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = _chunk_markdown(text)
    documents = chunks
    metadatas = [{"source": "brand_guidelines.md", "chunk": i} for i in range(len(chunks))]
    ids = [f"guidelines_{i}" for i in range(len(chunks))]

    add_documents(GUIDELINES_COLLECTION, documents, metadatas, ids)
    print(f"[indexer] Indexed {len(chunks)} brand guideline chunks.")


def index_example_campaigns(force: bool = False) -> None:
    if not force and collection_exists_and_populated(CAMPAIGNS_COLLECTION):
        print(f"[indexer] '{CAMPAIGNS_COLLECTION}' already indexed — skipping.")
        return

    path = os.path.join(KB_PATH, "example_campaigns.json")
    with open(path, "r", encoding="utf-8") as f:
        campaigns = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for camp in campaigns:
        text = (
            f"Campaign: {camp['title']}\n"
            f"Industry: {camp['industry']}\n"
            f"Objective: {camp['objective']}\n"
            f"Audience: {camp['audience']}\n"
            f"Tone: {camp['tone']}\n"
            f"Key messages: {' | '.join(camp['key_messages'])}\n"
            f"Tagline: {camp['tagline']}\n"
            f"Results: {camp['results']}\n"
            f"Learnings: {camp['learnings']}"
        )
        documents.append(text)
        metadatas.append({"source": "example_campaigns.json", "campaign_id": camp["id"], "title": camp["title"]})
        ids.append(camp["id"])

    add_documents(CAMPAIGNS_COLLECTION, documents, metadatas, ids)
    print(f"[indexer] Indexed {len(campaigns)} example campaigns.")


def index_all(force: bool = False) -> None:
    index_brand_guidelines(force=force)
    index_example_campaigns(force=force)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-index even if already populated")
    args = parser.parse_args()
    index_all(force=args.force)
