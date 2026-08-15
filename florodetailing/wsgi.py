"""
WSGI config for the Florø Detailing project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "florodetailing.settings")

application = get_wsgi_application()
