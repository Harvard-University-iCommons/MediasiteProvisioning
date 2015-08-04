"""
WSGI config for MediasiteProvisioning project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application

# need to append the path, not sure why.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MediasiteProvisioning.settings.local")

application = get_wsgi_application()
