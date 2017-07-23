import logging
import uuid

from aiohttp.web import View
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


def _user_id(username):
    return 'user:{}'.format(username)


def _auth_token_id(auth_token):
    return 'auth_token:{}'.format(auth_token)


def _handle_user(username, password, request):
    if not username or not password:
        return _handle_error(request, 'index.html', 'username or password not provided')

    redis_pool = request.app['redis_pool']
    user_id = _user_id(username)

    logger.info('Processing request for user: \'%s\'', username)
    if redis_pool.exists(user_id):
        return _validate_user(username, password, request)

    return _save_user(username, password, request)


def _validate_user(username, password, request):
    logger.info('User \'%s\' already exists on our database. Verifying if information matches', username)

    redis_pool = request.app['redis_pool']
    user_id = _user_id(username)

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
        return _handle_error(request, 'index.html', 'username or password not valid')


def _save_user(username, password, request):
    redis_pool = request.app['redis_pool']

    logger.info('Saving \'%s\' on database', username)
    try:
        auth_token = str(uuid.uuid4())
        user = ujson.dumps({
            'username': username,
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
            'auth_token': auth_token,
        })

        redis_pool.set(_user_id(username), user)
        redis_pool.set(_auth_token_id(auth_token), username)

        return {
            'username': username,
            'auth_token': auth_token,
        }
    except Exception as e:
        return _handle_error(request, 'index.html', 'Error: {}'.format(e))


class IndexView(View):

    @aiohttp_jinja2.template('index.html')
    async def get(self):
        pass

    @aiohttp_jinja2.template('user.html')
    async def post(self):
        form_data = await self.request.post()

        username = form_data['username']
        password = form_data['password']

        return _handle_user(username, password, self.request)
