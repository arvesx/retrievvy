from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

import config


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if bearer_token(request):
            return await call_next(request)

        return JSONResponse({"error": "Unauthorized"}, status_code=401)


def bearer_token(request):
    try:
        t = request.headers["Authorization"]
        t = t.replace("Bearer ", "")
    except KeyError:
        return False

    return t == config.WEB_TOKEN
