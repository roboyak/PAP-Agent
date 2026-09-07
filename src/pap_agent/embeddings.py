"""Local real embeddings and an explicitly named deterministic test double."""

import re
from hashlib import sha256

import httpx

from pap_agent.config import Settings

DIMENSIONS = 768


def ollama_identity(base_url: str, model: str) -> str:
    response = httpx.get(f"{base_url}/api/tags", timeout=5, trust_env=False)
    response.raise_for_status()
    match = next(item for item in response.json()["models"] if item["name"] == model)
    return f"{model}@{match['digest']}"


def model_identity() -> str:
    settings = Settings()
    return (
        "test-hash-v1"
        if settings.embedding_backend == "test"
        else ollama_identity(settings.ollama_base_url, settings.embedding_model)
    )


def embed_documents(documents: list[str]) -> list[list[float]]:
    settings = Settings()
    if settings.embedding_backend == "test":
        vectors = []
        for document in documents:
            vector = [0.0] * DIMENSIONS
            for word in re.findall(r"\w+", document.lower()):
                vector[int.from_bytes(sha256(word.encode()).digest()[:4]) % DIMENSIONS] += 1
            vectors.append(vector)
        return vectors
    response = httpx.post(
        f"{settings.ollama_base_url}/api/embed",
        timeout=30,
        trust_env=False,
        json={
            "model": settings.embedding_model,
            "input": documents,
            "truncate": False,
            "keep_alive": "10m",
        },
    )
    response.raise_for_status()
    vectors = response.json()["embeddings"]
    if len(vectors) != len(documents) or any(len(vector) != DIMENSIONS for vector in vectors):
        raise ValueError("Expected 768-dimensional embeddings from the configured model")
    return vectors


def embed_query(query: str) -> list[float]:
    return embed_documents([query])[0]
