"""
WSGI config for kainsaan project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kainsaan.settings')

application = get_wsgi_application()
