import logging
import os


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ROLE_RASPBERRY = 'raspberry'
ROLE_WEB = 'web'

# available roles
AVAILABLE_ROLES = tuple(
    v for k, v in locals().items() if k.startswith('ROLE_'),
)


def _verify_redis_url(redis_url):
    if not redis_url:
        logger.error('Please provide a \'REDIS_URL\'')
        return

    # return True if everythig went ok
    return True


def get_config():
    # verify redis_url
    redis_url = os.environ.get('REDIS_URL')
    if not _verify_redis_url(redis_url):
        return

    # build app_settings
    app_settings = {
        'host': '0.0.0.0',
        'port': os.environ.get('PORT', 8001),
        'redis_db': '0',
        'redis_url': redis_url,
    }

    # build result object
    result = {}
    result['app_settings'] = app_settings

    return result
