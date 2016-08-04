from dj_log_config_helper import configure_installed_apps_logger

from .base import *

SECRET_KEY = SECURE_SETTINGS['django_secret_key']

DEBUG = SECURE_SETTINGS['enable_debug']

ALLOWED_HOSTS = ['.harvard.edu']

# SSL is terminated at the ELB so look for this header to know that we
# should be in ssl mode
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True

LOG_LEVEL = SECURE_SETTINGS['log_level']
LOG_FILE = os.path.join(
    SECURE_SETTINGS['log_root'], 'django-mediasite_provisioning.log')

configure_installed_apps_logger(
    LOG_LEVEL, verbose=True, filename=LOG_FILE)
