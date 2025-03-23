import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from retrievvy import config
from . import middleware, hits, bundles, indexes

routes = [
    Route("/query", hits.get, methods=["GET"]),
    # Bundles
    Route("/bundle", bundles.get, methods=["GET"]),
    Route("/bundle", bundles.post, methods=["POST"]),
    Route("/bundle", bundles.delete, methods=["DELETE"]),
    Route("/bundles", bundles.list, methods=["GET"]),
    # Indexes
    Route("/index", indexes.get, methods=["GET"]),
    Route("/index", indexes.delete, methods=["DELETE"]),
    Route("/indexes", indexes.list, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization"],
    ),
    Middleware(middleware.AuthMiddleware),
]


app = Starlette(debug=config.DEBUG, routes=routes, middleware=middleware)


def run(host=config.WEB_HOST, port=config.WEB_PORT):
    uvicorn.run("retrievvy.webserver:app", host=host, port=port, reload=config.DEBUG)
