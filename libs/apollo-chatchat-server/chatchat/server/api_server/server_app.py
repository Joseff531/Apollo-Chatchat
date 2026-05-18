import argparse
import os
from typing import Literal

import uvicorn
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from chatchat import __version__
from chatchat.settings import Settings
from chatchat.server.api_server.chat_routes import chat_router
from chatchat.server.api_server.kb_routes import kb_router
from chatchat.server.api_server.mcp_routes import mcp_router
from chatchat.server.api_server.openai_routes import openai_router
from chatchat.server.api_server.server_routes import server_router
from chatchat.server.api_server.tool_routes import tool_router
from chatchat.server.chat.completion import completion
from chatchat.server.utils import MakeFastAPIOffline


def create_app(run_mode: str = None):
    app = FastAPI(title="Apollo-Chatchat API Server", version=__version__)
    MakeFastAPIOffline(app)
    # Add CORS middleware to allow all origins
    # set OPEN_DOMAIN=True in config.py to allow cross-domain
    if Settings.basic_settings.OPEN_CROSS_DOMAIN:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/", summary="Swagger documentation", include_in_schema=False)
    async def document():
        return RedirectResponse(url="/docs")

    app.include_router(chat_router)
    app.include_router(kb_router)
    app.include_router(tool_router)
    app.include_router(openai_router)
    app.include_router(server_router)
    app.include_router(mcp_router)

    # Other endpoints
    app.post(
        "/other/completion",
        tags=["Other"],
        summary="Request LLM model completion (via LLMChain)",
    )(completion)

    # Media files
    app.mount("/media", StaticFiles(directory=Settings.basic_settings.MEDIA_PATH), name="media")

    # Project related images
    img_dir = str(Settings.basic_settings.IMG_DIR)
    app.mount("/img", StaticFiles(directory=img_dir), name="img")

    return app


def run_api(host, port, **kwargs):
    if kwargs.get("ssl_keyfile") and kwargs.get("ssl_certfile"):
        uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_keyfile=kwargs.get("ssl_keyfile"),
            ssl_certfile=kwargs.get("ssl_certfile"),
        )
    else:
        uvicorn.run(app, host=host, port=port)


app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="apollo-chatchat",
        description="Apollo-Chatchat, a local knowledge-base LLM RAG and Agent application built with Langchain.",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # Initialization message
    args = parser.parse_args()
    args_dict = vars(args)

    run_api(
        host=args.host,
        port=args.port,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
    )
