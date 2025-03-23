import asyncio

from msgspec import Struct

import database
import rerank
import stats

from indexes import dense, sparse
from nlp import keywords, embeddings

# Types
# -----


class Query(Struct):
    q: str
    index: str
    limit: int
    # TODO: in future add filtering options


class Hit(Struct):
    id: int
    bundle_id: str
    content: str
    ref: str
    chunk_order: str


class Result(Struct):
    gini: float
    hits: list[Hit]


# Main
# ----


async def query(q: Query) -> Result:
    # Setup of initial conditions
    index = q.index
    limit = q.limit * 2 + 5  # Have a breathing room for the reranking process
    query_keywords = keywords.get(q.q)
    query_embedding = await embeddings.get_async([q.q])

    # Query the indexes
    task_sparse = asyncio.to_thread(
        sparse.query, index, " ".join(query_keywords), limit
    )
    task_dense = dense.query(index, query_embedding, limit)
    hits_sparse, hits_dense = await asyncio.gather(task_sparse, task_dense)

    # Fuse the results
    fused = rerank.adaptive_fusion(hits_dense, hits_sparse)
    ids, scores = zip(*fused)
    ids = list(ids)
    scores = list(scores)
    gini = stats.gini(scores)  # Measures ranking quality

    # Fetch chunk data and build a lookup to preserve the fused order
    chunks_raw = database.chunks_get(ids)
    chunk_map = {c["id"]: c for c in chunks_raw}

    hits: list[Hit] = []
    for id in ids:
        if id not in chunk_map:
            continue

        c = chunk_map[id]
        hits.append(
            Hit(
                id=id,
                bundle_id=c["bundle_id"],
                content=c["content"],
                ref=c["ref"],
                chunk_order=c["chunk_order"],
            )
        )

    hits = hits[: q.limit]  # original requested limit
    return Result(gini=gini, hits=hits)
