import json
import logging

from aiohttp.web import (
    WebSocketResponse,
    WSMsgType,
)

from pi_home_server.views import IndexView


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# TODO: does this make sense?
async def notify_active_connections(websockets):

    # gather connections and send them to all websockets
    connections_data = {}
    connections_data['active_connections'] = len(websockets)
    connections_data = json.dumps(connections_data)
    for ws in websockets:
        await ws.send_str(connections_data)


async def websocket_message_handler(msg, ws_response, websockets):
    logger.info('Got %s message from websocket', msg.data)

    # try to parse the message as json
    try:
        data = msg.json()
    except json.JSONDecodeError:
        logger.warning('Unable to parse websocket json message')

        # is message is not in a json format, we will do nothing
        return

    # TODO: do something with `data`
    await notify_active_connections(websockets)


async def websocket_handler(request):
    ws_response = WebSocketResponse()
    ok, protocol = ws_response.can_prepare(request)
    if not ok:
        logger.info('Unable to prepare connection between server and websocket')
        return ws_response

    await ws_response.prepare(request)

    try:
        websockets = request.app['websockets']
        websockets.append(ws_response)

        logger.info('A new websocket is connected, total: %s', len(websockets))

        # notify about active connections
        await notify_active_connections(websockets)

        # TODO: I couldn't make this work using .receive() method because
        # of the middlewares. So, again, does middlewares makes sense for this
        # project?
        async for msg in ws_response:
            # we only care about text messages
            if msg.type == WSMsgType.TEXT:
                await websocket_message_handler(
                    msg,
                    ws_response,
                    websockets,
                )

            else:
                return ws_response

        return ws_response

    finally:
        websockets = request.app['websockets']
        websockets.remove(ws_response)

        logger.info('A websocket is disconnected, total: %s', len(websockets))

        # notify about active connections
        await notify_active_connections(websockets)


routes = [
    ('*', '/', IndexView),
    ('GET', '/ws', websocket_handler),
]
