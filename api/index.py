from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from app import mcp


async def root(request: Request) -> JSONResponse:
    return JSONResponse({
        "name": "ONS Baby Names MCP Server",
        "mcp_endpoint": "/mcp",
        "description": "MCP server exposing England & Wales baby names data from the ONS birth registration dataset.",
    })


_mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: Starlette):
    # Forward lifespan to the MCP app so its session manager task group is initialised.
    async with mcp.session_manager.run():
        yield


# Vercel's Python runtime expects an ASGI-compatible object named "app".
app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/", root),
        Mount("/", app=_mcp_app),
    ],
)
