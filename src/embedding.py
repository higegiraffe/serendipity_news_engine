from __future__ import annotations

import hashlib
import os
from functools import lru_cache

import numpy as np

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False

from .utils import load_settings

VECTOR_SIZE = 384


def pack_vector(vector) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def unpack_vector(blob: bytes | None):
    if not blob:
        return None
    return np.frombuffer(blob, dtype=np.float32)


def _hash_embedding(text: str, size: int = VECTOR_SIZE) -> np.ndarray:
    vector = np.zeros(size, dtype=np.float32)
    tokens = text.lower().split() or [text.lower()]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % size
        vector[idx] += 1.0 if digest[4] % 2 else -1.0
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


@lru_cache(maxsize=1)
def _local_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    except Exception as exc:
        print(f"[embed] ハッシュ代替を使用します: {exc}")
        return None


def embed_texts(texts: list[str]) -> list[np.ndarray]:
    settings = load_settings()
    provider = settings.get("embedding", {}).get("provider", "local")
    load_dotenv()
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            model = settings.get("embedding", {}).get("openai_model", "text-embedding-3-small")
            response = client.embeddings.create(model=model, input=texts)
            return [np.asarray(item.embedding, dtype=np.float32) for item in response.data]
        except Exception as exc:
            print(f"[embed] OpenAI embedding に失敗したためローカルへ切り替えます: {exc}")
    model_name = settings.get("embedding", {}).get("local_model", "paraphrase-multilingual-MiniLM-L12-v2")
    model = _local_model(model_name)
    if model is None:
        return [_hash_embedding(text) for text in texts]
    return [np.asarray(vec, dtype=np.float32) for vec in model.encode(texts, normalize_embeddings=True)]
