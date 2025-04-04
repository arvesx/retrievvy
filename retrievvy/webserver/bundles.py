import asyncio
from typing import Annotated

from starlette.requests import Request
from starlette.responses import Response

from msgspec import Struct, Meta, ValidationError, convert
from msgspec.json import Decoder, encode

from loguru import logger

from retrievvy.index import Bundle, run
from retrievvy.indexes import dense, sparse
from retrievvy import database

# Decoder
# -------
decoder = Decoder(Bundle)


# Handlers
# --------

# Index a new bundle -----


async def post(request: Request):
    try:
        bundle_bytes = await request.body()
        bundle_obj = decoder.decode(bundle_bytes)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": str(exc)})
        return Response(content, status_code=422, media_type="application/json")

    if database.index_get(bundle_obj.index) is None:
        logger.info(f"Creating a new index with name '{bundle_obj.index}'")
        task_dense = dense.create(bundle_obj.index, 384)
        task_sparse = asyncio.to_thread(sparse.create, bundle_obj.index)
        await asyncio.gather(task_dense, task_sparse)
        database.index_add(bundle_obj.index)

    status = await run(bundle_obj)
    result = {"status": status}
    return Response(encode(result), status_code=201, media_type="application/json")


# List bundles -----


class List(Struct):
    index: str
    page: Annotated[int, Meta(ge=0)] = 0
    items: Annotated[int, Meta(ge=0)] = 0


async def list(request: Request):
    try:
        params = convert(dict(request.query_params), List, strict=False)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": str(exc)})
        return Response(content, status_code=422, media_type="application/json")

    bundles = database.bundle_list(params.index, params.page, params.items)

    return Response(encode(bundles), status_code=200, media_type="application/json")


# Delete bundle -----


class Delete(Struct):
    index: str
    bundle_id: str


async def delete(request: Request):
    try:
        params = convert(dict(request.query_params), Delete)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": str(exc)})
        return Response(content, status_code=422, media_type="application/json")

    exists = database.bundle_get(params.bundle_id, params.index)
    if not exists:
        content = encode(
            {
                "detail": "Not found",
            }
        )
        return Response(content, status_code=404, media_type="application/json")

    bundle_chunks = database.chunks_get_by_bundle_id(params.index, params.bundle_id)
    chunk_ids: list[int] = [c["id"] for c in bundle_chunks]

    # TODO: in future consider how to make the following operations happen atomically

    # First, delete the bundle synchronously
    database.bundle_del(bundle_id=params.bundle_id, index=params.index)

    # Run cleanup asynchronously
    async def cleanup_async():
        await asyncio.gather(
            dense.vec_del(params.index, chunk_ids),
            asyncio.to_thread(sparse.doc_del, params.index, chunk_ids),
        )

    asyncio.create_task(cleanup_async())

    return Response(status_code=204)


# Get bundle ----


class Get(Struct):
    index: str
    bundle_id: str


async def get(request: Request):
    try:
        params = convert(dict(request.query_params), Get)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": str(exc)})
        return Response(content, status_code=422, media_type="application/json")

    bundle = database.bundle_get(params.bundle_id, params.index)
    if bundle is None:
        content = encode(
            {
                "detail": f"Bundle with id {params.bundle_id} not found in {params.index}",
            }
        )
        return Response(content, status_code=404, media_type="application/json")

    return Response(encode(bundle), status_code=200, media_type="application/json")
