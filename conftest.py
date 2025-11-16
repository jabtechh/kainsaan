"""
pytest configuration for Kain Saan project.
"""

import os
import django
from django.conf import settings

# Configure Django settings for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kainsaan.settings')

def pytest_configure():
    """Configure Django settings for testing."""
    settings.DEBUG = False
    # Override settings for testing if needed
    settings.GOOGLE_PLACES_API_KEY = 'test-api-key'
    settings.GOOGLE_MAPS_API_KEY = 'test-api-key'
    
    django.setup()
