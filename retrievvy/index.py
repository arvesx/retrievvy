import asyncio
from dataclasses import dataclass
from typing import Literal

from msgspec import Struct
from loguru import logger

from . import chunks
from . import database

from .nlp import embeddings
from .indexes import sparse, dense

# Types
# -----


class Bundle(Struct):
    id: str
    index: str
    source: str
    name: str
    blocks: list[str]


@dataclass
class Chunk:
    content: str
    ref: str  # start and end indices of blocks from which this chunk spans across
    chunk_order: int


# Main
# -----


async def run(bundle: Bundle) -> Literal["pending", "chunked", "completed"]:
    status = database.bundle_status_get(bundle.id, bundle.index)

    # Initial database entry
    if status is None:
        logger.info(f"Inserting a new bundle with id {bundle.id} in the database")
        database.bundle_add(bundle.id, bundle.index, bundle.source, bundle.name)
        status = "pending"

    # Chunking process
    if status == "pending":
        chunk_objects = _chunk(bundle)
        logger.info(f"Inserting {len(chunk_objects)} chunks in the database")

        # TODO: in future, group database calls that are related in transaction
        database.chunks_add(
            [
                (bundle.index, bundle.id, chunk.content, chunk.ref, chunk.chunk_order)
                for chunk in chunk_objects
            ]
        )

        database.bundle_status_set(bundle.id, bundle.index, "chunked")
        status = "chunked"

    # Indexing phase
    if status != "completed":
        chunk_data = database.chunks_get_by_bundle_id(bundle.index, bundle.id)

        logger.info(f"Starting indexing phase for {len(chunk_data)} chunks")
        embs = await embeddings.get_async([chunk["content"] for chunk in chunk_data])

        data_to_sparse = [
            sparse.Doc(chunk["id"], chunk["content"]) for chunk in chunk_data
        ]
        data_to_dense = [
            dense.Vector(chunk["id"], emb) for chunk, emb in zip(chunk_data, embs)
        ]
        try:
            await asyncio.to_thread(sparse.doc_add, bundle.index, data_to_sparse)
            await dense.vec_add(bundle.index, data_to_dense)

            status = "completed"
        except Exception as e:
            logger.exception(f"Indexing failed for bundle {bundle.id}: {e}")
            # In case of error cleanup everything
            ids = [chunk["id"] for chunk in chunk_data]
            await asyncio.to_thread(sparse.doc_del, bundle.index, ids)
            await dense.vec_del(bundle.index, ids)

            raise e

    return status


# Helpers
# --------


def _chunk(bundle: Bundle) -> list[Chunk]:
    combined = "\n ".join(bundle.blocks)

    # Precompute block boundaries
    block_ranges = []
    pos = 0
    for i, block in enumerate(bundle.blocks, start=1):
        length = len(block)
        block_ranges.append((pos, pos + length - 1, i))
        pos += length + 2  # account for "\n "

    chunked_texts = chunks.get(combined)
    produced = []
    cursor = 0

    def find_block(idx: int) -> int | None:
        for start, end, blk in block_ranges:
            if start <= idx <= end:
                return blk
        return None

    for order, text in enumerate(chunked_texts, start=1):
        try:
            start_idx = combined.index(text, cursor)
        except ValueError:
            raise RuntimeError(f"Unable to locate chunk #{order!r} in combined text")

        end_idx = start_idx + len(text) - 1
        cursor = end_idx + 1

        start_blk = find_block(start_idx)
        end_blk = find_block(end_idx)
        ref = f"{start_blk}" if start_blk == end_blk else f"{start_blk}-{end_blk}"

        produced.append(Chunk(content=text, ref=ref, chunk_order=order))

    return produced
