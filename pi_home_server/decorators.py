from functools import wraps


def validate_role(role):

    def decorator(func):

        @wraps(func)
        def wrapper(app, action, data, message, client):
            # verify if client is registered
            ws_client = app._clients.get(client)
            if not ws_client:
                return False

            # verify role
            ws_role = ws_client['role']
            if ws_role != role:
                return False

            return func(app, action, data, message, client)

        return wrapper

    return decorator
