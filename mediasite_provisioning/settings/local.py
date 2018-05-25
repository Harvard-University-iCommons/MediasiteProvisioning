import logging

from dj_log_config_helper import configure_installed_apps_logger

from .base import *

DEBUG = True

# For Django Debug Toolbar:
INTERNAL_IPS = ['127.0.0.1', '10.0.2.2']

SECRET_KEY = 'en9#zy=gnnmz8blzh_!*jkpmy^ysy)e^01e6of!(xw0)s*h4(z'

configure_installed_apps_logger(logging.DEBUG,
                                additional_packages=['py.warnings'])
