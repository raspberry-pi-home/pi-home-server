from functools import wraps


def validate_role(role):

    def decorator(func):

        # TODO: fix this (?)
        # this is higly coupled to the signature of the methods are using this decorator
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


def get_user_clients_for_roles(roles):

    def decorator(func):

        # TODO: fix this (?)
        # this is higly coupled to the signature of the methods are using this decorator
        @wraps(func)
        def wrapper(app, action, data, message, client):
            # verify if client is registered
            ws_client = app._clients.get(client)
            if not ws_client:
                return False

            # get all clients for user with role 'raspberry'
            ws_username = ws_client['username']
            clients = [
                _client
                for _client, _data in app._clients.items()
                if _data['username'] == ws_username and _data['role'] in roles
            ]

            return func(app, action, data, message, client, clients)

        return wrapper

    return decorator
