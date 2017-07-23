import asyncio
import logging
import redis
import sys


from aiohttp.web import (
    Application,
    HTTPException,
    Response,
    WebSocketResponse,
)
import aiohttp_jinja2
import jinja2

from pi_home_server.config import get_config
from pi_home_server.server_routes import routes


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# def json_error(message, status):
#     logger.warning('Web server error: http=%s error=%s', status, message)
#     return Response(
#         status=status,
#         text='There was an error executing your request',
#     )


# TODO: does this makes sense on a websocket
# async def error_middleware(web_app, handler):
#     async def middleware_handler(request):
#         try:
#             response = await handler(request)
#             # TODO: ?
#             # we don't care about WebSocketResponse (for now)
#             if isinstance(response, WebSocketResponse):
#                 return response
#             if response.status == 200:
#                 return response
#             return json_error(response.message, response.status)
#         except HTTPException as ex:
#             if ex.status != 200:
#                 return json_error(ex.reason, ex.status)
#             raise
#     return middleware_handler


async def init_server(loop):
    logger.info('Building configuration')
    config = get_config()
    if not config:
        logger.info('Applicaion terminated')
        sys.exit()

    logger.info('App configuration: %s', config)

    host = config['app_settings']['host']
    port = config['app_settings']['port']
    redis_pool = redis.from_url(
        url=config['app_settings']['redis_url'],
        db=config['app_settings']['redis_db'],
    )

    logger.info('Building web application')
    web_app = Application(
        loop=loop,
        # middlewares=[
        #     error_middleware,
        # ],
    )
    web_app['websockets'] = []
    web_app['redis_pool'] = redis_pool

    aiohttp_jinja2.setup(
        web_app,
        loader=jinja2.PackageLoader('pi_home_server', 'templates'),
    )

    for route in routes:
        web_app.router.add_route(route[0], route[1], route[2])

    web_app.on_shutdown.append(on_shutdown)

    logger.info('Starting web server')
    web_app_handler = web_app.make_handler()
    web_server_generator = loop.create_server(
        web_app_handler,
        host=host,
        port=port,
    )

    return web_server_generator, web_app_handler, web_app


async def on_shutdown(web_app):
    logger.info('Closing websocket connections')
    for ws in web_app['websockets']:
        await ws.close()


async def shutdown(server, web_app, web_app_handler):
    logger.info('Stopping main server')
    server.close()
    await server.wait_closed()
    logger.info('Stopping web application')
    await web_app.shutdown()
    await web_app_handler.shutdown(timeout=5.0)
    await web_app.cleanup()


def main():
    logger.info('Starting application')

    loop = asyncio.get_event_loop()
    server_generator = init_server(loop)
    web_server_generator, web_app_handler, web_app = loop.run_until_complete(server_generator)
    server = loop.run_until_complete(web_server_generator)

    logger.info('Starting web server: %s', str(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Stopping application')
    finally:
        loop.run_until_complete(shutdown(server, web_app, web_app_handler))
        loop.close()

    logger.info('Applicaion stopped')
