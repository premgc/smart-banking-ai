from __future__ import annotations

from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from config.settings import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    QDRANT_HOST, 
    QDRANT_MODE,
    QDRANT_PORT,
    QDRANT_TIMEOUT,
    QDRANT_URL,
    SEARCH_LIMIT,
    VECTOR_STORE_DIR,
)

_model = None
_client = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_client() -> QdrantClient:
    global _client
    if _client is not None:
        return _client

    if QDRANT_MODE == 'remote':
        if QDRANT_URL:
            _client = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT)
        else:
            _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=QDRANT_TIMEOUT)
    else:
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        _client = QdrantClient(path=str(VECTOR_STORE_DIR))

    return _client


def collection_exists() -> bool:
    client = get_client()
    try:
        return client.collection_exists(QDRANT_COLLECTION)
    except Exception:
        return False


def ensure_collection(vector_size: int) -> None:
    client = get_client()
    if collection_exists():
        return
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def health_check() -> tuple[bool, str]:
    try:
        client = get_client()
        _ = client
        _ = get_model()
        if collection_exists():
            return True, f"Qdrant ready, collection '{QDRANT_COLLECTION}' found"
        return False, f"Qdrant reachable, but collection '{QDRANT_COLLECTION}' not found. Run python ingest.py"
    except Exception as e:
        return False, f'Qdrant health check failed: {e}'


def upsert_texts(texts: List[str]) -> int:
    clean_texts = [str(t).strip() for t in texts if str(t).strip()]
    if not clean_texts:
        return 0

    model = get_model()
    client = get_client()
    vectors = model.encode(clean_texts).tolist()
    vector_size = len(vectors[0])
    ensure_collection(vector_size)

    points = [
        PointStruct(id=idx, vector=vector, payload={'text': text})
        for idx, (text, vector) in enumerate(zip(clean_texts, vectors), start=1)
    ]

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return len(points)


def search(query: str, limit: int = SEARCH_LIMIT) -> List[str]:
    if not query or not str(query).strip():
        return []

    if not collection_exists():
        raise RuntimeError(
            f"Qdrant collection '{QDRANT_COLLECTION}' does not exist. Run python ingest.py first."
        )

    model = get_model()
    client = get_client()
    vector = model.encode(query).tolist()

    try:
        result = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=vector,
            limit=limit,
        )
        points = getattr(result, 'points', result)
    except AttributeError:
        points = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=vector,
            limit=limit,
        )
    except Exception as e:
        raise RuntimeError(f'Qdrant query failed: {e}') from e

    texts = []
    for point in points:
        payload = getattr(point, 'payload', None)
        if payload is None and isinstance(point, dict):
            payload = point.get('payload', {})
        text = str((payload or {}).get('text', '')).strip()
        if text:
            texts.append(text)
    return texts
