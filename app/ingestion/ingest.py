from pathlib import Path
import json
from app.ingestion.chunker import chunk_text
from app.ingestion.loader import load_text_from_file

DOCS_PATH = Path("data/docs")
INDEX_PATH = Path("data/index/chunks.json")

def ingest_documents():
    all_chunks = []

    for doc_path in DOCS_PATH.glob("*"):
        text = load_text_from_file(doc_path)
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "doc_id": doc_path.name,
                "chunk_id": f"{doc_path.name}-{i}",
                "text": chunk,
            })

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(all_chunks, indent=2))

if __name__ == "__main__":
    ingest_documents()
