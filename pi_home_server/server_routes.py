from pi_home_server.views import (
    IndexView,
    WebSocketView,
)


routes = [
    ('*', '/', IndexView),
    ('GET', '/ws', WebSocketView),
]
