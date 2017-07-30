import logging
import uuid

import bcrypt
import ujson

from pi_home_server.decorators import (
    get_user_clients_for_roles,
    validate_role,
)
import pi_home_server.config as config_constants
import pi_home_server.exceptions as exceptions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class App:

    def __init__(self, redis_pool):
        self._redis_pool = redis_pool
        self._clients = {}

    def _user_id(self, username):
        return 'user:{}'.format(username)

    def _auth_token_id(self, auth_token):
        return 'auth_token:{}'.format(auth_token)

    def _validate_user(self, username, password):
        logger.info('User \'%s\' already exists on our database. Verifying if information matches', username)

        user_id = self._user_id(username)
        user_string = self._redis_pool.get(user_id)
        user = ujson.loads(user_string)

        if (
            username == user['username'] and
            bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
        ):
            return {
                'username': user['username'],
                'auth_token': user['auth_token'],
            }
        else:
            raise exceptions.UserOrPasswordInvalidException

    def _save_user(self, username, password):
        logger.info('Saving \'%s\' on database', username)
        try:
            auth_token = str(uuid.uuid4())
            user = ujson.dumps({
                'username': username,
                'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
                'auth_token': auth_token,
            })

            self._redis_pool.set(self._user_id(username), user)
            self._redis_pool.set(self._auth_token_id(auth_token), username)

            return {
                'username': username,
                'auth_token': auth_token,
            }
        except Exception:
            raise exceptions.SaveUserException

    def handle_user(self, username, password):
        if not username or not password:
            raise exceptions.UserOrPasswordNotProvidedException

        logger.info('Processing request for user: \'%s\'', username)

        user_id = self._user_id(username)
        if self._redis_pool.exists(user_id):
            return self._validate_user(username, password)

        return self._save_user(username, password)

    def remove_client(self, client):
        try:
            del self._clients[client]
        except KeyError:
            # if client never send connect message, it won't be on the list
            pass

    def process_message(self, message, client):
        action_name = message.get('action')
        if not action_name:
            return None, False

        data = message.get('data')
        if not data:
            return action_name, False

        action_key = 'action_{action_name}'.format(
            action_name=action_name,
        )
        method = getattr(self, action_key, None)
        if not method:
            return action_name, False

        logger.info('Processing \'%s\' action', action_name)
        success = False
        try:
            success = method(action_name, data, message, client)
        except Exception as e:
            logger.error('There was an error excecuting \'%s\'. Error: %s', action_name, e)
            pass

        logger.info('Action \'%s\' end %s', action_name, 'successfully' if success else 'with failure')
        return action_name, success

    # both roles can use this action
    def action_connect(self, action, data, message, client):
        auth_token = data.get('auth_token')
        if not auth_token:
            return False

        role = data.get('role')
        if not role or role not in config_constants.AVAILABLE_ROLES:
            return False

        auth_token = self._auth_token_id(auth_token)
        if not self._redis_pool.exists(auth_token):
            logger.warning('Invalid auth_token provided to connect method')
            return False

        username = self._redis_pool.get(auth_token)
        self._clients[client] = {
            'username': username,
            'role': role,
        }

        return True

    @validate_role(config_constants.ROLE_WEB)
    @get_user_clients_for_roles(config_constants.ROLE_RASPBERRY)
    def action_set_value(self, action, data, message, client, clients):
        # forward the message to the clients
        for _client in clients:
            _client.send_json(message)

        return True

    @validate_role(config_constants.ROLE_RASPBERRY)
    @get_user_clients_for_roles(config_constants.ROLE_WEB)
    def action_board_status(self, action, data, message, client, clients):
        # forward the message to the clients
        for _client in clients:
            _client.send_json(message)

        return True
