import gzip
from typing import Annotated, Any
from starlette.requests import Request
from starlette.responses import Response

from msgspec import Meta, Struct, ValidationError, convert
from msgspec.json import encode


from retrievvy.indexes import dense


# Handlers
# --------

# List vectors of an index


class List(Struct):
    index: str
    offset: Annotated[int, Meta(ge=0)]
    limit: Annotated[int, Meta(ge=0)]


async def list(request: Request):
    try:
        params = convert(dict(request.query_params), List, strict=False)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": str(exc)})
        return Response(content, status_code=422, media_type="application/json")

    try:
        vecs, next_offset = await dense.vec_list(
            idx_name=params.index, offset=params.offset, limit=params.limit
        )
    except LookupError:
        content = encode(
            {
                "detail": f"Index with name {params.index} not found",
            }
        )
        return Response(content, status_code=404, media_type="application/json")

    response_data: dict[str, Any] = {
        "fetched": len(vecs),
        "next_offset": next_offset,
        "vectors": vecs,
    }

    raw_json = encode(response_data)
    compressed = gzip.compress(raw_json)

    return Response(
        content=compressed,
        status_code=200,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"},
    )
