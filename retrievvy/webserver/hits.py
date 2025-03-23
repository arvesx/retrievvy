from starlette.requests import Request
from starlette.responses import Response

from msgspec import ValidationError, convert
from msgspec.json import encode

from retrievvy import Query, query

# We're using msgspec json encoding capabilities because it's fast :)

# Handlers
# --------


async def get(request: Request):
    try:
        query_obj = convert(dict(request.query_params), Query)
    except ValidationError as exc:
        content = encode({"detail": "Validation error", "errors": exc.errors()})
        return Response(content, status_code=422, media_type="application/json")

    result = await query(query_obj)
    return Response(encode(result), status_code=200, media_type="application/json")
