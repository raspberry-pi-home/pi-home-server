import logging
import uuid

from aiohttp.web import (
    HTTPFound,
    View,
)
import aiohttp_jinja2
import bcrypt
import ujson


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _build_user_id(username):
    return 'user:{}'.format(username)


def _handle_user(username, password, redis_pool):
    if not username or not password:
        logger.error('username or password not provided')
        # TODO: hande error in template
        return HTTPFound('/')

    logger.info('Processing request for user: \'%s\'', username)
    user_id = 'user:{}'.format(username)
    if redis_pool.exists(user_id):
        logger.info('User \'%s\' already exists on our database. Verifying if information matches', username)
        user_string = redis_pool.get(user_id)
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
            logger.error('username or password not valid')
            # TODO: hande error in template
            return HTTPFound('/')

    return _save_user(username, password, user_id, redis_pool)


def _save_user(username, password, user_id, redis_pool):
    logger.info('Saving \'%s\' on database', username)
    try:
        user = ujson.dumps({
            'username': username,
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
            'auth_token': str(uuid.uuid4()),
        })

        redis_pool.set(user_id, user)

        return {
            'username': user['username'],
            'auth_token': user['auth_token'],
        }
    except Exception as e:
        logger.error('Error saving user: \'%s\'. Error: %s', username, e)
        # TODO: hande error in template
        return HTTPFound('/')


class IndexView(View):

    @aiohttp_jinja2.template('index.html')
    async def get(self):
        pass

    @aiohttp_jinja2.template('user.html')
    async def post(self):
        redis_pool = self.request.app['redis_pool']
        form_data = await self.request.post()

        username = form_data['username']
        password = form_data['password']

        return _handle_user(username, password, redis_pool)
