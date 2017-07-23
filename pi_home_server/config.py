import os


def get_config():
    # build app_settings
    app_settings = {
        'host': '0.0.0.0',
        'port': os.environ.get('PORT', 8001),
    }

    # build result object
    result = {}
    result['app_settings'] = app_settings

    return result
