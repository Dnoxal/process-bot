import asyncio
import logging

import uvicorn

from process_bot.api import app
from process_bot.bot import run_bot
from process_bot.config import get_settings
from process_bot.database import init_db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_api() -> None:
    settings = get_settings()
    browser_host = "127.0.0.1" if settings.api_host == "0.0.0.0" else settings.api_host
    logger.info(
        "Starting dashboard on http://%s:%s (bound to %s:%s)",
        browser_host,
        settings.api_port,
        settings.api_host,
        settings.api_port,
    )
    config = uvicorn.Config(app=app, host=settings.api_host, port=settings.api_port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    init_db()
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    asyncio.run(main())
