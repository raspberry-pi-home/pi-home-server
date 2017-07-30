import json
import logging
import uuid

from aiohttp.web import (
    View,
    WebSocketResponse,
    WSMsgType,
)
import aiohttp_jinja2
import bcrypt
import ujson


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _handle_error(request, template, error_message):
    logger.error('%s', error_message)

    context = {
        'error': {
            'message': error_message,
        },
    }
    return aiohttp_jinja2.render_template(template, request, context)


async def _websocket_message_handler(msg, ws_response, websockets, server_app):
    logger.info('Got %s message from websocket', msg.data)

    # try to parse the message as json
    try:
        data = msg.json()
    except json.JSONDecodeError:
        logger.warning('Unable to parse websocket json message')

        # is message is not in a json format, we will do nothing
        return ws_response

    action, status = server_app.process_message(data, ws_response)

    # respond with the status of the message
    ws_response.send_json({
        'action': '{action}_{status}'.format(
            action=action,
            status='ok' if bool(status) else 'not_ok',
        )
    })


class IndexView(View):

    @aiohttp_jinja2.template('index.html')
    async def get(self):
        pass

    @aiohttp_jinja2.template('user.html')
    async def post(self):
        request = self.request
        form_data = await request.post()
        server_app = request.app['server_app']

        username = form_data['username']
        password = form_data['password']

        try:
            return server_app.handle_user(username, password)
        except Exception as e:
            return _handle_error(request, 'index.html', e.message)


class WebSocketView(View):

    async def get(self):
        request = self.request
        ws_response = WebSocketResponse()
        ok, protocol = ws_response.can_prepare(request)
        if not ok:
            logger.info('Unable to prepare connection between server and websocket')
            return ws_response

        await ws_response.prepare(request)

        try:
            server_app = request.app['server_app']
            websockets = request.app['websockets']
            websockets.append(ws_response)

            logger.info('A new websocket is connected, total: %s', len(websockets))

            async for msg in ws_response:
                # we only care about text messages
                if msg.type == WSMsgType.TEXT:
                    await _websocket_message_handler(
                        msg,
                        ws_response,
                        websockets,
                        server_app,
                    )

                else:
                    return ws_response

            return ws_response

        finally:
            server_app = request.app['server_app']
            server_app.remove_client(ws_response)
            websockets = request.app['websockets']
            websockets.remove(ws_response)

            logger.info('A websocket is disconnected, total: %s', len(websockets))
