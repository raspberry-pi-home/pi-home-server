import json
import logging

from aiohttp.web import (
    WebSocketResponse,
    WSMsgType,
)
import aiohttp_jinja2


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@aiohttp_jinja2.template('index.html')
async def index_handler(request):
    pass


routes = [
    ('GET', '/', index_handler),
]
