import asyncio
from typing import Annotated

from starlette.requests import Request
from starlette.responses import Response

from msgspec import Struct, Meta, ValidationError, convert
from msgspec.json import encode

from retrievvy import database
from retrievvy.indexes import dense, sparse

# Handlers
# --------

# Get index -----


async def get(request: Request):
    name = request.query_params.get("name")
    if name is None:
        content = encode({"detail": "Query parameter `name` is required."})
        return Response(content, status_code=422, media_type="application/json")

    index = database.index_get(name)
    if index is None:
        content = encode(
            {
                "detail": f"Index with name {name} not found",
            }
        )
        return Response(content, status_code=404, media_type="application/json")

    return Response(encode(index), status_code=200, media_type="application/json")


# List indexes ------


class List(Struct):
    page: Annotated[int, Meta(ge=0)] = 0
    items: Annotated[int, Meta(ge=0)] = 0


async def list(request: Request):
    try:
        params = convert(dict(request.query_params), List, strict=False)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": str(exc)})
        return Response(content, status_code=422, media_type="application/json")

    index_list = database.index_list(params.page, params.items)
    return Response(encode(index_list), status_code=200, media_type="application/json")


# Delete index ----


async def delete(request: Request):
    name = request.query_params.get("name")
    if name is None:
        content = encode({"detail": "Query parameter `name` is required."})
        return Response(content, status_code=422, media_type="application/json")

    exists = database.index_get(name)
    if not exists:
        content = encode(
            {
                "detail": "Not found",
            }
        )
        return Response(content, status_code=404, media_type="application/json")

    # TODO: consider making the following operations atomic

    async def cleanup_async():
        await asyncio.gather(
            dense.delete(name),
            asyncio.to_thread(sparse.delete, name),
        )

    asyncio.create_task(cleanup_async())
    database.index_del(name=name)

    return Response(status_code=204)
