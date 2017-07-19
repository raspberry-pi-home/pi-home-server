#!/usr/bin/env python

import logging
import sys


logging.basicConfig(
    format='%(asctime)s:%(name)s:%(pathname)s:%(levelname)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


py3 = sys.version_info[0] == 3
if not py3:
    logger.error('This application in meant to run on python 3')
    logger.info('Applicaion terminated')
    sys.exit()


from pi_home_server import pi_home_server

pi_home_server()
