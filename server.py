from aiohttp import web
import logging

logger = logging.getLogger(__name__)

_app: web.Application | None = None


async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text="ok", status=200)


def create_web_app() -> web.Application:
    global _app
    app = web.Application()
    app.router.add_get("/health", health_handler)
    _app = app
    return app


def get_web_app() -> web.Application | None:
    return _app
