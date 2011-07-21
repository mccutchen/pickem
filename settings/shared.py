import os, sys

PROJECT_ROOT = os.path.realpath(
    os.path.dirname(
        os.path.dirname(__file__)))

# See if we're running in production or in development
PRODUCTION = 'Development' not in os.environ.get('SERVER_SOFTWARE', '')
DEBUG = not PRODUCTION

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'templates')

EMAIL_FROM = '"Pick\'em Pick\'em Robot" <robot@pickempickem.com>'

