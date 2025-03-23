from dataclasses import dataclass
from typing import Optional, Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    PointIdsList,
    VectorParams,
    Distance,
    Filter,
    HasIdCondition,
)

from retrievvy.config import QDRANT_URL

# Client
# ------

client = AsyncQdrantClient(url=QDRANT_URL, timeout=60)

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


async def create(name: str, emb_size: int) -> None:
    await client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=emb_size, distance=Distance.COSINE),
    )


async def delete(name: str) -> None:
    await client.delete_collection(collection_name=name)


# Vectors
# -------


async def vec_add(idx_name: str, vecs: list[Vector]) -> None:
    await client.upsert(
        collection_name=idx_name,
        points=[
            PointStruct(id=vec.id, vector=vec.vector, payload=vec.payload)
            for vec in vecs
        ],
    )


async def vec_del(idx_name: str, ids: list[int]) -> None:
    await client.delete(
        collection_name=idx_name, points_selector=PointIdsList(points=ids)
    )


# Query
# -----


async def query(
    idx_name: str,
    vec: list[float],
    limit: int = 10,
    filter_ids: Optional[list[int]] = None,
) -> list[Hit]:
    point_id_filter = (
        Filter(must=[HasIdCondition(has_id=filter_ids)]) if filter_ids else None
    )

    results = await client.query_points(
        collection_name=idx_name,
        query_vector=vec,
        limit=limit,
        with_vectors=True,
        filter=point_id_filter,
    )

    return [Hit(id=p.id, vector=p.vector, score=p.score) for p in results.points]
