from dataclasses import dataclass
from typing import Optional, Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    PointIdsList,
    VectorParams,
    Distance
)

# Client
# ------

client = AsyncQdrantClient(url="http://localhost:6333", timeout=60)

# Type definitions
# ----------------


@dataclass
class Vector:
    id: int
    vector: list[float]
    payload: Optional[dict[str, Any]] = None


@dataclass
class Hit:
    id: int
    vector: list[float]
    score: float

# Interaction funcs ------

# Index Management
# ----------------


async def create(name: str, emb_size: int):
    await client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=emb_size, distance=Distance.COSINE),
    )


async def delete(name: str):
    await client.delete_collection(collection_name=name)


# Vectors
# -------


async def vec_add(name: str, vecs: list[Vector]):
    await client.upsert(
        collection_name=name,
        points=[
            PointStruct(id=vec.id, vector=vec.vector, payload=vec.payload)
            for vec in vecs
        ],
    )


async def vec_del(name: str, ids: list[int]):
    await client.delete(collection_name=name, points_selector=PointIdsList(points=ids))


# Query
# -----


async def query(name: str, vec: list[float], limit: int = 10):
    results = await client.query_points(
        collection_name=name, query_vector=vec, limit=limit, with_vectors=True
    )

    return [Hit(id=p.id, vector=p.vector, score=p.score) for p in results.points]
